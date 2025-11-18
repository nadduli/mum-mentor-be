from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from dotenv import load_dotenv
import os
import uuid
import secrets
from api.v1.models.user.user import User, UserProfile, UserAuthSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.utils.logger import logger
from api.db.database import get_db

load_dotenv()
auth_scheme = HTTPBearer()



GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = float(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7.0))
ALGORITHM = os.getenv("ALGORITHM", "HS256")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(64))



class GoogleAuthService:
    def __init__(self):
        self.google_client_id = "407408718192.apps.googleusercontent.com"
        
    async def verify_google_token(self, token: str) -> dict:
        """Verify Google ID token and return user info"""
        try:
            logger.info("Verifying Google ID token")
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.google_client_id
            )
            logger.info("Google ID token verified successfully")
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'full_name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_or_create_user(self, db: Session, user_info: dict) -> User:
        """Get existing user or create new one"""

        google_id = user_info['google_id']
        email = user_info.get('email')
        logger.info("Fetching or creating user with Google ID: %s", google_id)
        user = db.query(User).filter(User.google_id == user_info['google_id']).first()
        logger.info("User fetched: %s", user)
        if not user:
            logger.info("No existing user found, creating new user")
            new_user = User(
                id=uuid.uuid4(),
                google_id=google_id,
                email=email,
                full_name=user_info.get("full_name"),
                password_hash=None,
                is_active=True,
                email_verified=user_info.get('email_verified', False),
            )
            logger.info("Creating new user with email: %s", email)
            db.add(new_user)
            db.flush()
            logger.info("New user created with ID: %s", new_user.id)
            try:
                logger.info("Creating user profile for user ID: %s", new_user.id)
                user_profile = UserProfile(
                    id=uuid.uuid4(),
                    user_id=new_user.id,
                    preferred_language="en",
                    avatar_url=user_info.get('picture'),
                    timezone="Africa/Lagos",
                )
                logger.info("User profile created: %s", user_profile)
                db.add(user_profile)
            except Exception as e:
                logger.warning("Failed to create user profile: %s", str(e))
                db.rollback()
                raise e
            logger.info("Committing new user to the database")
            db.commit()
            db.refresh(new_user)
            user = new_user
            logger.info("New user committed with ID: %s", user.id)

        logger.info("Updating user information if necessary for user ID: %s", user.id)
        changed = False
        if email and user.email != email:
            logger.info("Updating email for user ID: %s", user.id)
            user.email = email
            changed = True
            logger.info("Email updated to: %s", email)
        if user.full_name != user_info.get('full_name'):
            logger.info("Updating full name for user ID: %s", user.id)
            user.full_name = user_info.get('full_name')
            changed = True
            logger.info("Full name updated to: %s", user.full_name)
        if getattr(user, "google_id", None) != google_id:
            logger.info("Updating Google ID for user ID: %s", user.id)
            user.google_id = google_id
            changed = True
            logger.info("Google ID updated to: %s", google_id)
        user_email_verified = user_info.get('email_verified', False)
        if user.email_verified != user_email_verified:
            logger.info("Updating email verified status for user ID: %s", user.id)
            user.email_verified = user_email_verified
            changed = True
            logger.info("Email verified status updated to: %s", user_email_verified)

        if changed:
            logger.info("Committing updated user information for user ID: %s", user.id)
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            logger.info("User information updated for user ID: %s", user.id)

        try:
            logger.info("Updating user profile information if necessary for user ID: %s", user.id)
            profile = getattr(user, "profile", None)
            if profile and user_info.get('picture') and profile.avatar_url != user_info.get('picture'):
                logger.info("Updating avatar URL for user ID: %s", user.id)
                profile.avatar_url = user_info.get('picture')
                profile.updated_at = datetime.utcnow()
                db.commit()
                logger.info("Avatar URL updated to: %s", profile.avatar_url)

        except Exception:
            logger.warning("Failed to update user profile: %s", str(e))
            db.rollback()
        
        return user

    def _create_jwt(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        """Create JWT token with expiration and type"""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "type": token_type})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            SECRET_KEY, 
            algorithm=ALGORITHM
        )
        return encoded_jwt
    

    def create_access_token(self, *, user:User) -> str:
        """Create JWT access token"""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": getattr(user, "role", "user"),
        }
        
        return self._create_jwt(
            data=payload,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            token_type="access"
        )
    
    def create_refresh_token(self, *, user: User, session_id: Optional[uuid.UUID] = None) -> str:
        session_id = session_id or uuid.uuid4()
        payload = {
            "sub": str(user.id),
            "sid": str(session_id),
        }
        return self._create_jwt(payload, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")

    def create_session(self, db: Session, *, user: User, device_id: Optional[str] = None, device_name: Optional[str] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None, refresh_token_expires_days: int = 7) -> UserAuthSession:
        """
        Create and persist a refresh session record (UserAuthSession).
        Returns the session object.
        """
        session_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(days=(refresh_token_expires_days or REFRESH_TOKEN_EXPIRE_DAYS))
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
    
    def verify_token(self, token: str, refresh: bool | None) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            logger.info("Token verified successfully")
            if refresh and payload.get("type") != "refresh":
                raise JWTError("Invalid token type")
            if payload.get("type") not in ["access", "refresh"]:
                raise JWTError("Invalid token type")
            logger.info("Token type is valid: %s", payload.get("type"))
            return payload

        except JWTError:
            return {"error": "Could not validate credentials"}

    def revoke_session(self, db: Session, session_id: str) -> bool:
        logger.info("Revoking session with ID: %s", session_id)
        session = db.query(UserAuthSession).filter(UserAuthSession.id == session_id).first()
        if not session:
            return False
        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        logger.info("Session revoked at: %s", session.revoked_at)
        db.commit()
        return True
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(auth_scheme), db: Session = Depends(get_db)) -> User:
        """Get current user from JWT token"""
        logger.info("Getting current user from token")
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token decoded successfully")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        logger.info("Fetching user with ID: %s", user_id)
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning("User not found for ID: %s", user_id)
            raise HTTPException(status_code=401, detail="User not found")
        return user
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Fetch user by ID"""
        logger.info("Fetching user by ID: %s", user_id)
        return db.query(User).filter(User.id == user_id).first()
    
google_auth_service = GoogleAuthService()