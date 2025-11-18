from sqlalchemy.orm import Session
from api.v1.models.user.user import User
from api.utils.security import verify_password, hash_password

def change_user_password(user: User, old_password: str, new_password: str, db: Session):
    # Verify old password
    if not verify_password(old_password, user.password_hash):
        return False, "Old password is incorrect"

    # Hash new password
    user.password_hash = hash_password(new_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return True, "Password changed successfully"
