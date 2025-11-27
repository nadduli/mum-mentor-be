from sqlalchemy import Column, String, UUID
from api.db.base_model import BaseModel
import uuid

class JournalPhotos(BaseModel):
    __tablename__ = "journal_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), nullable=False)
    url = Column(String, nullable=False)