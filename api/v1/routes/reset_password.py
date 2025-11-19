from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.schemas.reset_password import ResetPassword
from api.v1.services.reset_password import reset_password_service
from api.utils.responses import success_response
reset_router = APIRouter(prefix='/auth', tags=['Authentication'])

@reset_router.patch("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    """
    
    Reset User Password (Step 3 of 3)

    Final step of the password reset flow.

    This endpoint updates the user's password after their OTP has been verified.

    Args:
        request: ResetPassword schema containing new_password and confirm_password.
        db: Database session.

    Returns:
        A success message confirming the password has been reset.

    """
    reset_password_service(db, request)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Password reset successfully"
    )