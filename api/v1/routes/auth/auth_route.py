import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timedelta
from pydantic import EmailStr, BaseModel
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user.user import User, UserAuthSession, UserActivityLog
from api.utils.responses import auth_response
from api.utils.auth_utils import verify_password, create_access_token, create_refresh_token, get_device_info


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


logger = logging.getLogger(__name__)

login_router = APIRouter(prefix='/users')


@login_router.post('/login', status_code=status.HTTP_200_OK)
def login(request: LoginRequest, db: Session = Depends(get_db), client: Request = None):
    try:
        ip_address = client.client.host if client.client else None
        user_agent = client.headers.get("User-Agent")
        device_name = get_device_info(user_agent).get("device")

        user = db.query(User).filter(User.email == request.email, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active user not found")

        if not verify_password(request.password, user.password_hash):
            log = UserActivityLog(
                user_id=user.id,
                activity_type="login",
                ip_address=ip_address,
                user_agent=user_agent,
                activity_metadata={"status": "unsuccessful", "details": "invalid password"}
            )
            db.add(log)
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id, user.role)

        session = UserAuthSession(
            user_id=user.id,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=device_name,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        db.add(session)
        db.commit()

        log = UserActivityLog(
            user_id=user.id,
            activity_type="login",
            ip_address=ip_address,
            user_agent=user_agent,
            activity_metadata={"status": "success"}
        )
        db.add(log)
        db.commit()

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