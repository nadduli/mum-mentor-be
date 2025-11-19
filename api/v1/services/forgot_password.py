import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user.user import User, UserOTPVerification
from api.v1.services.email_services import send_email


def generate_otp_code() -> str:
    """Generate a 6-digit OTP code."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


async def forgot_password_service(db: Session, email: str):
    """
    Handle forgot password request.
    
    Args:
        db: Database session
        email: User's email address
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or email sending fails
    """
    # Find user by email
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Generate 6-digit OTP
    otp_code = generate_otp_code()
    
    # Invalidate any existing unused password reset OTPs for this user
    existing_otps = db.query(UserOTPVerification).filter(
        UserOTPVerification.user_id == user.id,
        UserOTPVerification.otp_type == "password_reset",
        UserOTPVerification.used == False
    ).all()
    
    for otp in existing_otps:
        otp.used = True
        otp.used_at = datetime.now(timezone.utc)
    
    # Create new OTP record
    otp_record = UserOTPVerification(
        user_id=user.id,
        otp_code=otp_code,
        otp_type="password_reset",
        channel="email",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used=False,
        attempts=0,
        max_attempts=3
    )
    
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    
    # Send password reset email with OTP
    email_body = f"""
    Hello {user.full_name},

    We received a request to reset your password for your Mum Mentor AI account.

    Your password reset code is: {otp_code}

    This code will expire in 15 minutes.

    If you didn't request a password reset, please ignore this email and ensure your account is secure.

    Best regards,
    The Mum Mentor AI Team
    """
    
    try:
        await send_email(
            to_email=user.email,
            subject="Password Reset Code - Mum Mentor AI",
            body=email_body
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset code. Please try again later."
        )
    
    return {
        "message": "Password reset code has been sent to your email",
        "email": user.email
    }
