from pydantic import BaseModel, Field
from typing import Optional
from models.enums import TicketStatus, Severity


class CreateTicketRequest(BaseModel):
    company_id: str
    asset_id: str
    vulnerability_id: str
    priority: Severity = Severity.MEDIUM
    notes: Optional[str] = None
    assigned_user_id: Optional[str] = None


class UpdateTicketRequest(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[Severity] = None
    notes: Optional[str] = None
    assigned_user_id: Optional[str] = None
