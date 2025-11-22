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


class ChildCreate(BaseModel):
    full_name: str
    date_of_birth: Optional[date] = None
    due_date: Optional[date] = None
    gender: Optional[str] = None



class PartnerInput(BaseModel):
    name: str
    email: EmailStr


class ProfileSetupSubmit(BaseModel):
    mom_status: MomStatusEnum
    goals: List[str]

    partner: Optional[PartnerInput] = None
    children: List[ChildCreate] = Field(default_factory=list)



class ProfileSetupResponse(BaseModel):
    user_id: str
    mom_status: MomStatusEnum
    goals: List[str]
    partner: Optional[dict]

    children: List[dict]
    children_metadata: List[dict]
