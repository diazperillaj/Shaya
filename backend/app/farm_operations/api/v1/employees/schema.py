from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    document: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    observations: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    farm_id: int = Field(..., gt=0)


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeResponse(BaseModel):
    id: int
    farm_id: int
    full_name: str
    document: Optional[str]
    phone: Optional[str]
    active: bool
    observations: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
