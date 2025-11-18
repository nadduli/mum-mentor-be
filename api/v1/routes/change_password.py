from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.deps import get_current_user
from api.v1.schemas.change_password import ChangePasswordRequest
from api.v1.services.change_password import change_user_password
from api.v1.models.user.user import User

change_password_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@change_password_router.patch("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # new password must match confirm password
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )

    success, message = change_user_password(
        current_user, request.old_password, request.new_password, db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {"message": message}
