from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid

from api.v1.models.user.user import User, UserOTPVerification
from api.v1.schemas.verify_otp import VerifyOTP


def verify_otp_service(db: Session, data: VerifyOTP):
    """
    Verify an OTP code for a user. Enforces expiration and retry limits.

    Raises HTTPException on failure. On success marks the OTP as used and
    updates user verification flags where applicable.
    """
    # Convert user_id string to UUID
    try:
        user_uuid = uuid.UUID(data.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Fetch user
    current_user = db.query(User).filter(User.id == user_uuid).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch latest matching unused OTP for the user and otp_type
    otp_record = (
        db.query(UserOTPVerification)
        .filter(
            UserOTPVerification.user_id == current_user.id,
            UserOTPVerification.otp_type == data.otp_type,
            UserOTPVerification.used == False,
        )
        .order_by(UserOTPVerification.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(status_code=404, detail="OTP record not found")

    now = datetime.now(timezone.utc)

    # Make expires_at timezone-aware if it's naive (for SQLite compatibility)
    expires_at = otp_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    # Check expiration
    if expires_at < now:
        otp_record.used = True
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Check if already exceeded attempts
    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.used = True
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=403, detail="OTP locked due to too many attempts")

    # Validate code
    if otp_record.otp_code != data.otp_code:
        otp_record.attempts = (otp_record.attempts or 0) + 1
        if otp_record.attempts >= otp_record.max_attempts:
            otp_record.used = True
        db.add(otp_record)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    # Successful verification
    otp_record.used = True
    otp_record.used_at = now
    db.add(otp_record)

    # Update user's verified status depending on otp_type
    t = data.otp_type.lower()
    if t in ("email_verification", "email", "register"):
        current_user.email_verified = True
    if t in ("phone_verification", "phone"):
        current_user.phone_verified = True

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user
