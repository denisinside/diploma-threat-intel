from pydantic import BaseModel, Field
from typing import Optional
from models.enums import SubscriptionType, Severity, ChannelType


class CreateSubscriptionRequest(BaseModel):
    company_id: str
    sub_type: SubscriptionType
    keyword: str = Field(..., min_length=2)
    min_severity: Severity = Severity.LOW


class UpdateSubscriptionRequest(BaseModel):
    keyword: Optional[str] = Field(None, min_length=2)
    min_severity: Optional[Severity] = None


class CreateChannelRequest(BaseModel):
    company_id: str
    name: str = Field(..., min_length=1, max_length=200, description="Friendly name, e.g. 'Security Team Slack'")
    channel_type: ChannelType
    config: dict = Field(default_factory=dict)


class UpdateChannelRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    channel_type: Optional[ChannelType] = None
    config: Optional[dict] = None
    is_enabled: Optional[bool] = None
