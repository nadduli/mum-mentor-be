from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.v1.models.user.user import Waitlist
from api.v1.schemas.waitlist import WaitlistCreate
from datetime import datetime, timezone


def create_waitlist_entry(db: Session, data: WaitlistCreate):
    existing = db.query(Waitlist).filter(
        Waitlist.email == data.email.lower()
    ).first()

    if existing:
        return None, existing

    new_entry = Waitlist(
        full_name=data.full_name,
        email=data.email.lower(),
        referral_source=data.source,
    )

    try:
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry, None
    except IntegrityError:
        db.rollback()
        existing = db.query(Waitlist).filter(
            Waitlist.email == data.email.lower()
        ).first()
        return None, existing