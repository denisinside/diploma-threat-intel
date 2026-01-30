from models.DBModel import DBModel
from models.enums import AssetType
from typing import Optional
from pydantic import Field

class Asset(DBModel):
    """
    Specific technology or infrastructure piece owned by the company.
    Used to match against new vulnerabilities.
    """
    company_id: str = Field(...)
    name: str = Field(..., description="Name of asset, e.g., 'nginx' or 'sub.domain.com'")
    version: Optional[str] = Field(None, description="Specific version, e.g., '1.18.0'")
    type: AssetType
    is_active: bool = True
    
    # Metadata for BOM files
    source_file: Optional[str] = None