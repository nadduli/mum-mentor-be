from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import os

from api.v1.schemas.user import (
    UserRegistrationRequest,
    UserRegistrationResponse
)
from api.v1.services.user_service import UserService
from api.v1.services.email_services import send_email
from api.db.database import get_db
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    response_description="User registration data",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Invalid input or user already exists"},
        500: {"description": "Internal server error"}
    }
)
async def register_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **full_name**: User's full name (2-100 characters)
    - **email**: Valid email address (must be unique)
    - **phone**: Optional phone number (max 20 characters)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **confirm_password**: Must match password
    
    Returns user data.
    """
    logger.info("Registration attempt for email: %s", user_data.email)
    
    user, error, verification_token = await UserService.create_user(db, user_data)
    
    if error:
        logger.warning(
            "Registration failed for %s: %s",
            user_data.email,
            error,
        )
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error
        )
    
    if not user:
        logger.error(
            "User creation returned None without error for %s",
            user_data.email,
        )
        return fail_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create user"
        )
    
    # Send verification email with plain text template
    if verification_token and user.email:
        subject = "Verify Your Email Address"
        body = f"""Hi {user.full_name},

We're so glad to have you here. You're one step closer to experiencing a calmer, more supported motherhood journey with Nora.

Whether you're navigating pregnancy, caring for a newborn, or guiding a growing child — Nora is here with trusted answers, gentle guidance, and support whenever you need it.

Please use the button below to confirm your email and complete your setup:

{verification_token}

This verification code will expire in 24 hours.

Thanks,
The Nora Team"""
        
        await send_email(user.email, subject, body)
    
    # Prepare response data
    user_response = UserRegistrationResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )
    
    logger.info("Registration successful for user: %s", user.email)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="User registered successfully. Please check your email to verify your account.",
        data=user_response.model_dump()
    )
