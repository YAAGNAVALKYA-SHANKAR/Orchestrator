from pydantic import BaseModel,Field
from enum import Enum
from typing import Optional
class StatusEnum(str,Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
class SubCategoryBase(BaseModel):
    sub_category_name:str=Field(...)
    sub_category_type:str=Field(...)
    sub_category_category:Optional[str]=Field(None)
    sub_category_desc:str=Field(...)
    sub_category_status:StatusEnum=StatusEnum.INACTIVE