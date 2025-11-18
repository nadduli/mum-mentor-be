import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from api.v1.models.user.user import User, EmailVerificationToken
from api.utils.logger import logger


class EmailVerificationService:
    
    TOKEN_EXPIRY_HOURS = 24
    
    @staticmethod
    def generate_verification_token() -> str:
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_verification_record(
        db: Session,
        user_id: str
    ) -> Tuple[Optional[EmailVerificationToken], Optional[str]]:
        try:
            user_uuid = uuid.UUID(user_id)
            
            user = User.fetch_unique(db, id=user_uuid)
            if not user:
                return None, "User not found"
            
            token = EmailVerificationService.generate_verification_token()
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=EmailVerificationService.TOKEN_EXPIRY_HOURS
            )
            
            verification_token = EmailVerificationToken(
                user_id=user_uuid,
                token=token,
                expires_at=expires_at
            )
            
            verification_token.insert(db)
            
            logger.info("Verification token created for user: %s", user_id)
            return verification_token, None
            
        except ValueError:
            return None, "Invalid user ID format"
        except Exception as e:
            db.rollback()
            logger.error(
                "Error creating verification token for user %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
            return None, "Failed to create verification token"
    
    @staticmethod
    def verify_email_token(
        db: Session,
        token: str
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            verification_record = EmailVerificationToken.fetch_unique(db, token=token)
            
            if not verification_record:
                logger.warning("Invalid verification token attempt")
                return None, "Invalid verification token"
            
            if verification_record.used:
                logger.warning("Attempt to use already used token")
                return None, "Verification token has already been used"
            
            # Handle timezone for expires_at
            expires_at = verification_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                logger.warning("Attempt to use expired token")
                return None, "Verification token has expired"
            
            user = User.fetch_unique(db, id=verification_record.user_id)
            if not user:
                return None, "User not found"
            
            if user.email_verified:
                return None, "Email is already verified"
            
            # Update using BaseModel pattern
            user.email_verified = True
            user.update(db)
            
            verification_record.used = True
            verification_record.used_at = datetime.now(timezone.utc)
            verification_record.update(db)
            
            logger.info("Email verified successfully for user: %s", user.email)
            return user, None
            
        except Exception as e:
            db.rollback()
            logger.error(
                "Error verifying email token: %s",
                str(e),
                exc_info=True
            )
            return None, "An error occurred during email verification"
    
    @staticmethod
    def invalidate_old_tokens(db: Session, user_id: str) -> None:
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
                token.update(db)
            
            logger.info("Invalidated old tokens for user: %s", user_id)
            
        except ValueError:
            logger.error("Invalid user ID format: %s", user_id)
        except Exception as e:
            db.rollback()
            logger.error(
                "Error invalidating old tokens for user %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
    
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