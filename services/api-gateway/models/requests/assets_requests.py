from pydantic import BaseModel, Field
from typing import Optional
from models.enums import AssetType


class CreateAssetRequest(BaseModel):
    company_id: str
    name: str = Field(..., min_length=1, max_length=200, description="Asset name, e.g. 'nginx' or 'sub.domain.com'")
    version: Optional[str] = None
    type: AssetType
    source_file: Optional[str] = None


class UpdateAssetRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    version: Optional[str] = None
    type: Optional[AssetType] = None
    is_active: Optional[bool] = None
    source_file: Optional[str] = None
