"""
Authentication Dependencies
TODO: Replace mock authentication with real JWT validation when auth team completes their work
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user.user import User


async def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Get current authenticated user
    TODO: Replace with real JWT token validation
    """
    user = db.query(User).filter(User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No test user found. Create a user first."
        )
    
    return user
