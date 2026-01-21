from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated

Username = Annotated[
    str,
    StringConstraints(min_length=4)
]

Password = Annotated[
    str,
    StringConstraints(min_length=6)
]

class LoginSchema(BaseModel):
    username: Username
    password: Password


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True
