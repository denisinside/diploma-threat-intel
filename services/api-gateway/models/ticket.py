from pydantic import Field
from typing import Optional
from datetime import datetime
from models.enums import TicketStatus, Severity
from models.DBModel import DBModel

class CompanyVulnTicket(DBModel):
    """
    Management Window.
    Tracks the status of a specific CVE for a specific Company.
    """
    company_id: str = Field(...)
    asset_id: str = Field(...)
    vulnerability_id: str = Field(...)
    
    status: TicketStatus = TicketStatus.OPEN
    priority: Severity = Severity.MEDIUM
    
    notes: Optional[str] = None
    assigned_user_id: Optional[str] = None

    detected_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    resolved_at: Optional[datetime] = None

class AuditLog(DBModel):
    """
    Immutable log of actions. Who did what and when.
    """
    company_id: str = Field(...)
    user_id: str = Field(...)
    
    action: str = Field(..., description="e.g. 'vuln_status_update', 'settings_change'")
    
    target_entity: str = Field(...) 
    target_entity_id: str = Field(...)
    
    changes: dict = Field(default_factory=dict, description="{'old_status': 'open', 'new_status': 'ignored'}")
    
    ip_address: Optional[str] = None