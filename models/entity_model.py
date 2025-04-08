from enum import Enum
from pydantic import BaseModel,Field
from typing import Optional,List
class StatusEnum(str,Enum):
    ACTIVE="ACTIVE"
    INACTIVE="INACTIVE"
class EntityBase(BaseModel):
    entity_name:str=Field(...,min_length=1)
    entity_desc:Optional[str]=Field(None)
    entity_status:StatusEnum = StatusEnum.INACTIVE
    entity_category:str=Field(...)
    entity_subcategory:str=Field(...)
    entity_attributes:List[str]=Field(...) 