from sqlalchemy import select
from sqlalchemy.orm import Session

from api.v1.models.user.user import ProfileSetup
from api.v1.models.user.user import ChildProfile
from api.v1.schemas.profile_setup.profile_setup import ProfileSetupSubmit


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
    def build_profile(session: Session, setup: ProfileSetup):
        # Fetch children
        children = session.scalars(
            select(ChildProfile).where(
                ChildProfile.profile_setup_id == setup.id
            )
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
            ]
        }