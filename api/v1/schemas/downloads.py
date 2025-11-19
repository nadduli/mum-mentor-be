from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

class DownloadTrackRequest(BaseModel):
    download_type: str
    resource_id: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    source: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None

    @field_validator("download_type")
    @classmethod
    def validate_download_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("download_type is required")
        return v.strip().lower()

class DownloadTrackResponse(BaseModel):
    id: uuid.UUID
    download_type: str
    occurred_at: datetime

    model_config = {"from_attributes": True}
