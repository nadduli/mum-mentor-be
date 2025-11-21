import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from api.db.base_model import BaseModel


class TokenBlacklist(BaseModel):
    __tablename__ = "token_blacklist"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'access' or 'refresh'
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(200))  # 'logout', 'refresh', etc.

    @classmethod
    def is_token_blacklisted(cls, db, token: str) -> bool:
        """Check if token is blacklisted"""
        blacklisted_token = cls.fetch_unique(db, token=token)
        return blacklisted_token is not None

    @classmethod
    def cleanup_expired_tokens(cls, db):
        """Remove expired tokens from blacklist using BaseModel methods"""
        expired_tokens = cls.fetch_all(db)  # Get all tokens first
        expired_count = 0
        
        for token in expired_tokens:
            if token.expires_at < datetime.now(timezone.utc):
                token.delete(db)
                expired_count += 1
                
        return expired_count