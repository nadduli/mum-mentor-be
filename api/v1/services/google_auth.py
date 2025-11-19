# api/v1/services/google_auth.py
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import os
import secrets
import jwt
from dotenv import load_dotenv
from jose import JWTError
from typing import Optional, Dict, Any

from api.v1.models.user.user import User, UserProfile, UserAuthSession
from api.v1.schemas.google_auth_schema import GoogleVerificationResponse, UserResponse, RefreshTokenRequest, RefreshTokenResponse
from api.utils.auth_utils import create_access_token, verify_reset_password_token, create_refresh_token
from api.utils.logger import logger
load_dotenv()

ALGORITHM = os.getenv("ALGORITHM", "HS256")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(64))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "407408718192.apps.googleusercontent.com")

class GoogleAuthService:
    """
    Service that handles verifying Google ID tokens and mapping them to local users.
    - Verifies token audience/issuer.
    - Creates user if not present.
    - Updates basic user info (email, name, picture, email_verified).
    - Issues a local access token (no refresh tokens stored).
    """

    def __init__(self):
        if not GOOGLE_CLIENT_ID:
            logger.warning("GOOGLE_CLIENT_ID not set in environment")
        self.google_client_id = GOOGLE_CLIENT_ID

    def verify_google_token(self, token: str) -> GoogleVerificationResponse:
        """
        Verify Google ID token and return a typed response.
        Raises HTTPException(401) on failure.
        """
        try:
            logger.info("Verifying Google ID token")
            idinfo = google_id_token.verify_oauth2_token(token, google_requests.Request(), self.google_client_id)
        except Exception as exc:
            logger.warning("Google token verification exception: %s", str(exc))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token")

        # check issuer & audience
        if idinfo.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            logger.warning("Invalid issuer in id token: %s", idinfo.get("iss"))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

        aud = idinfo.get("aud")
        if aud != self.google_client_id:
            logger.warning("Invalid audience in id token: %s (expected: %s)", aud, self.google_client_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

        data = {
            "google_id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "full_name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "email_verified": bool(idinfo.get("email_verified", False)),
        }
        logger.info("Google ID token verified for google_id=%s email=%s", data["google_id"], data["email"])
        return GoogleVerificationResponse(**data)

    def get_or_create_user(self, db: Session, google_data: GoogleVerificationResponse) -> User:
        """
        Given verified google_data, fetch or create a local User record and update profile.
        Returns the SQLAlchemy User instance.
        """
        # Try google_id first
        user = None
        if google_data.google_id:
            user = db.query(User).filter(User.google_id == google_data.google_id).first()

        # fallback to email
        if not user and google_data.email:
            user = db.query(User).filter(User.email == google_data.email).first()

        if not user:
            logger.info("Creating new user from Google data: %s", google_data.email)
            user = User(
                id=uuid.uuid4(),
                google_id=google_data.google_id,
                email=google_data.email,
                full_name=google_data.full_name or "",
                password_hash=None,
                is_active=True,
                email_verified=google_data.email_verified,
            )
            db.add(user)
            db.flush()
            # create profile
            try:
                profile = UserProfile(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    preferred_language="en",
                    avatar_url=google_data.picture,
                    timezone="Africa/Lagos",
                )
                db.add(profile)
            except Exception as e:
                logger.warning("Could not create user profile: %s", str(e))
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user profile")

            db.commit()
            db.refresh(user)
            logger.info("New user created with id=%s", user.id)
            return user

        # update existing user fields if needed
        changed = False
        if google_data.email and user.email != google_data.email:
            user.email = google_data.email
            changed = True
        if google_data.full_name and user.full_name != google_data.full_name:
            user.full_name = google_data.full_name
            changed = True
        if getattr(user, "google_id", None) != google_data.google_id and google_data.google_id:
            user.google_id = google_data.google_id
            changed = True
        if user.email_verified != google_data.email_verified:
            user.email_verified = google_data.email_verified
            changed = True

        if changed:
            user.updated_at = datetime.utcnow()
            try:
                db.commit()
                db.refresh(user)
            except Exception as e:
                logger.warning("Failed to commit user updates: %s", str(e))
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user")

        # update profile avatar if present
        try:
            profile = getattr(user, "profile", None)
            if profile and google_data.picture and profile.avatar_url != google_data.picture:
                profile.avatar_url = google_data.picture
                profile.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()

        return user
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Fetch user by ID"""
        logger.info("Fetching user by ID: %s", user_id)
        return db.query(User).filter(User.id == user_id).first()
    

    def create_session(self, db: Session, *, user: User, device_id: Optional[str] = None, device_name: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None, refresh_token_expires_days: int = 7) -> UserAuthSession:
        """
        Create and persist a refresh session record (UserAuthSession).
        Returns the session object.
        """
        session_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(days=7.0)
        session = UserAuthSession(
            id=session_id,
            user_id=user.id,
            refresh_token=str(uuid.uuid4()),
            device_id=device_id,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    

    def revoke_session(self, db: Session, sid: str) -> bool:
        logger.info("Revoking session with ID: %s", sid)
        if not sid:
            raise HTTPException(
                status_code=400,
                detail = "Token is invalid or not refresh token"
            )
        try:
            session = db.query(UserAuthSession).filter(UserAuthSession.id == sid).first()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = "Invalid session id"
            )
        if not session:
            return False
        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        logger.info("Session revoked at: %s", session.revoked_at)
        db.commit()
        return True

    def issue_local_access_token(self, user: User, sid: str | None) -> str:
        """
        Issue your application's access token for the user.
        Uses your existing auth_utils.create_access_token (unchanged).
        """
        token = create_access_token(user_id=user.id, sid = sid, role=getattr(user, "role", "user"))
        return token
    
    def issue_local_refresh_token(self, user: User, sid: str | None) -> str:
        """
        Issue your application's refresh token for the user.
        Uses your existing auth_utils.create_refresh_token (unchanged).
        """
        
        token = create_refresh_token(user_id=user.id, sid=sid, role=getattr(user, "role", "user"))
        return token
    
    def verify_token(self, token: str, refresh: bool | None) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            logger.info("Token verified successfully")
            logger.info(f"payload {payload}")
            if payload.get("token_type") not in ["access", "refresh"]:
                raise JWTError("Invalid token type")
            
            if refresh and payload.get("token_type") != "refresh":
                raise JWTError("Invalid token type, expected refresh token")
            
            if not refresh and payload.get("token_type") != "access":
                raise JWTError("Invalid token type, expected access")
            
            logger.info("Token type is valid: %s", payload.get("token_type"))
            return payload.get("user")

        except JWTError:
            return {"error": "Could not validate credentials"}
google_auth_service = GoogleAuthService()
