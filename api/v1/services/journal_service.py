from typing import Optional
import uuid
from sqlalchemy.orm import Session
from api.v1.models.journal.journal import Journal
from api.v1.models.journal.journal_photos import JournalPhoto
from api.v1.models.journal.journal_category import JournalCategory
from api.v1.schemas.journal import JournalCreateRequest
from api.utils.logger import logger

class JournalService:
    """Service class for journal-related operations"""

    @staticmethod
    def create_journal(db: Session, journal_data: JournalCreateRequest, user_id: str) -> Optional[Journal]:
        """
        Create a new journal entry
        
        Args:
            db: Database session
            journal_data: Journal creation data
            user_id: ID of the user creating the journal
            
        Returns:
            Created Journal object or None if failed
        """
        try:
            # Handle Category
            category_id = None
            if journal_data.category:
                # Check if category exists

                existing_category = db.query(JournalCategory).filter(JournalCategory.name == journal_data.category).first()
                
                if existing_category:
                    category_id = existing_category.id
                else:
                    new_category = JournalCategory(name=journal_data.category)
                    new_category.add(db)
                    db.flush()
                    category_id = new_category.id

            new_journal = Journal(
                user_id=uuid.UUID(user_id),
                title=journal_data.title,
                content=journal_data.thoughts,
                category_id=category_id,
                mood=journal_data.mood,
                entry_date=journal_data.date
            )
            
            new_journal.add(db)
            db.flush() 
            
            # Save photos if any
            if journal_data.photos:
                for photo_url in journal_data.photos:
                    new_photo = JournalPhoto(
                        journal_id=new_journal.id,
                        url=photo_url
                    )
                    new_photo.add(db)
            
            db.commit()
            db.refresh(new_journal)
            
            logger.info(f"Journal created successfully for user_id={user_id}")
            return new_journal
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating journal for user_id={user_id}: {str(e)}", exc_info=True)
            return None
