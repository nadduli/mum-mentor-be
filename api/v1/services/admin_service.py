from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple
import re

from api.v1.models.user.user import User
from api.v1.schemas.admin import AdminCreate
from api.utils.security import hash_password
from api.utils.logger import logger
from pydantic import SecretStr

# Password validation rules
PASSWORD_RULES = (
    (re.compile(r".{8,}"), "Password must be at least 8 characters long"),
    (re.compile(r"[A-Z]"), "Password must contain at least one uppercase letter"),
    (re.compile(r"[a-z]"), "Password must contain at least one lowercase letter"),
    (re.compile(r"\d"), "Password must contain at least one digit"),
    (re.compile(r"[!@#$%^&*(),.?\":{}|<>]"), "Password must contain at least one special character"),
)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength. Returns (is_valid, error_message)."""
    for pattern, message in PASSWORD_RULES:
        if not pattern.search(password):
            return False, message
    return True, ""


def create_admin(db: Session, admin_in: AdminCreate) -> Tuple[Optional[User], Optional[str]]:
    """
    Create an admin user.
    
    Args:
        db: Database session
        admin_in: Admin registration data
        
    Returns:
        Tuple of (User object, error message)
        Returns (User, None) on success
        Returns (None, error_message) on failure
    """
    try:
        # 1) Extract plaintext password from SecretStr (or accept plain str)
        if isinstance(admin_in.password, SecretStr):
            plain_password = admin_in.password.get_secret_value()
        else:
            plain_password = str(admin_in.password)

        # 2) Validate password strength
        ok, msg = validate_password_strength(plain_password)
        if not ok:
            logger.warning("Admin registration failed: weak password for %s", admin_in.email)
            return None, msg

        # 3) Prevent creating super_admin via this endpoint
        requested_role = (admin_in.role or "admin").lower()
        if requested_role == "super_admin":
            logger.warning(
                "Attempt to create super_admin via admin endpoint for email: %s",
                admin_in.email
            )
            return None, "Cannot create 'super_admin' via this endpoint."

        # 4) Check duplicates (email/phone)
        if admin_in.email:
            existing = User.fetch_unique(db, email=admin_in.email)
            if existing:
                logger.warning(
                    "Admin registration attempt with existing email: %s",
                    admin_in.email
                )
                return None, "A user with this email already exists."

        if admin_in.phone:
            existing_phone = User.fetch_unique(db, phone=admin_in.phone)
            if existing_phone:
                logger.warning(
                    "Admin registration attempt with existing phone: %s",
                    admin_in.phone
                )
                return None, "A user with this phone already exists."

        # 5) Hash password
        hashed = hash_password(plain_password)

        # 6) Create User
        user = User(
            full_name=admin_in.full_name,
            email=admin_in.email,
            phone=admin_in.phone,
            password_hash=hashed,
            role=requested_role,
            is_active=True,
        )

        user.insert(db)
        
        logger.info("Admin user created successfully: %s with role: %s", user.email, user.role)
        return user, None
        
    except IntegrityError:
        db.rollback()
        logger.error(
            "Database integrity error during admin creation for email: %s",
            admin_in.email
        )
        return None, "A user with this email or phone already exists."
    except Exception as e:
        db.rollback()
        logger.error(
            "Error creating admin user %s: %s",
            admin_in.email,
            str(e),
            exc_info=True
        )
        return None, "An error occurred while creating the admin account."