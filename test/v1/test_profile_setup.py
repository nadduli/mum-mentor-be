from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from main import app
from api.db.database import get_db
from api.db.base_model import Base
from api.v1.models.user.user import User
from api.utils.deps import get_current_user
from api.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


TEST_USER_ID = uuid.uuid4()


def override_get_current_user():
    """Return the test user for authentication override."""
    db = TestingSessionLocal()
    user = db.query(User).filter(User.id == TEST_USER_ID).first()
    db.close()
    return user


# Override FastAPI deps
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Recreate tables and seed a user before each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create test user
    user = User(
        id=TEST_USER_ID,
        full_name="Test User",
        email="test@example.com",
        phone="+2348100000000",
        password_hash=hash_password("password123"),
        email_verified=True,
        phone_verified=True,
        is_active=True,
        role="user",
    )
    db.add(user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


class TestCreateProfileSetup:

    def test_create_profile_setup_success(self):
        """Success: profile setup is created correctly"""
        payload = {
            "mom_status": "pregnant",
            "goals": ["healthy pregnancy", "exercise"],
            "partner": {
                "name": "John Doe",
                "email": "partner@example.com"
            },
            "children": [
                {
                    "full_name": "Baby One",
                    "date_of_birth": "2020-01-01",
                    "gender": "female"
                }
            ]
        }

        response = client.post("/api/v1/profile-setup/", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["mom_status"] == "pregnant"
        assert len(data["data"]["children"]) == 1

    def test_create_profile_setup_duplicate(self):
        """Expected Error: creating profile twice returns 409"""
        payload = {
            "mom_status": "mixed",
            "goals": ["stay active"],
            "partner": None,
            "children": []
        }

        # First attempt → success
        first = client.post("/api/v1/profile-setup/", json=payload)
        assert first.status_code == 201

        # Second attempt → 409 conflict
        second = client.post("/api/v1/profile-setup/", json=payload)
        assert second.status_code == 409

        data = second.json()
        assert data["status"] == "failure"
        assert "already been created" in data["message"]

    def test_create_profile_setup_invalid_payload(self):
        """Invalid Input: missing required fields triggers 422"""
        payload = {
            # mom_status missing!
            "goals": ["good health"]
        }

        response = client.post("/api/v1/profile-setup/", json=payload)
        assert response.status_code == 422

        data = response.json()
        assert "errors" in data["error"]