from typing import Optional, Tuple
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from api.v1.models.user.user import User, UserOTPVerification
from api.v1.schemas.verify_otp import VerifyOTPRequest
from api.utils.logger import logger

class VerifyOTPService:
    """Service class for OTP verification operations"""

    @staticmethod
    def verify_otp(
        db: Session,
        data: VerifyOTPRequest
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Verify an OTP code for a user
        
        Args:
            db: Database session
            data: OTP verification data
            
        Returns:
            Tuple of (User object, error message)
            Returns (User, None) on success
            Returns (None, error_message) on failure
        """
        try:
            # Convert user_id string to UUID
            try:
                user_uuid = uuid.UUID(data.user_id)
            except ValueError:
                return None, "Invalid user ID format"

            # Fetch user using BaseModel pattern
            current_user = User.fetch_unique(db, id=user_uuid)
            if not current_user:
                return None, "User not found"

            # Fetch latest matching unused OTP
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
                return None, "OTP record not found"

            now = datetime.now(timezone.utc)

            # Handle timezone for expires_at
            expires_at = otp_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # Check expiration
            if expires_at < now:
                otp_record.used = True
                otp_record.update(db)
                return None, "OTP has expired"

            # Check attempt limits
            if otp_record.attempts >= otp_record.max_attempts:
                otp_record.used = True
                otp_record.update(db)
                return None, "OTP locked due to too many attempts"

            # Validate OTP code
            if otp_record.otp_code != data.otp_code:
                otp_record.attempts = (otp_record.attempts or 0) + 1
                if otp_record.attempts >= otp_record.max_attempts:
                    otp_record.used = True
                otp_record.update(db)
                return None, "Invalid OTP code"

            # Successful verification
            otp_record.used = True
            otp_record.used_at = now
            otp_record.update(db)

            # Update user verification status
            otp_type = data.otp_type.lower()
            if otp_type in ("email_verification", "email", "register"):
                current_user.email_verified = True
            elif otp_type in ("phone_verification", "phone"):
                current_user.phone_verified = True
            
            current_user.update(db)

            logger.info(
                "OTP verification successful for user: %s, type: %s",
                current_user.email,
                data.otp_type
            )
            return current_user, None

        except Exception as e:
            logger.error(
                "Error during OTP verification for user_id %s: %s",
                data.user_id,
                str(e),
                exc_info=True
            )
            return None, "An error occurred during OTP verification"