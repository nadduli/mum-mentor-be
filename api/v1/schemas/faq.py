from pydantic import BaseModel
from typing import Any
import uuid
from datetime import datetime

class FAQResponse(BaseModel):
    id: uuid.UUID
    category: str
    question: str
    answer: str
    keywords: Any
    view_count: int
    helpful_count: int
    order_index: int
    created_at: datetime

    class Config:
        orm_mode = True

class FAQListResponse(BaseModel):
    data: list[FAQResponse]
    meta: dict