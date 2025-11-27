from sqlalchemy import Column, UUID
from api.db.base_model import BaseModel
import uuid

class PostLikes(BaseModel):
    __tablename__ = "post_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    comment_id = Column(UUID(as_uuid=True), nullable=True)