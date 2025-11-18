import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Union
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
        user_id: Union[str, uuid.UUID]
    ) -> Tuple[Optional[EmailVerificationToken], Optional[str]]:
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            token = EmailVerificationService.generate_verification_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=EmailVerificationService.TOKEN_EXPIRY_HOURS)
            
            verification_token = EmailVerificationToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                used=False
            )
            
            verification_token.insert(db)
            
            logger.info(f"Verification token created for user: {user_id}")
            return verification_token, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating verification token: {str(e)}", exc_info=True)
            return None, "Failed to create verification token"
    
    @staticmethod
    def verify_email_token(
        db: Session,
        token: str
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            verification_record = EmailVerificationToken.fetch_unique(db, token=token)
            
            if not verification_record:
                return None, "Invalid verification token"
            
            if verification_record.used:
                return None, "Verification token has already been used"
            
            expires_at = verification_record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                return None, "Verification token has expired"
            
            user = User.fetch_unique(db, id=verification_record.user_id)
            
            if not user:
                return None, "User not found"
            
            if user.email_verified:
                return None, "Email is already verified"
            
            user.email_verified = True
            verification_record.used = True
            verification_record.used_at = datetime.now(timezone.utc)
            
            db.add(user)
            db.add(verification_record)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Email verified successfully for user: {user.id}")
            return user, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying email token: {str(e)}", exc_info=True)
            return None, "An error occurred during email verification"
    
    @staticmethod
    def invalidate_old_tokens(db: Session, user_id: Union[str, uuid.UUID]) -> None:
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            old_tokens = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used == False
            ).all()
            
            for token in old_tokens:
                token.used = True
                token.used_at = datetime.now(timezone.utc)
                db.add(token)
            
            db.commit()
            logger.info(f"Invalidated old tokens for user: {user_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error invalidating old tokens: {str(e)}", exc_info=True)
    
    @staticmethod
    def get_recent_verification_count(db: Session, user_id: Union[str, uuid.UUID], minutes: int = 60) -> int:
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            
            count = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.created_at >= cutoff_time
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error checking verification count: {str(e)}", exc_info=True)
            return 0
