import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.base_model import BaseModel


class Memory(BaseModel):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("albums.id"), nullable=False)
    photo: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id"), nullable=False) 
    note: Mapped[str] = mapped_column(String(250))
    saved_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    # When an Album is deleted, cascade-delete its memories
    album = relationship("Album", back_populates="memories", cascade="all, delete")
    # When a Photo is deleted, cascade-delete associated memories
    photo_data = relationship("Photos", back_populates="memories", cascade="all, delete")