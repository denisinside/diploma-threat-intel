from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic response for operations that don't return an entity"""
    message: str
    success: bool = True
