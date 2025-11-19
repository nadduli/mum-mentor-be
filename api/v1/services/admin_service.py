from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Tuple, Dict, Any
import re

from api.v1.models.user.user import User
from api.v1.schemas.admin import AdminCreate
from api.utils.security import hash_password
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


def create_admin(db: Session, admin_in: AdminCreate) -> Tuple[User, Dict[str, Any]]:
    """
    Create an admin user with default profile and settings.
    Returns tuple (created_user, meta) where meta contains helpful info.
    Raises ValueError on validation issues.
    """

    # 1) Extract plaintext password from SecretStr (or accept plain str)
    if isinstance(admin_in.password, SecretStr):
        plain_password = admin_in.password.get_secret_value()
    else:
        # Accept str for backward compatibility
        plain_password = str(admin_in.password)

    # 2) Validate password strength
    ok, msg = validate_password_strength(plain_password)
    if not ok:
        raise ValueError(msg)

    # 2) Prevent creating super_admin via this endpoint
    requested_role = (admin_in.role or "admin").lower()
    if requested_role == "super_admin":
        raise ValueError("Cannot create 'super_admin' via this endpoint.")

    # 3) Check duplicates (email/phone)
    if admin_in.email:
        existing = User.fetch_unique(db, email=admin_in.email)
        if existing:
            raise ValueError("A user with this email already exists.")

    if admin_in.phone:
        existing_phone = User.fetch_unique(db, phone=admin_in.phone)
        if existing_phone:
            raise ValueError("A user with this phone already exists.")

    # 4) Hash password
    hashed = hash_password(plain_password)

    # 5) Create User
    user = User(
        full_name=admin_in.full_name,
        email=admin_in.email,
        phone=admin_in.phone,
        password_hash=hashed,
        role=requested_role,
        is_active=True,
    )

    try:
        user.insert(db)
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Failed to create admin user due to database integrity error.") from e

    # Prepare a safe response dict (do not include password_hash)
    safe_user = {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
    }

    meta = {"message": "Admin account created successfully."}
    return user, {"user": safe_user, **meta}