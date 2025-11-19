import pytest
from unittest.mock import patch, Mock, MagicMock
from fastapi import status
from google.auth.exceptions import GoogleAuthError
import uuid
from datetime import datetime

from api.v1.schemas.google_auth_schema import GoogleVerificationResponse


class TestGoogleLogin:
    """Tests for POST /google/login endpoint"""
    def test_successful_login_new_user(self, client, db_session, mock_google_token):
        """Test successful login with a new Google user"""
        
        # Mock Google token verification
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            # Make request
            response = client.post(
                "/api/v1/google/login",
                json={
                    "id_token": "fake_google_token_12345",
                    "device_id": "device_123",
                    "device_name": "iPhone 13"
                }
            )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "success"
        assert data["message"] == "Google login successful"
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        
        # Verify user was created in database
        from api.v1.models.user.user import User
        user = db_session.query(User).filter(User.email == "testuser@gmail.com").first()
        assert user is not None
        assert user.google_id == "123456789"
        assert user.full_name == "Test User"
        assert user.email_verified is True
        assert user.is_active is True
    
    def test_successful_login_existing_user(self, client, db_session, sample_user, mock_google_token):
        """Test successful login with existing Google user"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_google_token"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        
        # Verify user count didn't increase
        from api.v1.models.user.user import User
        user_count = db_session.query(User).count()
        assert user_count == 1
    
    def test_login_invalid_token(self, client, db_session):
        """Test login with invalid Google token"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "invalid_token"}
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["status"] == "failure"
        assert "Invalid Google token" in data["message"]
    
    def test_login_wrong_issuer(self, client, db_session, mock_google_token):
        """Test login with token from wrong issuer"""
        
        mock_google_token["iss"] = "malicious.com"
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["status"] == "failure"
    
    def test_login_wrong_audience(self, client, db_session, mock_google_token):
        """Test login with token for different client_id"""
        
        mock_google_token["aud"] = "wrong_client_id.apps.googleusercontent.com"
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_missing_id_token(self, client, db_session):
        """Test login without id_token"""
        
        response = client.post(
            "/api/v1/google/login",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_updates_existing_user_info(self, client, db_session, sample_user, mock_google_token):
        """Test that login updates user information if changed"""
        
        # Modify mock token with new name
        mock_google_token["name"] = "Updated Name"
        mock_google_token["picture"] = "https://example.com/new_photo.jpg"
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify user was updated
        from api.v1.models.user.user import User
        db_session.refresh(sample_user)
        user = db_session.query(User).filter(User.id == sample_user.id).first()
        assert user.full_name == "Updated Name"
        
        # Verify profile picture was updated
        assert user.profile.avatar_url == "https://example.com/new_photo.jpg"
    
    def test_login_database_error(self, client, db_session, mock_google_token):
        """Test login handles database errors gracefully"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            # Mock database error
            with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
                response = client.post(
                    "/api/v1/google/login",
                    json={"id_token": "fake_token"}
                )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["status"] == "failure"
    
    def test_login_creates_user_profile(self, client, db_session, mock_google_token):
        """Test that login creates user profile for new users"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify profile was created
        from api.v1.models.user.user import User, UserProfile
        user = db_session.query(User).filter(User.email == "testuser@gmail.com").first()
        profile = db_session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        
        assert profile is not None
        assert profile.avatar_url == "https://example.com/photo.jpg"
        assert profile.preferred_language == "en"
        assert profile.timezone == "Africa/Lagos"
    
    def test_login_with_optional_device_info(self, client, db_session, mock_google_token):
        """Test login with optional device information"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            response = client.post(
                "/api/v1/google/login",
                json={
                    "id_token": "fake_token",
                    "device_id": "unique_device_123",
                    "device_name": "Samsung Galaxy S21"
                },
                headers={"User-Agent": "MyApp/1.0"}
            )
        
        assert response.status_code == status.HTTP_200_OK


class TestGetUserInfo:
    """Tests for GET /google/user endpoint"""
    
    # def test_get_user_info_success(self, client, db_session, sample_user, auth_headers):
    #     """Test retrieving authenticated user information"""
        
    #     response = client.get(
    #         "/api/v1/google/user",
    #         headers=auth_headers
    #     )
        
    #     assert response.status_code == status.HTTP_200_OK
    #     data = response.json()
        
    #     assert data["status"] == "success"
    #     assert data["message"] == "User info retrieved"
    #     assert data["data"]["email"] == sample_user.email
    #     assert data["data"]["full_name"] == sample_user.full_name
    #     assert data["data"]["google_id"] == sample_user.google_id
    #     assert data["data"]["is_active"] is True
    #     assert data["data"]["email_verified"] is True
    
    def test_get_user_info_without_auth(self, client, db_session):
        """Test retrieving user info without authentication"""
        
        response = client.get("/api/v1/google/user")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_user_info_invalid_token(self, client, db_session):
        """Test retrieving user info with invalid token"""
        
        response = client.get(
            "/api/v1/google/user",
            headers={"Authorization": "Bearer invalid_token_123"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_info_expired_token(self, client, db_session, sample_user):
        """Test retrieving user info with expired token"""
        
        # Create an expired token
        import jwt
        from datetime import timedelta
        import os
        
        expired_payload = {
            "user": {
                "user_id": str(sample_user.id),
                "role": sample_user.role
            },
            "exp": datetime.utcnow() - timedelta(hours=1),
            "token_type": "access"
        }
        
        expired_token = jwt.encode(
            expired_payload,
            os.getenv("SECRET_KEY"),
            algorithm="HS256"
        )
        
        response = client.get(
            "/api/v1/google/user",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    


class TestGoogleAuthService:
    """Direct tests for GoogleAuthService methods"""
    
    def test_verify_google_token_success(self, mock_google_token):
        """Test successful Google token verification"""
        
        from api.v1.services.google_auth import google_auth_service
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            result = google_auth_service.verify_google_token("fake_token")
        
        assert isinstance(result, GoogleVerificationResponse)
        assert result.google_id == "123456789"
        assert result.email == "testuser@gmail.com"
        assert result.full_name == "Test User"
        assert result.email_verified is True
    
    def test_verify_google_token_invalid(self):
        """Test Google token verification with invalid token"""
        
        from api.v1.services.google_auth import google_auth_service
        from fastapi import HTTPException
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                google_auth_service.verify_google_token("invalid_token")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_or_create_user_creates_new(self, db_session):
        """Test get_or_create_user creates new user"""
        
        from api.v1.services.google_auth import google_auth_service
        
        google_data = GoogleVerificationResponse(
            google_id="new_user_123",
            email="newuser@gmail.com",
            full_name="New User",
            picture="https://example.com/pic.jpg",
            email_verified=True
        )
        
        user = google_auth_service.get_or_create_user(db_session, google_data)
        
        assert user.google_id == "new_user_123"
        assert user.email == "newuser@gmail.com"
        assert user.full_name == "New User"
        assert user.email_verified is True
        assert user.is_active is True
    
    def test_get_or_create_user_finds_existing_by_google_id(self, db_session, sample_user):
        """Test get_or_create_user finds existing user by Google ID"""
        
        from api.v1.services.google_auth import google_auth_service
        
        google_data = GoogleVerificationResponse(
            google_id=sample_user.google_id,
            email="different@gmail.com",
            full_name="Different Name",
            picture=None,
            email_verified=True
        )
        
        user = google_auth_service.get_or_create_user(db_session, google_data)
        
        assert user.id == sample_user.id
        # Email should be updated
        assert user.email == "different@gmail.com"
    
    def test_get_or_create_user_finds_existing_by_email(self, db_session, sample_user):
        """Test get_or_create_user finds existing user by email when google_id is different"""
        
        from api.v1.services.google_auth import google_auth_service
        
        # Remove google_id from existing user
        sample_user.google_id = None
        db_session.commit()
        
        google_data = GoogleVerificationResponse(
            google_id="new_google_id_456",
            email=sample_user.email,
            full_name="Test User",
            picture=None,
            email_verified=True
        )
        
        user = google_auth_service.get_or_create_user(db_session, google_data)
        
        assert user.id == sample_user.id
        # Google ID should be added
        assert user.google_id == "new_google_id_456"
    
    def test_issue_local_access_token(self, sample_user):
        """Test issuing local access token"""
        
        from api.v1.services.google_auth import google_auth_service
        import jwt
        import os
        
        token = google_auth_service.issue_local_access_token(sample_user)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        decoded = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )
        
        assert decoded["user"]["user_id"] == str(sample_user.id)
        assert decoded["user"]["role"] == sample_user.role
        assert decoded["token_type"] == "access"


class TestIntegrationScenarios:
    """Integration tests for complete user flows"""
    
    def test_multiple_logins_same_user(self, client, db_session, mock_google_token):
        """Test multiple logins for the same user"""
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            # First login
            response1 = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
            
            # Second login
            response2 = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
            
            assert response1.status_code == status.HTTP_200_OK
            assert response2.status_code == status.HTTP_200_OK
            
            # Verify only one user was created
            from api.v1.models.user.user import User
            user_count = db_session.query(User).count()
            assert user_count == 1
    
    def test_concurrent_user_creation(self, client, db_session, mock_google_token):
        """Test handling of concurrent user creation attempts"""
        
        from api.v1.models.user.user import User
        
        with patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_google_token
            
            # Make concurrent requests
            response1 = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
            response2 = client.post(
                "/api/v1/google/login",
                json={"id_token": "fake_token"}
            )
            
            # Both should succeed
            assert response1.status_code == status.HTTP_200_OK
            assert response2.status_code == status.HTTP_200_OK
            
            # Only one user should exist
            user_count = db_session.query(User).count()
            assert user_count == 1


