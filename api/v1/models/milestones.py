import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.base_model import BaseModel


class Milestone(BaseModel):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    owner_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "mother" | "child"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | completed

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestone_categories.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    category = relationship("MilestoneCategory", back_populates="milestones")