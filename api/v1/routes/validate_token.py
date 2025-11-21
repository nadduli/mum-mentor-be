from fastapi import APIRouter, Depends, status
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
from api.utils.responses import success_response


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/validate-token")
def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate JWT access token.

    This endpoint validates the JWT token from the Authorization header
    and returns whether it's valid or not along with basic user information.

    How it works:
    - Client sends request with Bearer token in Authorization header
    - Server validates the token using get_current_user middleware
    - If valid, returns success with user info
    - If invalid/expired, returns 401 Forbidden

    Returns:
        200: Token is valid with user information
        401: Token is invalid or expired

    Example Response:
    {
        "status": "success",
        "status_code": 200,
        "message": "Token is valid",
        "data": {
            "valid": true
        }
    }
    """
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token is valid",
        data={"valid": True}
    )
