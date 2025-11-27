import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from api.db.base_model import BaseModel
import enum

class MotherCategory(str, enum.Enum):
    """Predefined milestone categories for mothers."""
    BODY_RECOVERY = "Body Recovery"
    MENTAL_WELLNESS = "Mental Wellness"
    ROUTINE_BUILDER = "Routine Builder"
    SELF_CARE = "Self Care"

class ChildCategory(str, enum.Enum):
    """Predefined milestone categories for children."""
    DEVELOPMENT = "Development"
    HEALTH_NUTRITION = "Health and Nutrition"
    ACTIVITIES_PLAY = "Activities and Play"
    GROWTH_CHECK = "Growth Check"

class MilestoneCategory(BaseModel):
    __tablename__ = "milestone_categories"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    owner_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "mother" | "child"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    milestones: Mapped[List["Milestone"]] = relationship(back_populates="milestone_category")

class Milestone(BaseModel):
    __tablename__ = "milestones"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    owner_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "mother" | "child"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | completed
    
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milestone_categories.id"), nullable=False)
    category_name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # For mother: Body Recovery | Mental Wellness | Routine Builder | Self Care
       # For child: Development | Health and Nutrition | Activities and Play | Growth Check
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    milestone_category: Mapped["MilestoneCategory"] = relationship(back_populates="milestones")
