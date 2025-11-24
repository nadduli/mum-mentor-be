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