"""Test registration endpoint"""

import pytest

from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.auth
class TestUserRegistration:
    """Test cases for user registration."""

    def test_valid_registration_success(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test successful user registration with valid data."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["status"] == "success"
        assert "verify your account" in data["message"].lower()
        assert "data" in data

        user_data = data["data"]
        assert user_data["full_name"] == sample_user_data["full_name"]
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["email_verified"] is False
        assert user_data["phone_verified"] is False
        assert user_data["role"] == "user"
        assert user_data["is_active"] is True
        assert "id" in user_data
        assert "created_at" in user_data
        assert "password" not in user_data

    def test_duplicate_email_failure(self, client: TestClient, sample_user_data: dict):
        """Test that re-registration with unverified email updates data and sends new OTP."""

        response1 = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        updated_data = sample_user_data.copy()
        updated_data["full_name"] = "Updated Name"
        response2 = client.post("/api/v1/auth/register", json=updated_data)
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert response2.json()["status"] == "failure"

    def test_invalid_email_failure(self, client: TestClient, sample_user_data: dict):
        """Test registration with invalid email format fails."""
        user_data = sample_user_data.copy()
        user_data["email"] = "invalid-email"

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "weak_password",
        [
            "short",
            "nouppercase123!",
            "NOLOWERCASE123!",
            "NoDigits!",
            "NoSpecial123",
        ],
    )
    def test_weak_password_failure(
        self, client: TestClient, sample_user_data: dict, weak_password: str
    ):
        """Test registration with weak password fails."""
        user_data = sample_user_data.copy()
        user_data["password"] = weak_password
        user_data["confirm_password"] = weak_password

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_mismatched_passwords_failure(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test registration with mismatched passwords fails."""
        user_data = sample_user_data.copy()
        user_data["confirm_password"] = "DifferentPass123!"

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "error" in data

    def test_missing_required_fields_failure(self, client: TestClient):
        """Test registration with missing required fields fails."""
        required_fields = ["full_name", "email", "password", "confirm_password"]

        for field in required_fields:
            user_data = {
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            }
            del user_data[field]

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_full_name(self, client: TestClient, sample_user_data: dict):
        """Test registration with invalid full name fails."""
        invalid_names = [
            "123",  # Numbers only
            "Name123",  # Contains numbers
            "Name@#$",  # Contains invalid special characters
            "  ",  # Only whitespace
            "",  # Empty string
        ]

        for invalid_name in invalid_names:
            user_data = sample_user_data.copy()
            user_data["full_name"] = invalid_name

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_valid_full_name_variations_success(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test registration with valid full name variations succeeds."""
        valid_names = [
            "Jane Doe",
            "Mary-Jane Watson",
            "O'Brien",
            "Jean-Pierre",
        ]

        for idx, valid_name in enumerate(valid_names):
            valid_data = sample_user_data.copy()
            valid_data["full_name"] = valid_name
            valid_data["email"] = (
                f"{valid_name.replace(' ', '').lower()}{idx}@example.com"
            )

            response = client.post("/api/v1/auth/register", json=valid_data)
            assert response.status_code == status.HTTP_201_CREATED

            data = response.json()
            assert data["data"]["full_name"] == valid_name.strip()

    def test_email_case_insensitivity_failure(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test that email is case-insensitive for duplicate checking."""

        # First registration with lowercase email and verify
        response1 = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Second registration with uppercase email
        user_data = sample_user_data.copy()
        user_data["email"] = sample_user_data["email"].upper()

        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_409_CONFLICT

    def test_correct_response_structure(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test that registration response has correct structure."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()

        for field in ["status", "status_code", "message", "data"]:
            assert field in response_data.keys()

        user_data = response_data["data"]
        required_fields = [
            "id",
            "full_name",
            "email",
            "email_verified",
            "phone_verified",
            "role",
            "is_active",
            "created_at",
        ]
        for field in required_fields:
            assert field in user_data.keys()

        assert "password" not in user_data
        assert "password_hash" not in user_data

    def test_extra_whitespace_in_name_success(
        self, client: TestClient, sample_user_data: dict
    ):
        """Test that extra whitespace in name is trimmed."""
        data_with_whitespace = sample_user_data.copy()
        data_with_whitespace["full_name"] = "  Jane   Doe  "
        data_with_whitespace["email"] = "whitespace@example.com"

        response = client.post("/api/v1/auth/register", json=data_with_whitespace)

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert response_data["data"]["full_name"] == "Jane Doe"
