from pydantic import BaseModel,Field
from enum import Enum
class StatusEnum(str,Enum):
    ACTIVE="ACTIVE"
    INACTIVE="INACTIVE"
class CategoryBase(BaseModel):
    category_name:str=Field(...)
    category_type:str=Field(...)
    category_desc:str=Field(...)
    category_status:StatusEnum=StatusEnum.INACTIVE 