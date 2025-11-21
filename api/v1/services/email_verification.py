import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Union
from sqlalchemy.orm import Session
import random

from api.v1.models.user.user import User, EmailVerificationToken
from api.utils.logger import logger

class EmailVerificationService:
    
    TOKEN_EXPIRY_MINUTES = 10
    
    @staticmethod
    def generate_verification_otp() -> str:
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    @staticmethod
    def create_verification_record(
        db: Session,
        user_id: Union[str, uuid.UUID]
    ) -> Tuple[Optional[EmailVerificationToken], Optional[str]]:
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            otp = EmailVerificationService.generate_verification_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=EmailVerificationService.TOKEN_EXPIRY_MINUTES
            )
            
            verification_token = EmailVerificationToken(
                user_id=user_id,
                token=otp,
                expires_at=expires_at,
                used=False
            )
            
            verification_token.add(db)
            
            logger.info("Verification code created for user: %s", user_id)
            return verification_token, None
            
        except ValueError:
            return None, "Invalid user ID format"
        except Exception as e:
            logger.error(
                "Error creating verification code for user %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
            return None, "Failed to create verification code"
    
    @staticmethod
    def verify_email_token(
        db: Session,
        token: str
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            verification_record = EmailVerificationToken.fetch_unique(db, token=token)
            
            if not verification_record:
                logger.warning("Invalid verification code attempt")
                return None, "Invalid verification code"
            
            if verification_record.used:
                logger.warning("Attempt to use already used code")
                return None, "Verification code has already been used"
            
            # Handle timezone for expires_at
            expires_at = verification_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                logger.warning("Attempt to use expired code")
                return None, "Verification code has expired"
            
            user = User.fetch_unique(db, id=verification_record.user_id)
            if not user:
                return None, "User not found"
            
            if user.email_verified:
                return None, "Email is already verified"
            
            # Update user and verification record
            user.email_verified = True
            user.updated_at = datetime.now(timezone.utc)
            
            verification_record.used = True
            verification_record.used_at = datetime.now(timezone.utc)
            verification_record.updated_at = datetime.now(timezone.utc)
            
            # Commit both updates atomically
            db.commit()
            db.refresh(user)
            db.refresh(verification_record)
            
            logger.info("Email verified successfully for user: %s", user.email)
            return user, None
            
        except Exception as e:
            db.rollback()
            logger.error(
                "Error verifying email code: %s",
                str(e),
                exc_info=True
            )
            return None, "An error occurred during email verification"
    
    @staticmethod
    def invalidate_old_tokens(db: Session, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Invalidate all unused verification tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID as string
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            user_uuid = uuid.UUID(user_id)
            
            old_tokens = EmailVerificationToken.fetch_all(
                db, 
                user_id=user_uuid, 
                used=False
            )
            
            for token in old_tokens:
                token.used = True
                token.used_at = datetime.now(timezone.utc)
                token.updated_at = datetime.now(timezone.utc)
            
            logger.info("Invalidated old tokens for user: %s", user_id)
            return True, None
            
        except ValueError:
            logger.error("Invalid user ID format: %s", user_id)
            return False, "Invalid user ID format"
        except Exception as e:
            logger.error(
                "Error invalidating old tokens for user %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
            return False, f"Failed to invalidate old tokens: {str(e)}"
    
    @staticmethod
    def get_recent_verification_count(db: Session, user_id: str, minutes: int = 60) -> int:
        try:
            user_uuid = uuid.UUID(user_id)
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            
            count = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_uuid,
                EmailVerificationToken.created_at >= cutoff_time
            ).count()
            
            return count
            
        except ValueError:
            logger.error("Invalid user ID format: %s", user_id)
            return 0
        except Exception as e:
            logger.error(
                "Error checking verification count for user %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
            return 0