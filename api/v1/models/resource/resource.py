from sqlalchemy import Column, String, UUID
from api.db.base_model import BaseModel
import uuid



class Resource(BaseModel):
    __tablename__ = "resource"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(UUID(as_uuid=True), nullable=False)