from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from api.v1.models.user.user import ProfileSetup
from api.v1.models.user.user import ChildProfile
from api.v1.schemas.profile_setup.profile_setup import ProfileSetupSubmit
from api.utils.logger import logger

class ProfileSetupExistsError(Exception):
    """Raised when a user already has a setup profile."""
    pass

class ProfileSetupService:

    @staticmethod
    def create(session: Session, user_id, payload: ProfileSetupSubmit):
        try:
            # Check if profile exists already
            existing = session.scalar(
                select(ProfileSetup).where(ProfileSetup.user_id == user_id)
            )

            if existing:
                logger.info(
                    f"[PROFILE SETUP EXISTS] user_id={user_id} already has a profile."
                )
                raise ProfileSetupExistsError(
                    "A profile has already been created for this user."
                )

            # Create new setup
            setup = ProfileSetup(
                user_id=user_id,
                mom_status=payload.mom_status,
                goals=payload.goals,
                partner=payload.partner.model_dump() if payload.partner else None,
            )

            session.add(setup)
            session.flush()

            # Create children
            for ch in payload.children:
                session.add(
                    ChildProfile(
                        profile_setup_id=setup.id,
                        full_name=ch.full_name,
                        date_of_birth=ch.date_of_birth,
                        due_date=ch.due_date,
                        gender=ch.gender,
                    )
                )

            session.commit()

            logger.info(f"[PROFILE SETUP CREATED] user_id={user_id} setup_id={setup.id}")

            # Build response
            return {
                "id": str(setup.id),
                "user_id": str(user_id),
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
                    for c in setup.children
                ],
            }

        except SQLAlchemyError as db_err:
            logger.error(f"[DB ERROR] creating profile setup for user {user_id}: {db_err}")
            session.rollback()
            raise

        except Exception as e:
            logger.error(f"[UNEXPECTED ERROR] creating profile setup for user {user_id}: {e}")
            session.rollback()
            raise