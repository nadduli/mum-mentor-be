from sqlalchemy import Column, String, Integer, DateTime, func, UUID

import uuid

from api.db.base_model import BaseModel

class Posts(BaseModel):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    views = Column(Integer, default=0)