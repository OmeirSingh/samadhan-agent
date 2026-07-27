"""Pydantic request/response schemas."""
import datetime as dt
from typing import Optional
from pydantic import BaseModel


class GrievanceCreate(BaseModel):
    citizen_name: Optional[str] = "Anonymous"
    citizen_contact: Optional[str] = ""
    channel: Optional[str] = "web"
    raw_text: str
    attachment_note: Optional[str] = ""
    location: Optional[str] = ""


class StatusUpdate(BaseModel):
    status: str


class GrievanceOut(BaseModel):
    id: int
    tracking_id: str
    citizen_name: str
    citizen_contact: str
    channel: str
    raw_text: str
    attachment_note: str
    summary: str
    category: str
    department: str
    priority: str
    sentiment: str
    location: str
    policy_basis: str
    suggested_action: str
    ai_mode: str
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True
