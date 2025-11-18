from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.security import verify_password  # ✅ Import at top level
from api.v1.models.user.user import User, UserAuthSession, UserActivityLog
from api.utils.responses import auth_response
from api.utils.login import create_access_token, create_refresh_token, get_device_info
from api.v1.schemas.login import LoginRequest
from api.utils.logger import logger

login_router = APIRouter(prefix='/auth', tags=['Authentication'])


@login_router.post('/login', status_code=status.HTTP_200_OK)
def login_route(request: LoginRequest, db: Session = Depends(get_db), client: Request = None):
    try:
        ip_address = client.client.host if client.client else None
        user_agent = client.headers.get("User-Agent")
        device_name = get_device_info(user_agent).get("device")

        logger.info(f"Login attempt for email: {request.email}")
        
        user = User.fetch_unique(db, email=request.email, is_active=True)
        if not user:
            logger.warning(f"User not found or not active: {request.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active user not found")

        logger.info(f"User found: {user.email}")
        logger.info(f"User is_active: {user.is_active}")
        logger.info(f"User password_hash type: {type(user.password_hash)}")
        logger.info(f"User password_hash: {user.password_hash}")
        logger.info(f"Input password: {request.password}")

        # ✅ Use the verify_password imported from top (NO local import)
        password_match = verify_password(request.password, str(user.password_hash))
        logger.info(f"Password verification result: {password_match}")
        
        if not password_match:
            logger.warning(f"Password mismatch for user: {user.email}")
            log = UserActivityLog(
                user_id=user.id,
                activity_type="login",
                ip_address=ip_address,
                user_agent=user_agent,
                activity_metadata={"status": "unsuccessful", "details": "invalid password"}
            )
            log.insert(db)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        logger.info(f"Login successful for user: {user.email}")
        
        # Update user using BaseModel method
        user.last_login_at = datetime.now(timezone.utc)
        user.update(db)

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id, user.role)

        # Use BaseModel insert for session
        session = UserAuthSession(
            user_id=user.id,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )

        session.insert(db)

        
        log = UserActivityLog(
            user_id=user.id,
            activity_type="login",
            ip_address=ip_address,
            user_agent=user_agent,
            activity_metadata={"status": "success"}
        )
        log.insert(db)

        return auth_response(
            status_code=200,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name
                }
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"exception occurred in login route: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)