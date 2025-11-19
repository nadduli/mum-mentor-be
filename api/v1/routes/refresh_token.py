from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.db.database import get_db
from api.utils.responses import auth_response, fail_response
from api.v1.schemas.refresh_tokens import RefreshTokenRequest
from api.v1.services.auth_service import (
	create_access_token,
	generate_refresh_token,
	refresh_token_expiry,
)
from api.v1.models.user.user import UserAuthSession, UserActivityLog, User


router = APIRouter()


@router.post("/auth/refresh", tags=["auth"])
def refresh_access_token(
    payload: RefreshTokenRequest,
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

    try:
        # Find session by refresh token
        session = (
            db.query(UserAuthSession)
            .filter(UserAuthSession.refresh_token == payload.refresh_token)
            .first()
        )

        if not session:
            return fail_response(
                status.HTTP_401_UNAUTHORIZED, "Invalid refresh token provided."
            )

        if session.is_revoked:
            return fail_response(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked.")

        if session.expires_at and session.expires_at < now:
            return fail_response(status.HTTP_401_UNAUTHORIZED, "Refresh token expired.")

        # Optional device binding check
        device_header = request.headers.get("X-Device-Id")
        if session.device_id and device_header and session.device_id != device_header:
            return fail_response(
                status.HTTP_403_FORBIDDEN, "Device mismatch for refresh token."
            )

        # Load user
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            return fail_response(status.HTTP_401_UNAUTHORIZED, "User not found for token.")

        # Create new access token
        access_token = create_access_token(user.id)

        # Rotate refresh token: generate a new one and extend expiry
        new_refresh = generate_refresh_token()
        session.refresh_token = new_refresh
        session.expires_at = refresh_token_expiry()
        session.updated_at = now

        # Log refresh activity
        activity = UserActivityLog(
            user_id=session.user_id,
            activity_type="refresh_token",
            ip_address=(request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
            activity_metadata={"rotated": True},
        )
        db.add(activity)
        db.add(session)
        db.commit()  

        return auth_response(
            status.HTTP_200_OK,
            "Access token refreshed successfully.",
            access_token,
            new_refresh,
            data={"user_id": str(user.id)},
        )
    except Exception as e:
        db.rollback()  # Roll back any changes on error
        import traceback
        tb = traceback.format_exc()
        print("DEBUG: Exception in refresh_access_token:\n", tb)
        return fail_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred during token refresh.",
        )