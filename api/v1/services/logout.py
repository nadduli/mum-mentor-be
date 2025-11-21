from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID
from api.v1.models.blacklist import TokenBlacklist
from api.v1.models.user.user import UserAuthSession
from api.utils.login import get_token_expiration, decode_token
from api.utils.logger import logger


class Logout:
    def __init__(self, db: Session):
        self.db = db

    def blacklist_token(self, token: str, user_id: UUID, reason: str = "logout") -> bool:
        """Add token to blacklist using BaseModel methods"""
        try:
            # Check if token is already blacklisted
            if TokenBlacklist.is_token_blacklisted(self.db, token):
                return True

            # Get token expiration
            expiration = get_token_expiration(token)
            if not expiration:
                return False

            # Get token type from payload
            payload = decode_token(token)
            token_type = payload.get("token_type", "access") if payload else "access"

            blacklisted_token = TokenBlacklist(
                token=token,
                token_type=token_type,
                expires_at=expiration,
                user_id=user_id,
                reason=reason
            )
            blacklisted_token.insert(self.db)
            
            logger.info(f"Token blacklisted for user {user_id}, reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            return False

    def logout_user(self, token: str, user_id: UUID) -> bool:
        """Logout user by blacklisting current token"""
        return self.blacklist_token(token, user_id, "logout")

    def logout_all_sessions(self, user_id: UUID) -> int:
        """Logout from all devices by blacklisting all sessions and tokens"""
        try:
            # Get all sessions using BaseModel method
            sessions = UserAuthSession.fetch_all(self.db, user_id=user_id)
            sessions_ended = 0
            
            for session in sessions:
                # Blacklist the refresh token
                if self.blacklist_token(session.refresh_token, user_id, "logout_all"):
                    sessions_ended += 1
                # Delete the session using BaseModel method
                session.delete(self.db)
            
            logger.info(f"Logged out all {sessions_ended} sessions for user {user_id}")
            return sessions_ended
            
        except Exception as e:
            logger.error(f"Error logging out all sessions: {str(e)}")
            return 0

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired blacklisted tokens using BaseModel method"""
        return TokenBlacklist.cleanup_expired_tokens(self.db)