from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, List
from datetime import date
from enum import Enum


class MomStatusEnum(str, Enum):
    pregnant = "pregnant"
    new_mom = "new_mom"
    toddler_mom = "toddler_mom"
    mixed = "mixed"


class ChildInput(BaseModel):
    full_name: str
    date_of_birth: Optional[date] = None
    due_date: Optional[date] = None
    gender: Optional[str] = None


class PartnerInput(BaseModel):
    name: str
    email: EmailStr


class ProfileSetupSubmit(BaseModel):
    mom_status: MomStatusEnum
    goals: list[str]
    partner: Optional[PartnerInput] = None
    children: list[ChildInput] = []


class ProfileSetupResponse(BaseModel):
    user_id: str
    mom_status: MomStatusEnum
    goals: List[str]
    partner: Optional[dict]

    children: List[dict]
    children_metadata: List[dict]


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
            "example": {"mom_status": "new_mom", "goals": ["Sleep", "Mental Wellness"]}
        }
    }
