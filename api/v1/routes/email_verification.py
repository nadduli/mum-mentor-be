from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import os

from api.v1.schemas.user import (
    EmailVerificationRequest,
    ResendVerificationRequest
)
from api.v1.services.email_verification import EmailVerificationService
from api.v1.services.email_services import send_email
from api.v1.models.user.user import User
from api.db.database import get_db
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify user email",
    description="""
        Verify a user's email address using a verification token.

        This endpoint confirms a user's email by validating the verification token sent
        to their registered email address.

        ### How It Works
        - The user receives an email containing a verification link with a *token*.
        - The user clicks the link, which calls this endpoint.
        - If the token is valid and not expired, the user's email is marked as verified."""
)
def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    logger.info("Email verification attempt with token")
    
    user, error = EmailVerificationService.verify_email_token(db, request.token)
    
    if error:
        logger.warning("Email verification failed: %s", error)
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error
        )
    
    if not user:
        logger.error("Email verification returned None without error")
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to verify email"
        )
    
    logger.info("Email verified successfully for user: %s", user.email)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Email verified successfully",
        data={"email_verified": True}
    )


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
    description="""Resend email verification link to user
        Resend Email Verification Link

        This endpoint allows a user to request a new email verification link if they
        did not receive the original one or it has expired.

        ### When to Use This
        - The user registered but never received the verification email.
        - The user’s previous verification token has expired.
        - The user wants a fresh verification link."""
)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    logger.info("Resend verification request for email: %s", request.email)
    
    user = User.fetch_unique(db, email=request.email.lower())
    
    if not user:
        # Return generic message for security
        return success_response(
            status_code=status.HTTP_200_OK,
            message="If the email exists, a verification link has been sent"
        )
    
    if user.email_verified:
        logger.info("User email already verified: %s", request.email)
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Email is already verified"
        )
    
    recent_count = EmailVerificationService.get_recent_verification_count(
        db, str(user.id), minutes=60
    )
    
    if recent_count >= 3:
        logger.warning("Rate limit exceeded for user: %s", request.email)
        return fail_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message="Too many verification requests. Please try again later"
        )
    
    EmailVerificationService.invalidate_old_tokens(db, str(user.id))
    
    verification_token, error = EmailVerificationService.create_verification_record(
        db, str(user.id)
    )
    
    if error or not verification_token:
        logger.error("Failed to create verification token for: %s", request.email)
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to generate verification token"
        )
    
    if not user.email:
        logger.error("User has no email address: %s", str(user.id))
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="User email not found"
        )
    
    try:
        subject = "Verify Your Email Address"
        body = f"""Hi {user.full_name},

We're so glad to have you here. You're one step closer to experiencing a calmer, more supported motherhood journey with Nora.

Whether you're navigating pregnancy, caring for a newborn, or guiding a growing child — Nora is here with trusted answers, gentle guidance, and support whenever you need it.

Please use the verification code below to confirm your email and complete your setup:

{verification_token.token}

This verification code will expire in 24 hours.

Thanks,
The Nora Team"""
        
        # Send email and check if it was successful
        await send_email(user.email, subject, body)
        
        
        logger.info("Verification email sent successfully to: %s", request.email)
        
    except Exception as email_error:
        logger.error(
            "Failed to send verification email to %s: %s",
            request.email,
            str(email_error),
            exc_info=True
        )
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to send verification email. Please try again later."
        )
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Verification email sent successfully"
    )