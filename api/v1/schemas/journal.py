from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class JournalEdit(BaseModel):
    title: Optional[str] = None
    entry_date: Optional[datetime] = None
    category: Optional[str] = None
    mood: Optional[str] = None
    photos: Optional[List[str]] = None
    content: Optional[str] = None

class JournalData(BaseModel):
    id: uuid.UUID
    title: str

class JournalResponse(BaseModel):
    status: str
    message: str
    data: JournalData