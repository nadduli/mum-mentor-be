# import pytest
# from fastapi import status
# from fastapi.testclient import TestClient


# @pytest.mark.auth
# class TestUserRegistration:
#     """Test cases for user registration."""

#     def test_successful_registration(self, client: TestClient, sample_user_data: dict):
#         """Test successful user registration with valid data."""
#         response = client.post("/api/v1/auth/register", json=sample_user_data)
        
#         assert response.status_code == status.HTTP_201_CREATED
        
#         data = response.json()
#         assert data["status"] == "success"
#         assert "verify your account" in data["message"].lower()
#         assert "data" in data
        
#         user_data = data["data"]
#         assert user_data["full_name"] == sample_user_data["full_name"]
#         assert user_data["email"] == sample_user_data["email"]
#         assert user_data["email_verified"] is False
#         assert user_data["phone_verified"] is False
#         assert user_data["role"] == "user"
#         assert user_data["is_active"] is True
#         assert "id" in user_data
#         assert "created_at" in user_data
#         assert "password" not in user_data



#     def test_duplicate_email_registration(self, client: TestClient, sample_user_data: dict):
#         """Test registration with duplicate email fails."""
#         # First registration
#         response1 = client.post("/api/v1/auth/register", json=sample_user_data)
#         assert response1.status_code == status.HTTP_201_CREATED
        
#         # Second registration with same email
#         response2 = client.post("/api/v1/auth/register", json=sample_user_data)
#         assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
#         data = response2.json()
#         assert data["status"] == "failure"
#         assert "already exists" in data["message"].lower()

#     def test_registration_with_invalid_email(self, client: TestClient, sample_user_data: dict):
#         """Test registration with invalid email format fails."""
#         invalid_data = sample_user_data.copy()
#         invalid_data["email"] = "invalid-email"
        
#         response = client.post("/api/v1/auth/register", json=invalid_data)
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

#     def test_registration_with_weak_password(self, client: TestClient, sample_user_data: dict):
#         """Test registration with weak password fails."""
#         weak_passwords = [
#             "short",  # Too short
#             "nouppercase123!",  # No uppercase
#             "NOLOWERCASE123!",  # No lowercase
#             "NoDigits!",  # No digits
#             "NoSpecial123",  # No special character
#         ]
        
#         for weak_password in weak_passwords:
#             invalid_data = sample_user_data.copy()
#             invalid_data["password"] = weak_password
#             invalid_data["confirm_password"] = weak_password
            
#             response = client.post("/api/v1/auth/register", json=invalid_data)
#             assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

#     def test_registration_with_mismatched_passwords(self, client: TestClient, sample_user_data: dict):
#         """Test registration with mismatched passwords fails."""
#         invalid_data = sample_user_data.copy()
#         invalid_data["confirm_password"] = "DifferentPass123!"
        
#         response = client.post("/api/v1/auth/register", json=invalid_data)
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
#         data = response.json()
#         assert "detail" in data

#     def test_registration_with_missing_required_fields(self, client: TestClient):
#         """Test registration with missing required fields fails."""
#         required_fields = ["full_name", "email", "password", "confirm_password"]
        
#         for field in required_fields:
#             incomplete_data = {
#                 "full_name": "Jane Doe",
#                 "email": "jane@example.com",
#                 "password": "SecurePass123!",
#                 "confirm_password": "SecurePass123!"
#             }
#             del incomplete_data[field]
            
#             response = client.post("/api/v1/auth/register", json=incomplete_data)
#             assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

#     def test_registration_with_invalid_full_name(self, client: TestClient, sample_user_data: dict):
#         """Test registration with invalid full name fails."""
#         invalid_names = [
#             "123",  # Numbers only
#             "Name123",  # Contains numbers
#             "Name@#$",  # Contains invalid special characters
#             "  ",  # Only whitespace
#             "",  # Empty string
#         ]
        
#         for invalid_name in invalid_names:
#             invalid_data = sample_user_data.copy()
#             invalid_data["full_name"] = invalid_name
            
#             response = client.post("/api/v1/auth/register", json=invalid_data)
#             assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

#     def test_registration_with_valid_full_name_variations(self, client: TestClient, sample_user_data: dict):
#         """Test registration with valid full name variations succeeds."""
#         valid_names = [
#             "Jane Doe",
#             "Mary-Jane Watson",
#             "O'Brien",
#             "Jean-Pierre",
#         ]
        
#         for idx, valid_name in enumerate(valid_names):
#             valid_data = sample_user_data.copy()
#             valid_data["full_name"] = valid_name
#             valid_data["email"] = f"user{idx}@example.com"
            
#             response = client.post("/api/v1/auth/register", json=valid_data)
#             assert response.status_code == status.HTTP_201_CREATED
            
#             data = response.json()
#             assert data["data"]["full_name"] == valid_name.strip()



#     def test_registration_email_case_insensitivity(self, client: TestClient, sample_user_data: dict):
#         """Test that email is case-insensitive for duplicate checking."""
#         # First registration with lowercase email
#         response1 = client.post("/api/v1/auth/register", json=sample_user_data)
#         assert response1.status_code == status.HTTP_201_CREATED
        
#         # Second registration with uppercase email
#         duplicate_data = sample_user_data.copy()
#         duplicate_data["email"] = sample_user_data["email"].upper()
        
#         response2 = client.post("/api/v1/auth/register", json=duplicate_data)
#         assert response2.status_code == status.HTTP_400_BAD_REQUEST

#     def test_registration_response_structure(self, client: TestClient, sample_user_data: dict):
#         """Test that registration response has correct structure."""
#         response = client.post("/api/v1/auth/register", json=sample_user_data)
        
#         assert response.status_code == status.HTTP_201_CREATED
        
#         data = response.json()
        
#         # Check top-level structure
#         assert "status" in data
#         assert "status_code" in data
#         assert "message" in data
#         assert "data" in data
        
#         # Check user data structure
#         user_data = data["data"]
#         required_fields = [
#             "id", "full_name", "email",
#             "email_verified", "phone_verified", 
#             "role", "is_active", "created_at"
#         ]
#         for field in required_fields:
#             assert field in user_data
        
#         # Ensure sensitive data is not exposed
#         assert "password" not in user_data
#         assert "password_hash" not in user_data

#     def test_registration_with_extra_whitespace_in_name(self, client: TestClient, sample_user_data: dict):
#         """Test that extra whitespace in name is trimmed."""
#         data_with_whitespace = sample_user_data.copy()
#         data_with_whitespace["full_name"] = "  Jane   Doe  "
#         data_with_whitespace["email"] = "whitespace@example.com"
        
#         response = client.post("/api/v1/auth/register", json=data_with_whitespace)
        
#         assert response.status_code == status.HTTP_201_CREATED
        
#         response_data = response.json()
#         assert response_data["data"]["full_name"] == "Jane   Doe"  # Internal whitespace preserved, edges trimmed
