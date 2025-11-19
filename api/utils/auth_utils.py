import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from user_agents import parse

load_dotenv()

JWT_SECRET = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

pwd_context = CryptContext(schemes="bcrypt", deprecated="auto")

def create_access_token(user_id, role, sid = None):
    user = {
        "user_id": str(user_id),
        "role": role,
        "sid": str(sid)
    }

    payload = {
        "user": user,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "token_type": "access"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    return token


def create_refresh_token(user_id, role, sid = None):
    user = {
        "user_id": str(user_id),
        "role": role,
        "sid": sid
    }
    payload = {
        "user": user,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "token_type": "refresh"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    return token


def get_device_info(user_agent_str):
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
    
def verify_reset_password_token(token: str) -> dict[str, str]:
    try:
      return jwt.decode(token, JWT_SECRET, ALGORITHM)
    except Exception as e:
      raise HTTPException(status_code=401, detail=str(e))
    