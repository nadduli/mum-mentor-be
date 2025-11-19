import argparse
from datetime import datetime, timedelta, timezone
import uuid
import os

from dotenv import load_dotenv

load_dotenv()

from api.db.database import SessionLocal
from api.v1.models.user.user import User, UserOTPVerification


def create_otp(user_identifier: str, otp_code: str = "123456", minutes: int = 10):
    db = SessionLocal()
    try:
        # Try to parse as UUID first, otherwise treat as email
        user = None
        try:
            user_uuid = uuid.UUID(user_identifier)
            user = db.query(User).filter(User.id == user_uuid).first()
        except Exception:
            # treat as email
            user = db.query(User).filter(User.email == user_identifier).first()

        if not user:
            print("User not found. Provide a valid UUID or existing user email.")
            return 1

        otp = UserOTPVerification(
            user_id=user.id,
            otp_code=otp_code,
            otp_type="email_verification",
            channel="email",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
            used=False,
        )
        db.add(otp)
        db.commit()
        db.refresh(otp)

        print(f"Created OTP record:\n  user_id: {user.id}\n  otp_code: {otp.otp_code}\n  otp_id: {otp.id}\n  expires_at: {otp.expires_at}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an OTP record for testing verify-otp endpoint")
    parser.add_argument("user", help="User UUID or email to attach the OTP to")
    parser.add_argument("--code", default="123456", help="OTP code to insert (default: 123456)")
    parser.add_argument("--minutes", type=int, default=10, help="How many minutes until OTP expires")

    args = parser.parse_args()
    exit(create_otp(args.user, otp_code=args.code, minutes=args.minutes))
