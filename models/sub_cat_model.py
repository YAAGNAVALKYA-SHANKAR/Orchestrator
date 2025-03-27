from pydantic import BaseModel, Field
from enum import Enum

class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class SubCategoryBase(BaseModel):
    sub_category_name: str = Field(...)
    sub_category_type: str = Field(...)
    sub_category_desc: str = Field(...)
    sub_category_status: StatusEnum = StatusEnum.INACTIVE 