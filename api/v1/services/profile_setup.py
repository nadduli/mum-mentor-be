import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.v1.models.user.user import ProfileSetup
from api.v1.models.user.user import ChildProfile
from api.v1.schemas.profile_setup import (
    ProfileSetupSubmit,
    ProfileSetupUpdate,
)
from api.utils.logger import logger


class ProfileSetupService:

    @staticmethod
    def submit(session: Session, user_id, payload: ProfileSetupSubmit):
        # 1. Delete existing setup (idempotent overwrite)
        existing = session.scalar(
            select(ProfileSetup).where(ProfileSetup.user_id == user_id)
        )

        if existing:
            session.delete(existing)
            session.commit()

        # 2. Create new setup
        setup = ProfileSetup(
            user_id=user_id,
            mom_status=payload.mom_status,
            goals=[g.strip() for g in payload.goals if g.strip()],
            partner=payload.partner.model_dump() if payload.partner else None,
        )

        session.add(setup)
        session.flush()  # get setup.id

        # 3. Add children
        for child in payload.children:
            session.add(
                ChildProfile(
                    profile_setup_id=setup.id,
                    full_name=child.full_name,
                    date_of_birth=child.date_of_birth,
                    due_date=child.due_date,
                    gender=child.gender,
                )
            )

        session.commit()

        return ProfileSetupService.build_profile(session, setup)

    @staticmethod
    def get(session: Session, user_id):
        profile_setup = session.scalar(
            select(ProfileSetup).where(ProfileSetup.user_id == user_id)
        )
        if profile_setup:
            return ProfileSetupService.build_profile(session, profile_setup)
        return None

    @staticmethod
    def update(session: Session, user_id: uuid.UUID, payload: ProfileSetupUpdate):
        setup = session.scalar(
            select(ProfileSetup).where(ProfileSetup.user_id == user_id)
        )

        if not setup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile setup not found. Please complete initial setup first.",
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
                    gender=child_data.get("gender"),
                )
                new_children.append(new_child)

            setup.children = new_children

        setup.update(session)

        logger.info(f"Profile updated for user {user_id}")

        return setup
        
    @staticmethod
    def build_profile(session: Session, setup: ProfileSetup):
        # Fetch children
        children = session.scalars(
            select(ChildProfile).where(ChildProfile.profile_setup_id == setup.id)
        ).all()

        return {
            "user_id": str(setup.user_id),
            "mom_status": setup.mom_status,
            "goals": setup.goals,
            "partner": setup.partner,
            "children": [
                {
                    "id": str(c.id),
                    "full_name": c.full_name,
                    "date_of_birth": c.date_of_birth,
                    "due_date": c.due_date,
                    "gender": c.gender,
                }
                for c in children
            ],
        }
