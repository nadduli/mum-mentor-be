from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from api.v1.models.journal.journal import Journal
from api.v1.models.journal.journal_photos import JournalPhoto
from api.v1.schemas.journal import JournalEdit
from api.utils.logger import logger

class JournalService:
    
    @staticmethod
    def update_journal(session: Session, journal_id: uuid.UUID, user_id: uuid.UUID, payload: JournalEdit):
        logger.info(f"User {user_id} attempting to edit journal {journal_id}")

        journal = session.query(Journal).filter(
            Journal.id == journal_id, 
            Journal.user_id == user_id
        ).first()

        if not journal:
            logger.warning(f"Journal {journal_id} not found or unauthorized for user {user_id}")
            raise HTTPException(status_code=404, detail="Journal entry not found")

        update_data = payload.model_dump(exclude_unset=True)
        
        for field in ["title", "content", "mood", "entry_date", "category_id"]:
            if field in update_data and update_data[field] is not None:
                setattr(journal, field, update_data[field])

        if "photo_urls" in update_data and update_data["photo_urls"] is not None:
            session.query(JournalPhoto).filter(JournalPhoto.journal_id == journal.id).delete()
            
            for url in update_data["photo_urls"]:
                new_photo = JournalPhoto(journal_id=journal.id, url=url)
                session.add(new_photo)

        try:
            session.commit()
            session.refresh(journal)
            logger.info(f"Journal {journal_id} successfully updated")
            return journal
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating journal {journal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while updating the journal")