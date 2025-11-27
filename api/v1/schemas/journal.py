from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class JournalEdit(BaseModel):
    title: Optional[str] = None
    entry_date: Optional[datetime] = None
    mood: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    photo_urls: Optional[List[str]] = None 

class JournalResponseData(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    mood: Optional[str]
    entry_date: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    category_id: Optional[uuid.UUID]
    
    class Config:
        from_attributes = True

class JournalResponse(BaseModel):
    status: str
    message: str
    data: JournalResponseData