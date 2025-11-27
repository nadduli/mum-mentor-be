from sqlalchemy import Column, UUID
from api.db.base_model import BaseModel
import uuid

class ResourceLikes(BaseModel):
    __tablename__ = "resource_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), nullable=False)