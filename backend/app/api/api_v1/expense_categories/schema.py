from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ExpenseCategoryUpdate(ExpenseCategoryCreate):
    pass


class ExpenseCategoryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
