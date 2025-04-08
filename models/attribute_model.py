from pydantic import BaseModel,Field
from typing import Optional
class AttributeBase(BaseModel):
    attribute_name:str=Field(...,min_length=1)
    attribute_desc:Optional[str]=Field(None)
    attribute_data_type:str=Field(...)
    attribute_default_value:Optional[str]=Field(None)
    attribute_value_constraints:Optional[dict]=Field(None)
    attribute_is_mandatory:bool=Field(False)
    attribute_is_editable:bool=Field(True)
    attribute_is_searchable:bool=Field(False)