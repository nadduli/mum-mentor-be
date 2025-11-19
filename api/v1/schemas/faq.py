from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class FAQListResponse(BaseModel):
    data: list[FAQResponse]
    meta: dict