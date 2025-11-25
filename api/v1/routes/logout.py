from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.deps import get_current_user, security
from api.v1.models.user.user import User, UserActivityLog
from api.v1.schemas.logout import LogoutResponse, LogoutAllResponse
from api.v1.services.logout import Logout
from api.utils.responses import success_response
from api.utils.logger import logger
from api.utils.login import get_device_info

router = APIRouter(prefix='/auth', tags=['Authentication'])


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"}
    }
)
def logout_route(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),  # Use security instead of oauth2_scheme
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log out user and blacklist current access token.
    
    - Blacklists the current JWT access token
    - Logs the logout activity
    - Token becomes immediately invalid
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        device_name = get_device_info(user_agent).get("device") if user_agent else "Unknown"
        
        token = credentials.credentials
        
        logger.info(f"Logout initiated for user: {current_user.email}")

        # Blacklist the current token
        auth_service = Logout(db)
        success = auth_service.logout_user(token, current_user.id)
        
        if not success:
            logger.warning(f"Failed to blacklist token for user: {current_user.email}")

        # Log the logout activity
        log = UserActivityLog(
            user_id=current_user.id,
            activity_type="logout",
            ip_address=ip_address,
            user_agent=user_agent,
            activity_metadata={
                "status": "success",
                "device": device_name,
                "token_blacklisted": success
            }
        )
        log.insert(db)

        return success_response(
            status_code=200,
            message="Logout successful. Token has been revoked.",
            data={"success": True}
        )

    except Exception as e:
        logger.error(f"Error during logout for user {current_user.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )