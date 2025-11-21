from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user.user import User
import os
import uuid

oauth2_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def get_current_user(
    credentials : HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception
    
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = payload.get("user")
        if not user_data:
            raise credentials_exception

        user_id = user_data.get("user_id")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Convert user_id string to UUID
    try:
        user_id_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id_uuid).first()

    if user is None:
        raise credentials_exception

    return user


def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency to verify user is an admin.
    Raises HTTPException with 403 Forbidden if user is not admin.
    Returns the admin user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required",
    )

    if credentials is None:
        raise credentials_exception
    
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = payload.get("user")
        if not user_data:
            raise credentials_exception

        user_id = user_data.get("user_id")
        role = user_data.get("role")
        
        if not user_id:
            raise credentials_exception
        
        if role != "admin":
            raise forbidden_exception
            
    except JWTError:
        raise credentials_exception

    # Convert user_id string to UUID
    try:
        user_id_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id_uuid).first()

    if user is None:
        raise credentials_exception
    
    if user.role != "admin":
        raise forbidden_exception

    return user