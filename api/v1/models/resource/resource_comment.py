from sqlalchemy import Column, String, UUID
from api.db.base_model import BaseModel
import uuid

class ResourceComment(BaseModel):
    __tablename__ = "resource_comment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    comment = Column(String, nullable=False)