import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from user_agents import parse
from sqlalchemy.orm import Session

load_dotenv()

JWT_SECRET = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_access_token(user_id, role):
    expires_delta = timedelta(minutes=30)
    expiration = datetime.now(timezone.utc) + expires_delta
    
    user = {
        "user_id": str(user_id),
        "role": role
    }

    payload = {
        "user": user,
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
        "token_type": "access"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token, expiration


def create_refresh_token(user_id, role):
    expires_delta = timedelta(days=7)
    expiration = datetime.now(timezone.utc) + expires_delta
    
    user = {
        "user_id": str(user_id),
        "role": role
    }
    
    payload = {
        "user": user,
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
        "token_type": "refresh"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token, expiration


def decode_token(token: str):
    """Decode JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_expiration(token: str) -> datetime | None:
    """Get expiration time from token without verification"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM], options={"verify_exp": False})
        return datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    except Exception:
        return None


def get_device_info(user_agent_str):
    if not user_agent_str:
        return {"device": "Unknown"}
        
    user_agent = parse(user_agent_str)
    return {
        "browser": user_agent.browser.family,
        "browser_version": user_agent.browser.version_string,
        "os": user_agent.os.family,
        "os_version": user_agent.os.version_string,
        "device": user_agent.device.family,
        "is_mobile": user_agent.is_mobile,
        "is_tablet": user_agent.is_tablet,
        "is_pc": user_agent.is_pc,
        "is_bot": user_agent.is_bot
    }