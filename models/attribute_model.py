from pydantic import BaseModel, Field
from typing import Optional

class AttributeBase(BaseModel):
    name: str = Field(..., description="Name of the attribute", min_length=1)
    description: Optional[str] = Field(None, description="Description of the attribute")
    data_type: str = Field(..., description="Type of data (e.g., string, integer, boolean)")
    default_value: Optional[str] = Field(None, description="Default value for the attribute")
    value_constraints: Optional[dict] = Field(None, description="Min and max value constraints, if applicable")
    is_mandatory: bool = Field(False, description="Whether this attribute is mandatory when used in an entity")
    is_editable: bool = Field(True, description="Whether this attribute can be edited after creation")
    is_searchable: bool = Field(False, description="Whether this attribute is searchable in entities")