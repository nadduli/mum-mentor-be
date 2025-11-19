from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from jwt import InvalidTokenError

from api.db.database import get_db
from api.utils.responses import auth_response, fail_response
from api.v1.services.refresh_service import refresh_access_token_service
from api.utils.logger import logger
from api.v1.models.user.user import UserAuthSession, UserActivityLog, User


router = APIRouter(prefix="/auth", tags=['Authentication'])


@router.post("/refresh",status_code=status.HTTP_200_OK,
summary="Refresh Access Token",
response_description="New access and refresh tokens",
responses={
200: {"description": "Access token refreshed successfully"},
401: {"description": "Unauthorized"},
403: {"description": "Device mismatch for refresh token"},
500: {"description": "Internal server error"}
})
def refresh_access_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh an access token using a valid refresh token.

    Security measures implemented:
    - Validates the refresh token exists in the DB and is not revoked.
    - Ensures the refresh session has not expired.
    - Optionally enforces device binding via `X-Device-Id` header when available.
    - Rotates the refresh token on success and updates expiry.
    - Logs the refresh action in `user_activity_logs`.
    """
    now = datetime.now(timezone.utc)

    # Extract token from Authorization header
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return fail_response(status.HTTP_401_UNAUTHORIZED, "Missing Authorization header")

    incoming_token = auth_header.split(" ", 1)[1].strip()

    device_header = request.headers.get("X-Device-Id")
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    data, error = refresh_access_token_service(db, incoming_token, device_header, client_host, user_agent)

    if error:
        #logger for errors
        logger.warning(f"Refresh token error: {error.get('message')}")
        return fail_response(error.get("status_code", status.HTTP_401_UNAUTHORIZED), error.get("message"))

    # logger success
    logger.info("Access token refreshed successfully.")
    return auth_response(
        status.HTTP_200_OK,
        "Access token refreshed successfully.",
        data.get("access_token"),
        data.get("refresh_token"),
        data={"user_id": data.get("user_id")},
    )