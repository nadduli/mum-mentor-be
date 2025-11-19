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
    """
    Change Password (Logged-in Users Only)

    This endpoint allows an authenticated user to change their password while logged in.

    ### How to Test This Endpoint in Swagger

    1. *Login first* using the /auth/login endpoint.
    2. Copy the *access_token* from the login response.
    3. Click the *Authorize* button at the top of the Swagger page.
    4. Select the authentication scheme and *paste ONLY the token*  
        (Swagger automatically adds the Bearer prefix — do NOT type it yourself).
    5. Now open /auth/change-password and click *Try it out*.

    ### Example Request Body
    json
    {
        "old_password": "OldPass123!",
        "new_password": "NewPass456!",
        "confirm_password": "NewPass456!"
    }

    """

    #new password must match confirm password
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
