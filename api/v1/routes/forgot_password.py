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
    
    Forgot Password (Step 1 of 3)

    This is the first step in the password reset flow for users who are *logged out*.

    ###  Step-by-Step Reset Process
    1. *Forgot Password (this endpoint)*  
    - User submits their email.  
    - A password reset OTP/code is generated and sent to the user's email.

    2. *Verify OTP*  
    - User enters the OTP received in their email to confirm ownership.

    3. *Reset Password*  
    - After OTP verification, user submits a new password to complete the reset.

    ### What This Endpoint Does
    - Checks if the email belongs to a registered user.
    - Generates a one-time OTP/reset code.
    - Sends the OTP to the user's email address.

    ### After Calling This Endpoint
    The user should take the OTP they received and send it to the /auth/verify-otp endpoint to continue with Step 2.


    
    """
    result = await forgot_password_service(db, request.email)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message=result["message"],
        data={"email": result["email"]}
    )