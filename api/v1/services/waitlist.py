from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.v1.models.user.user import Waitlist
from api.v1.schemas.waitlist import WaitlistCreate
from datetime import datetime, timezone
import uuid


def create_waitlist_entry(db: Session, data: WaitlistCreate):
    existing = db.query(Waitlist).filter(
        Waitlist.email == data.email.lower()
    ).first()

    if existing:
        return None, existing

    new_entry = Waitlist(
        full_name=data.full_name,
        email=data.email.lower(),
        # referral_source=data.source,
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


def delete_waitlist_entry(db: Session, waitlist_id: str):
    """
    Delete a waitlist entry by ID.
    
    Args:
        db: Database session
        waitlist_id: UUID string of the waitlist entry to delete
        
    Returns:
        Tuple (deleted_entry, error_message):
            - If successful: (waitlist_entry_object, None)
            - If not found: (None, "Waitlist entry not found")
    """
    try:
        # Convert string to UUID
        entry_id = uuid.UUID(waitlist_id)
    except (ValueError, AttributeError):
        return None, "Invalid waitlist ID format"
    
    entry = db.query(Waitlist).filter(Waitlist.id == entry_id).first()
    
    if not entry:
        return None, "Waitlist entry not found"
    
    try:
        db.delete(entry)
        db.commit()
        return entry, None
    except Exception as e:
        db.rollback()
        return None, f"Failed to delete waitlist entry: {str(e)}"