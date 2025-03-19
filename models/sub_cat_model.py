from pydantic import BaseModel, Field
from enum import Enum

class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class SubCategoryBase(BaseModel):
    name: str = Field(...)
    type: str = Field(...)
    desc: str = Field(...)
    status: StatusEnum = StatusEnum.INACTIVE 