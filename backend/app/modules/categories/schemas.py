from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime


class ResponseBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str
    type: Literal["income", "expense"]
    icon: str
    color: str | None = None


class CategoryResponse(ResponseBase):
    id: str
    name: str
    type: str
    icon: str
    color: str | None = None
    created_at: datetime
