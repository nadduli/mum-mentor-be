# api/v1/routers/google_auth.py
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from api.db.database import get_db
from datetime import datetime,  timezone
from api.utils.responses import success_response, fail_response, JSONResponse
from api.utils.logger import logger
from api.v1.models.user.user import UserAuthSession
from api.v1.schemas.google_auth_schema import GoogleAuthRequest, GoogleAuthResponse, UserResponse, RefreshTokenRequest, RevokeRequest
from api.v1.services.google_auth import google_auth_service, run_verify
from api.utils.deps import get_current_user
from api.v1.models.user.user import User
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
    google_data: GoogleVerificationResponse | JSONResponse = await run_verify(payload.id_token)
    if not isinstance(google_data, dict):
        logger.warning("Google token verification failed")
        return google_data

    google_data = GoogleVerificationResponse(**google_data) 
    try:
        user = google_auth_service.get_or_create_user(db, google_data)
        if not isinstance(user, User):
            return user
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        session = google_auth_service.create_session(
            db,
            user=user,
            device_id=payload.device_id,
            device_name=payload.device_name,
            ip_address=client_ip,
            user_agent=user_agent,
        )
    except Exception as exc:
        logger.error("Failed to get or create user: %s", str(exc))
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to create user")

    # optionally record session metadata (device_id, device_name, ip, user-agent) - skipped for refresh tokens
    

    # issue local access token
    try:
        access_token = google_auth_service.issue_local_access_token(user, sid = str(session.id))
        refresh_token = google_auth_service.issue_local_refresh_token(user, sid = str(session.id))
    except Exception as exc:
        logger.error("Failed to create local access token: %s", str(exc))
        return fail_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to create access token")

    logger.info("Google login successful for user_id=%s ip=%s", user.id, client_ip)

    # return access token (no refresh_token stored)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Google login successful",
        data=GoogleAuthResponse(access_token=access_token, refresh_token=refresh_token).model_dump()
    )


@router.post(
    "/refresh/",
    response_model=GoogleAuthResponse,
    status_code=status.HTTP_200_OK)
async def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """returns new access and refresh tokens given a valid refresh token
    Args:
        payload (RefreshRequest): takes in refresh token
        db (Session, optional): Defaults to Depends(get_db).
    """
    payload_data = google_auth_service.verify_token(payload.refresh_token, refresh=True)
    if isinstance(payload_data, JSONResponse):
        logger.warning("Invalid refresh token attempt")
        return payload_data
    if not payload_data:
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token"
        )
    sid = payload_data.get('sid')
    user_id = payload_data.get("user_id")
    session = db.query(UserAuthSession).filter(UserAuthSession.id == sid, UserAuthSession.is_revoked == False).first()
    logger.info(f"Session {session}")
    if not session or session.expires_at < datetime.now(timezone.utc):
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Refresh token session is invalid or expired"
        )
    if not user_id:
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token payload"
        )
    user = google_auth_service.get_user_by_id(db, user_id)
    if not user or isinstance(user, JSONResponse):
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User not found"
        )
    sid = str(session.id)
    access_token = google_auth_service.issue_local_access_token(user=user, sid=sid)
    refresh_token = google_auth_service.issue_local_refresh_token(
        user=user, sid=sid
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token refreshed successfully",
        data=GoogleAuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        ).model_dump()
    )




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


@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke(payload: RevokeRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token session
    Args:
        payload (RevokeRequest): takes in refresh token
        db (Session, optional): Defaults to Depends(get_db).
    """
    payload_data = google_auth_service.verify_token(payload.refresh_token, refresh=True)
    if isinstance(payload_data, JSONResponse):
        return payload_data
    logger.info(f"payload_data: {payload_data}")
    if not payload_data:
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token"
        )

    sid = payload_data.get("sid")

    success = google_auth_service.revoke_session(db, str(sid))
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to revoke session"
        )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Session revoked successfully"
    )


# @router.post("/revoke-access", status_code=status.HTTP_200_OK)
# async def revoke(payload: RevokeRequest, db: Session = Depends(get_db)):
#     """Revoke a refresh token session
#     Args:
#         payload (RevokeRequest): takes in refresh token
#         db (Session, optional): Defaults to Depends(get_db).
#     """
#     payload_data = google_auth_service.verify_token(payload.refresh_token, refresh=False)
#     logger.info(f"payload_data: {payload_data}")
#     if not payload_data:
#         return fail_response(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             message="Invalid refresh token"
#         )
    
#     sid = payload_data.get("sid")

#     success = google_auth_service.revoke_session(db, str(sid))
#     if not success:
#         return fail_response(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             message="Failed to revoke session"
#         )
#     return success_response(
#         status_code=status.HTTP_200_OK,
#         message="Session revoked successfully"
#     )