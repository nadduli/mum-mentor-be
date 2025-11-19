import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from fastapi import status
from api.v1.models.user.user import User, UserProfile
from api.v1.services.google_auth import GoogleAuthService
from api.v1.schemas.google_auth_schema import GoogleAuthRequest, GoogleVerificationResponse

@pytest.fixture
def google_auth_service():
    return GoogleAuthService()

class TestGoogleAuthService:
    @patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token')
    def test_verify_google_token_success(self, mock_verify, google_auth_service):
        mock_verify.return_value = {
            "sub": "google123",
            "email": "google@gmail.com",
            "name": "Google User",
            "picture": "http://picture.url",
            "iss": "accounts.google.com",
            "aud": google_auth_service.google_client_id
        }
        response = google_auth_service.verify_google_token("valid_token")
        assert response.google_id == "google123"
        assert response.email == "google@gmail.com"
        assert response.full_name == "Google User"
        assert response.email_verified is False
    @patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_token(self, mock_verify, google_auth_service):
        mock_verify.side_effect = Exception("Invalid token")
        with pytest.raises(Exception):
            google_auth_service.verify_google_token("invalid_token")
    @patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_issuer(self, mock_verify, google_auth_service):
        mock_verify.return_value = {
            "sub": "google123",
            "iss": "invalid_issuer",
            "aud": google_auth_service.google_client_id
        }
        with pytest.raises(Exception):
            google_auth_service.verify_google_token("token_with_invalid_issuer")
    @patch('api.v1.services.google_auth.google_id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_audience(self, mock_verify, google_auth_service):
        mock_verify.return_value = {
            "sub": "google123",
            "iss": "accounts.google.com",
            "aud": "wrong_audience"
        }
        with pytest.raises(Exception):
            google_auth_service.verify_google_token("token_with_invalid_audience")
    def test_issue_local_access_token(self, google_auth_service, db_session):
        user = User(
            full_name="Test User",
            email="google@gmail.com",
            password_hash="hashedpassword",
            email_verified=True
        )
        user.insert(db_session)
        token = google_auth_service.issue_local_access_token(user)
        assert isinstance(token, str)
    def test_get_or_create_user_new_user(self, google_auth_service, db_session):
        google_data = GoogleVerificationResponse(
            google_id="google_new_123",
            email="google@gmail.com",
            full_name="Google New User",
            email_verified=True
        )
        user = google_auth_service.get_or_create_user(db_session, google_data)
        assert user.google_id == "google_new_123"


    