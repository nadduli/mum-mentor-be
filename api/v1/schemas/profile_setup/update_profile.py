from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date
from api.v1.models.enums.enums import MomStatusEnum

class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class ChildUpdate(BaseModel):
    full_name: str
    date_of_birth: Optional[date] = None
    due_date: Optional[date] = None
    gender: Optional[str] = None

class ProfileSetupUpdate(BaseModel):
    """
    Schema for PATCH requests. 
    All fields are optional to allow partial updates.
    """
    mom_status: Optional[MomStatusEnum] = None
    goals: Optional[List[str]] = None
    partner: Optional[PartnerUpdate] = None
    children: Optional[List[ChildUpdate]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "mom_status": "new_mom",
                "goals": ["Sleep", "Mental Wellness"]
            }
        }
    }