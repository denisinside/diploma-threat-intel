from models.DBModel import DBModel
from models.enums import SubscriptionType, Severity, ChannelType, TicketStatus
from typing import Optional
from pydantic import Field
from datetime import datetime

class Subscription(DBModel):
    """
    Rule for what the company wants to monitor.
    """
    company_id: str = Field(...)
    sub_type: SubscriptionType
    
    # For Vulns: "nginx", "python", "ecosystem:npm"
    # For Leaks: "company.com", "internal-project-name"
    keyword: str = Field(..., min_length=2)
    
    # Only notify if severity is higher than X (for Vulns)
    min_severity: Severity = Severity.LOW

class NotificationChannel(DBModel):
    """
    Destinations for alerts.
    """
    company_id: str = Field(...)
    name: str = Field(..., description="Friendly name, e.g. 'Security Team Slack'")
    channel_type: ChannelType
    
    # Configuration depends on type (webhook_url, chat_id, email_address)
    config: dict = Field(default_factory=dict) 
    is_enabled: bool = True