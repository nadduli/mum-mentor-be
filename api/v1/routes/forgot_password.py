from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.schemas.forgot_password import ForgotPassword
from api.v1.services.forgot_password import forgot_password_service
from api.utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPassword,
    db: Session = Depends(get_db)
):
    """
    Handle forgot password request.
    
    Sends a password reset link to the user's email address.
    
    Args:
        request: ForgotPassword schema with email
        db: Database session
        
    Returns:
        Success response with confirmation message
    """
    result = await forgot_password_service(db, request.email)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message=result["message"],
        data={"email": result["email"]}
    )