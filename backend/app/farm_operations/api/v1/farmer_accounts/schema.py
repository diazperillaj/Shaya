from typing import Optional

from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from app.api.api_v1.farmers.schema import FarmerCreate

Username = Annotated[str, StringConstraints(min_length=4, max_length=255)]
Password = Annotated[str, StringConstraints(min_length=6)]


class FarmerAccountCreate(BaseModel):
    """Da acceso a un caficultor ya registrado."""

    farmer_id: int = Field(..., gt=0)
    username: Username
    password: Password


class FarmerAccountCreateFull(FarmerCreate):
    """Registra un caficultor nuevo (persona y caficultor) con su cuenta, en una sola operación."""

    username: Username
    password: Password


class FarmerAccountResponse(BaseModel):
    """Caficultor y el estado de su acceso al sistema."""

    farmer_id: int
    full_name: str
    document: Optional[str]
    phone: Optional[str]
    farms: int
    user_id: Optional[int]
    username: Optional[str]
    account_role: Optional[str] = Field(
        None, description="`farmer`, o el rol de personal si la persona ya trabaja en Shaya"
    )
