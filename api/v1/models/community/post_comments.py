from sqlalchemy import Column, String, UUID
from api.db.base_model import BaseModel
import uuid

class PostComments(BaseModel):
    __tablename__ = "post_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    comment_id = Column(UUID(as_uuid=True), nullable=True)
    comment = Column(String, nullable=False)