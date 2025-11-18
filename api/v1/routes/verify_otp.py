from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from api.db.database import get_db
from api.v1.schemas.verify_otp import VerifyOTP
from api.v1.services.verify_otp import verify_otp_service
from api.utils.responses import auth_response
from api.utils.auth_utils import create_access_token, create_refresh_token, get_device_info
from api.v1.models.user.user import UserAuthSession

router = APIRouter()


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTP, db: Session = Depends(get_db), client: Request = None):
    """
    Verify OTP endpoint

    Verifies the OTP code and returns JWT tokens for authentication.
    After successful verification, the user is automatically logged in.
    """
    # Verify OTP and get the user
    user = verify_otp_service(db, request)

    # Generate JWT tokens
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    # Get device information
    ip_address = client.client.host if client and client.client else None
    user_agent = client.headers.get("User-Agent") if client else None
    device_name = get_device_info(user_agent).get("device") if user_agent else None

    # Create auth session
    session = UserAuthSession(
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_name,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(session)
    db.commit()

    return auth_response(
        status_code=status.HTTP_200_OK,
        message="OTP verified successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        data={
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified
            }
        }
    )
