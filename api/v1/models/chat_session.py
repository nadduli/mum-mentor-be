# api/v1/models/chat/chat_session.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.base_model import BaseModel

class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    summary: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="Compressed context when conversation exceeds 50 messages"
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship - all messages in this session
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete")