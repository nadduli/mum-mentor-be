from sqlalchemy import Column, UUID
from api.db.base_model import BaseModel
import uuid

class SavedForLater(BaseModel):
    __tablename__ = "saved_for_later"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)