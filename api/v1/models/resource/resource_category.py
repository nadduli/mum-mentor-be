from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.db.base_model import BaseModel
import uuid

class ResourceCategory(BaseModel):
    __tablename__ = "resource_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    
    resources = relationship("Resource", back_populates="category")