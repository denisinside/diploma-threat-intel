from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Annotated
from datetime import datetime

PyObjectId = Annotated[str, Field(alias="_id", default=None)]

class DBModel(BaseModel):
    """Base model for all mongo database entities"""
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )