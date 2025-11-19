# api/v1/routers/google_auth.py
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger
from api.v1.schemas.google_auth_schema import GoogleAuthRequest, GoogleAuthResponse, UserResponse
from api.v1.services.google_auth import google_auth_service
from api.utils.deps import get_current_user
from fastapi.security import HTTPAuthorizationCredentials
from api.v1.services.google_auth import GoogleVerificationResponse

router = APIRouter(prefix="/google", tags=["Google Authentication"])


@router.post("/login", status_code=status.HTTP_200_OK, response_model=GoogleAuthResponse)
async def google_login(payload: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """
    Accepts a Google `id_token` from the client (React Native / Expo).
    Verifies the token with Google, creates/updates a local user, and returns a local access token.
    """
    logger.info("Google login attempt")
    # verify id_token with Google
    try:
        google_data: GoogleVerificationResponse = await run_verify(payload.id_token)
    except Exception as exc:
        logger.warning("Google token verification failed: %s", str(exc))
        return fail_response(status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid Google token")

    # get or create user
    try:
        user = google_auth_service.get_or_create_user(db, google_data)
    except Exception as exc:
        logger.error("Failed to get or create user: %s", str(exc))
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to create user")

    # optionally record session metadata (device_id, device_name, ip, user-agent) - skipped for refresh tokens
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # issue local access token
    try:
        access_token = google_auth_service.issue_local_access_token(user)
    except Exception as exc:
        logger.error("Failed to create local access token: %s", str(exc))
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to create access token")

    logger.info("Google login successful for user_id=%s ip=%s", user.id, client_ip)

    # return access token (no refresh_token stored)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Google login successful",
        data=GoogleAuthResponse(access_token=access_token).model_dump()
    )


async def run_verify(token: str) -> GoogleVerificationResponse:
    """
    Helper to call the service verify method which is synchronous (keeps route clean).
    """
    # google_auth_service.verify_google_token is sync; we can call it directly (no await).
    # But the route is async; call synchronously.
    return google_auth_service.verify_google_token(token)


@router.get("/user", status_code=status.HTTP_200_OK)
def get_current_user_info(current_user=Depends(get_current_user)):  # wire to your deps.get_current_user
    """
    Return basic information about the currently authenticated user.
    Make sure this route uses your existing deps.get_current_user dependency in production.
    """
    if not current_user:
        return fail_response(status_code=status.HTTP_401_UNAUTHORIZED, message="Unauthorized")
    user_resp = UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        google_id=current_user.google_id,
        role=getattr(current_user, "role", None)
    )
    return success_response(status_code=status.HTTP_200_OK, message="User info retrieved", data=user_resp.model_dump())


@router.get("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_access_token(token: str):
    """
    Endpoint to refresh access token using a refresh token.
   """
    
    pass