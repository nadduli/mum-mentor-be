import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from api.v1.models.milestones import (
    Milestone as MilestoneModel,
    MilestoneCategory,
)
from api.v1.schemas.milestones import (
    ListMilestonesData,
    MilestoneCategory as MilestoneCategorySchema,
    Pagination,
    MilestoneCategoryStats,
    Milestone as MilestoneSchema,
)


class MilestoneService:
    @staticmethod
    def get_milestones_by_category(
        db: Session,
        category_id: uuid.UUID,
        user_id: uuid.UUID,
        milestone_status: str,
        child_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 10,
    ):
        owner_id = child_id if child_id else user_id
        owner_type = "child" if child_id else "mother"

        category = db.get(MilestoneCategory, category_id)
        if not category or category.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )

        milestones_query = select(MilestoneModel).where(
            MilestoneModel.category_id == category_id,
            MilestoneModel.owner_id == owner_id,
            MilestoneModel.owner_type == owner_type,
            MilestoneModel.status == milestone_status,
        )

        total_milestones = db.scalar(
            select(func.count()).select_from(milestones_query.subquery())
        )
        total_pages = (total_milestones + limit - 1) // limit

        offset = (page - 1) * limit
        milestones = db.scalars(
            milestones_query.order_by(MilestoneModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        pending_milestones = db.scalar(
            select(func.count(MilestoneModel.id)).where(
                MilestoneModel.category_id == category_id,
                MilestoneModel.owner_id == owner_id,
                MilestoneModel.owner_type == owner_type,
                MilestoneModel.status == "pending",
            )
        )
        completed_milestones = db.scalar(
            select(func.count(MilestoneModel.id)).where(
                MilestoneModel.category_id == category_id,
                MilestoneModel.owner_id == owner_id,
                MilestoneModel.owner_type == owner_type,
                MilestoneModel.status == "completed",
            )
        )

        category_data = MilestoneCategorySchema(
            id=category.id,
            owner_id=category.owner_id,
            owner_type=category.owner_type,
            name=category.name,
            description=category.description,
            created_at=category.created_at,
            updated_at=category.updated_at,
            stats=MilestoneCategoryStats(
                pending_milestones=pending_milestones,
                completed_milestones=completed_milestones,
            ),
        )

        milestones_data = [
            MilestoneSchema.model_validate(m) for m in milestones
        ]

        return ListMilestonesData(
            category=category_data,
            milestones=milestones_data,
            pagination=Pagination(
                next_cursor=str(page + 1) if page < total_pages else None,
                prev_cursor=str(page - 1) if page > 1 else None,
                per_page=limit,
            ),
        )
