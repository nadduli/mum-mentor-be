from sqlalchemy.orm import Session
from fastapi import HTTPException
from api.utils import hash_password, verify_password
from api.v1.models.user.user import User
from api.v1.schemas.reset_password import ResetPassword


def reset_password_service(db: Session, data: ResetPassword, user_id: str = None):
    """
    Reset user password
    
    Args:
        db: Database session
        data: ResetPassword schema containing old and new passwords
        user_id: User ID from JWT (TODO: extract from middleware)
    
    Raises:
        HTTPException: 401 if password doesn't match, 404 if user not found, 400 if passwords don't match
    
    Returns:
        None
    """
    # TODO: Extract user_id from JWT middleware
    if not user_id:
        user_id = ""  # Placeholder until middleware is implemented
    
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    current_user = db.query(User).filter(User.id == user_id).first()
    
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Old password is incorrect")
    
    hashed_password = hash_password(data.new_password)
    current_user.password_hash = hashed_password
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return None