import os
import datetime

import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from user_agents import parse

load_dotenv()

JWT_SECRET = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

pwd_context = CryptContext(schemes="bcrypt", deprecated="auto")

def create_access_token(user_id, role):
    user = {
        "user_id": str(user_id),
        "role": role
    }

    payload = {
        "user": user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        "token_type": "access"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    return token


def create_refresh_token(user_id, role):
    user = {
        "user_id": str(user_id),
        "role": role
    }
    payload = {
        "user": user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "token_type": "refresh"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    return token


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


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