from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
import uuid

from api.v1.models.milestones import Milestone
from api.v1.models.user.user import ChildProfile, ProfileSetup
from api.v1.schemas.milestone import MilestoneCreate, MilestoneToggle

class MilestoneService:

    @staticmethod
    def _validate_child_ownership(session: Session, user_id: uuid.UUID, child_id: uuid.UUID):
        """
        Security Check: Ensure the child exists AND belongs to the requesting mother.
        """
        # We join tables to find the child linked to this specific user_id
        child = session.query(ChildProfile).join(ProfileSetup).filter(
            ChildProfile.id == child_id,
            ProfileSetup.user_id == user_id
        ).first()

        if not child:
            raise HTTPException(
                status_code=404, 
                detail="Child profile not found or does not belong to you."
            )
        return child

    @staticmethod
    def create(session: Session, user_id: uuid.UUID, payload: MilestoneCreate) -> Milestone:
        if payload.child_id:
            MilestoneService._validate_child_ownership(session, user_id, payload.child_id)
            
            owner_id = payload.child_id
            owner_type = "child"
        else:
            owner_id = user_id
            owner_type = "mother"

        new_milestone = Milestone(
            owner_id=owner_id,
            owner_type=owner_type,
            name=payload.name,
            description=payload.description,
            category_id=payload.category_id,
            status="pending"
        )

        session.add(new_milestone)
        try:
            session.commit()
            session.refresh(new_milestone)
            return new_milestone
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=f"Database Error: {str(e)}")

    @staticmethod
    def toggle_status(session: Session, user_id: uuid.UUID, milestone_id: uuid.UUID, payload: MilestoneToggle) -> Milestone:
        milestone = session.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

        if milestone.owner_type == "child":
            MilestoneService._validate_child_ownership(session, user_id, milestone.owner_id)
        elif milestone.owner_type == "mother":
            if milestone.owner_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        milestone.status = "completed" if payload.completed else "pending"
        
        session.commit()
        session.refresh(milestone)
        return milestone

    @staticmethod
    def get_pending(session: Session, user_id: uuid.UUID, child_id: Optional[uuid.UUID] = None):
        if child_id:
            MilestoneService._validate_child_ownership(session, user_id, child_id)
            target_id = child_id
            target_type = "child"
        else:
            target_id = user_id
            target_type = "mother"

        return session.query(Milestone).filter(
            Milestone.owner_id == target_id,
            Milestone.owner_type == target_type,
            Milestone.status == "pending"
        ).order_by(Milestone.created_at.asc()).all()