from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from api.v1.services.google_auth import google_auth_service
from api.db.database import get_db
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger
from api.v1.schemas.google_auth_schema import (
    GoogleAuthRequest,
    GoogleAuthResponse,
    RefreshRequest,
    RevokeRequest,
)
from api.v1.models.user.user import UserAuthSession

router = APIRouter(prefix="/google", tags=["Google Authentication"])


@router.post(
    "/login/",
    response_model=GoogleAuthResponse,
    status_code=status.HTTP_200_OK)
async def google_login(payload: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user via Google OAuth2 token.
    
    - **token**: Google ID token obtained from client-side authentication.
    
    Returns access and refresh tokens upon successful authentication.
    """
    logger.info("Google login attempt")

    try:
        info = await google_auth_service.verify_google_token(payload.id_token)
    except ValueError as e:
        logger.warning("Google token verification failed: %s", str(e))
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid Google token"
        )
    try:
        user = google_auth_service.get_or_create_user(db, info)
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
        access_token = google_auth_service.create_access_token(user=user)
        refresh_token = google_auth_service.create_refresh_token(
            user=user,
            session_id=session.id
        )
        logger.info("Google login successful for user ID: %s", user.id)    
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Google login successful",
            data=GoogleAuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            ).model_dump()
        )
    except Exception as e:
        logger.error("Google login failed: %s", str(e))
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=str(e)
        )
    
@router.post(
    "/refresh/",
    response_model=GoogleAuthResponse,
    status_code=status.HTTP_200_OK)
async def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """returns new access and refresh tokens given a valid refresh token

    Args:
        payload (RefreshRequest): takes in refresh token
        db (Session, optional): Defaults to Depends(get_db).
    """
    payload_data = google_auth_service.verify_token(payload.refresh_token, refresh=True)
    if not payload_data:
        logger.warning("Invalid refresh token attempt")
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token"
        )

    sid = payload_data.get("sid")
    user_id = payload_data.get("sub")

    session = db.query(UserAuthSession).filter(UserAuthSession.id == sid, UserAuthSession.is_revoked == False).first()
    if not session or session.expires_at < datetime.utcnow():
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Refresh token session is invalid or expired"
        )
    user = google_auth_service.get_user_by_id(db, user_id)
    if not user:
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User not found"
        )
    access_token = google_auth_service.create_access_token(user=user)
    refresh_token = google_auth_service.create_refresh_token(
        user=user,
        session_id=session.id
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

@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke(payload: RevokeRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token session

    Args:
        payload (RevokeRequest): takes in refresh token
        db (Session, optional): Defaults to Depends(get_db).
    """
    payload_data = google_auth_service.verify_token(payload.refresh_token, refresh=True)
    if not payload_data:
        return fail_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid refresh token"
        )
    sid = payload_data.get("sid")

    success = google_auth_service.revoke_session(db, sid)
    if not success:
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to revoke session"
        )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Session revoked successfully"
    )

@router.get("/user", status_code=status.HTTP_200_OK)
async def get_user_info(current_user=Depends(google_auth_service.get_current_user)):
    """Get Google authenticated user info
    Args:
        current_user (User, optional): Defaults to Depends(google_auth_service.get_current_user).
    """
    logger.info("Google user info accessed")
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User info retrieved successfully",
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_verified": current_user.email_verified,
        }
    )