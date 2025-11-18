from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from api.db.database import get_db
from api.v1.schemas.verify_otp import VerifyOTPRequest
from api.v1.services.verify_otp import VerifyOTPService
from api.utils.auth_utils import create_access_token, create_refresh_token, get_device_info
from api.v1.models.user.user import UserAuthSession
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/verify-otp",
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
    description="Verify OTP code and authenticate user"
)
async def verify_otp(
    request_data: VerifyOTPRequest,
    db: Session = Depends(get_db),
    client: Request = None
):
    """
    Verify OTP endpoint

    Verifies the OTP code and returns JWT tokens for authentication.
    After successful verification, the user is automatically logged in.
    """
    logger.info("OTP verification attempt for user_id: %s", request_data.user_id)
    
    # Verify OTP and get the user
    user, error = VerifyOTPService.verify_otp(db, request_data)
    
    if error:
        logger.warning(
            "OTP verification failed for user_id %s: %s",
            request_data.user_id,
            error
        )
        return fail_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=error
        )
    
   
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    # Get device information
    ip_address = client.client.host if client and client.client else None
    user_agent = client.headers.get("User-Agent") if client else None
    device_name = get_device_info(user_agent).get("device") if user_agent else None

    # Create auth session using BaseModel pattern
    from api.v1.models.user.user import UserAuthSession
    from datetime import datetime, timedelta, timezone
    
    session = UserAuthSession(
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_name,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    session.insert(db)  # Using BaseModel insert method

    logger.info("OTP verification successful for user: %s", user.email)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="OTP verified successfully",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified
            }
        }
    )