from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from api.v1.models.user.user import User
from api.v1.schemas.user import UserRegistrationRequest
from api.utils.security import hash_password
from api.utils.logger import logger


class UserService:
    """Service class for user-related operations"""

    @staticmethod
    def create_user(
        db: Session,
        user_data: UserRegistrationRequest
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user account
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Tuple of (User object, error message)
            Returns (User, None) on success
            Returns (None, error_message) on failure
        """
        try:
            # Check if user already exists using BaseModel fetch_unique
            # existing_user = User.fetch_unique(db, email=user_data.email.lower())
            result = db.execute(
                select(User).where(User.email == user_data.email.lower())
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.warning(
                    "Registration attempt with existing email: %s",
                    user_data.email,
                )
                return None, "User with this email already exists"
            
            # Create new user
            new_user = User(
                full_name=user_data.full_name.strip(),
                email=user_data.email.lower() if user_data.email else None,
                # phone=user_data.phone,
                password_hash=hash_password(user_data.password),
                email_verified=False,
                phone_verified=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info("User registered successfully: %s", new_user.email)
            return new_user, None
            
        except IntegrityError:
            db.rollback()
            logger.error(
                "Database integrity error during registration for email: %s",
                user_data.email,
            )
            return None, "User with this email already exists"
        except Exception as e:
            db.rollback()
            logger.error(
                "Error creating user %s: %s",
                user_data.email,
                str(e),
                exc_info=True,
            )
            return None, "An error occurred while creating the account"