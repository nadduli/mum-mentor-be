import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from api.db.base_model import Base
from api.db.database import get_db
from api.v1.models.user.user import User, ProfileSetup, ChildProfile
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
    """Create a user and force auth to use it"""
    db = TestingSessionLocal()
    user = User(full_name="Test Mom", email="mom@test.com", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    app.dependency_overrides[get_current_user] = lambda: user
    return user

@pytest.fixture(scope="function")
def pre_existing_profile(client, test_user):
    """Helper to create a profile BEFORE we try to update it"""
    payload = {
        "mom_status": "pregnant",
        "goals": ["Sleep"],
        "partner": {"name": "Dad", "email": "dad@test.com"},
        "children": []
    }
    client.post("/api/v1/profile-setup/", json=payload)
    return payload


def test_update_partial_fields(client, test_user, pre_existing_profile):
    """Test 1: Update ONLY mom_status, keep goals the same"""
    patch_payload = {
        "mom_status": "new_mom"
    }

    response = client.patch("/api/v1/profile-setup/", json=patch_payload)

    assert response.status_code == 200
    data = response.json()
    
    assert data["data"]["mom_status"] == "new_mom"
    
    assert data["data"]["goals"] == ["Sleep"] 
    assert data["data"]["partner"]["name"] == "Dad"

def test_update_children_list(client, test_user, pre_existing_profile):
    """Test 2: Add a child (verify list replacement logic)"""
    
    patch_payload = {
        "children": [
            {
                "full_name": "New Baby",
                "gender": "male",
                "date_of_birth": str(date.today())
            }
        ]
    }

    response = client.patch("/api/v1/profile-setup/", json=patch_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["children"]) == 1
    assert data["data"]["children"][0]["full_name"] == "New Baby"

    db = TestingSessionLocal()
    count = db.query(ChildProfile).count()
    assert count == 1 # Old children should be gone, new one exists
    db.close()

def test_update_not_found(client, test_user):
    """Test 3: Try to update a profile that doesn't exist yet"""
    patch_payload = {"mom_status": "mixed"}
    
    response = client.patch("/api/v1/profile-setup/", json=patch_payload)
    
    assert response.status_code == 404
    assert "Profile setup not found" in response.json()["message"]

def test_remove_partner(client, test_user, pre_existing_profile):
    """Test 4: Explicitly remove the partner by sending null"""
    patch_payload = {"partner": None}
    
    response = client.patch("/api/v1/profile-setup/", json=patch_payload)
    
    assert response.status_code == 200
    assert response.json()["data"]["partner"] is None