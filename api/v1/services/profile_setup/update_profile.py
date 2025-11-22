from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
import uuid

from api.v1.models.user.user import ProfileSetup, ChildProfile
from api.v1.schemas.profile_setup.update_profile import ProfileSetupUpdate
from api.utils.logger import logger

class ProfileUpdateService:
    
    @staticmethod
    def update(session: Session, user_id: uuid.UUID, payload: ProfileSetupUpdate):
        setup = session.scalar(
            select(ProfileSetup).where(ProfileSetup.user_id == user_id)
        )
        
        if not setup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Profile setup not found. Please complete initial setup first."
            )

        update_data = payload.model_dump(exclude_unset=True)

        if "mom_status" in update_data:
            setup.mom_status = update_data["mom_status"]
        
        if "goals" in update_data:
            setup.goals = [g.strip() for g in update_data["goals"] if g.strip()]

        if "partner" in update_data:
            if update_data["partner"] is None:
                setup.partner = None
            else:
                setup.partner = update_data["partner"]

        if "children" in update_data:
            setup.children = [] 
            
            new_children = []
            for child_data in update_data["children"]:
                new_child = ChildProfile(
                    full_name=child_data["full_name"],
                    date_of_birth=child_data.get("date_of_birth"),
                    due_date=child_data.get("due_date"),
                    gender=child_data.get("gender")
                )
                new_children.append(new_child)
            
            setup.children = new_children

        setup.update(session)
        
        logger.info(f"Profile updated for user {user_id}")
        
        return setup