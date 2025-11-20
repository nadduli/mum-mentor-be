from typing import Optional, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.v1.models.user.user import User
from api.v1.schemas.user import UserRegistrationRequest
from api.v1.services.email_verification import EmailVerificationService
from api.utils.security import hash_password
from api.utils.logger import logger

class UserService:
    """Service class for user-related operations"""

    @staticmethod
    async def create_user(
        db: Session,
        user_data: UserRegistrationRequest
    ) -> Tuple[Optional[User], Optional[str], Optional[str]]:
        """
        Create a new user account
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Tuple of (User object, error message, verification token)
            Returns (User, None, token) on success
            Returns (None, error_message, None) on failure
        """
        try:
            existing_user = User.fetch_unique(db, email=user_data.email.lower())
            
            if existing_user:
                # Allow re-registration if email is NOT verified
                if not existing_user.email_verified:
                    logger.info(
                        "Re-registration for unverified email: %s",
                        user_data.email,
                    )
                    
                    # Update existing user with new data
                    existing_user.full_name = user_data.full_name.strip()
                    existing_user.password_hash = hash_password(user_data.password)
                    existing_user.update(db)
                    
                    # Invalidate old verification tokens
                    EmailVerificationService.invalidate_old_tokens(db, str(existing_user.id))
                    
                    # Generate new OTP
                    verification_token_record, error = EmailVerificationService.create_verification_record(
                        db, str(existing_user.id)
                    )
                    
                    if error or not verification_token_record:
                        logger.error("Failed to create verification token for: %s", user_data.email)
                        return None, "Failed to generate verification code", None
                    
                    token = verification_token_record.token
                    logger.info("User data updated and new verification code generated: %s", existing_user.email)
                    return existing_user, None, token
                
                # Block registration if email IS verified
                else:
                    logger.warning(
                        "Registration attempt with verified email: %s",
                        user_data.email,
                    )
                    return None, "User already exists", None
            
            # Create new user if email doesn't exist
            new_user = User(
                full_name=user_data.full_name.strip(),
                email=user_data.email.lower() if user_data.email else None,
                password_hash=hash_password(user_data.password),
                email_verified=False,
                phone_verified=False
            )
            
            new_user.insert(db)
            
            verification_token_record, error = EmailVerificationService.create_verification_record(
                db, str(new_user.id)
            )
            
            token = verification_token_record.token if verification_token_record else None
            
            logger.info("User registered successfully: %s", new_user.email)
            return new_user, None, token
            
        except IntegrityError:
            db.rollback()
            logger.error(
                "Database integrity error during registration for email: %s",
                user_data.email,
            )
            return None, "User already exists", None
        except Exception as e:
            db.rollback()
            logger.error(
                "Error creating user %s: %s",
                user_data.email,
                str(e),
                exc_info=True,
            )
            return None, "An error occurred while creating the account", None