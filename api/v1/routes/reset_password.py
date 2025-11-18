from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.schemas.reset_password import ResetPassword
from api.v1.services.reset_password import reset_password_service
from api.utils.responses import success_response
from api.middleware import verify_token

reset_router = APIRouter(prefix='/auth', tags=['Authentication'])

@reset_router.patch("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """
    Reset user password endpoint
    
    Args:
        request: ResetPassword schema with old_password, new_password, confirm_password
        db: Database session
        user_id: User ID from JWT token (extracted by verify_token middleware)
    
    Returns:
        Success response
    """
    reset_password_service(db, request)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password reset successfully"
    )