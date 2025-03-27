from pydantic import BaseModel, Field
from typing import Optional

class AttributeBase(BaseModel):
    attribute_name: str = Field(..., description="Name of the attribute", min_length=1)
    attribute_description: Optional[str] = Field(None, description="Description of the attribute")
    attribute_data_type: str = Field(..., description="Type of data (e.g., string, integer, boolean)")
    attribute_default_value: Optional[str] = Field(None, description="Default value for the attribute")
    attribute_value_constraints: Optional[dict] = Field(None, description="Min and max value constraints, if applicable")
    attribute_is_mandatory: bool = Field(False, description="Whether this attribute is mandatory when used in an entity")
    attribute_is_editable: bool = Field(True, description="Whether this attribute can be edited after creation")
    attribute_is_searchable: bool = Field(False, description="Whether this attribute is searchable in entities")