import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from main import app
from api.db.base_model import Base
from api.db.database import get_db
from api.v1.models.user.user import User, ProfileSetup
from api.v1.dependencies.auth import get_current_user
from datetime import date

TEST_DATABASE_URL = "postgresql://fastapi_user:password123@localhost:5432/mum_mentor_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(client):
    """Create a dummy user to attach the profile to"""
    db = TestingSessionLocal()
    user = User(full_name="Test Mom", email="mom@test.com", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    app.dependency_overrides[get_current_user] = lambda: user
    return user


def test_submit_profile_success(client, test_user):
    """Test 1: Submit valid profile data (Happy Path)"""
    payload = {
        "mom_status": "pregnant",
        "goals": ["Sleep", "Nutrition"],
        "partner": {
            "name": "Dad",
            "email": "dad@test.com"
        },
        "children": [
            {
                "full_name": "Baby 1",
                "gender": "female",
                "date_of_birth": str(date.today())
            }
        ]
    }

    response = client.post("/api/v1/profile-setup/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["mom_status"] == "pregnant"
    assert data["data"]["partner"]["email"] == "dad@test.com"

def test_submit_profile_invalid_enum(client, test_user):
    """Test 2: Send an invalid status (Validation Check)"""
    payload = {
        "mom_status": "alien_mom",
        "goals": ["Sleep"]
    }

    response = client.post("/api/v1/profile-setup/", json=payload)
    
    assert response.status_code == 422 

def test_submit_profile_overwrite(client, test_user):
    """Test 3: Verify that submitting twice overwrites the old one"""
    payload = {"mom_status": "new_mom", "goals": ["Sleep"]}
    
    client.post("/api/v1/profile-setup/", json=payload)
    
    payload["mom_status"] = "toddler_mom"
    response = client.post("/api/v1/profile-setup/", json=payload)

    assert response.status_code == 201
    assert response.json()["data"]["mom_status"] == "toddler_mom"
    
    db = TestingSessionLocal()
    count = db.query(ProfileSetup).filter_by(user_id=test_user.id).count()
    assert count == 1
    db.close()