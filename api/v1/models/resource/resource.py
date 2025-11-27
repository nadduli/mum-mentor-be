from sqlalchemy import Column, String, UUID, ForeignKey
from sqlalchemy.orm import relationship
from api.db.base_model import BaseModel
import uuid



class Resource(BaseModel):
    __tablename__ = "resource"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("resource_categories.id"), nullable=False)
    content = Column(String, nullable=False)
    
    category = relationship("ResourceCategory", back_populates="resources")