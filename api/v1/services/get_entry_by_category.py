import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from api.v1.models.journal import Journal, JournalCategory

def get_entries_by_category(db: Session, category_title: str, user_id: uuid.UUID):
    """
    Get journal entries by category title for a specific user.
    """
    stmt = select(Journal).join(JournalCategory).where(
        JournalCategory.name.ilike(f"%{category_title}%"),
        Journal.user_id == user_id
    ).order_by(Journal.created_at.desc())
    
    result = db.execute(stmt)
    return result.scalars().all()
