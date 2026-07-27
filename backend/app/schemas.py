"""Pydantic request/response schemas."""
import datetime as dt
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class GrievanceCreate(BaseModel):
    citizen_name: Optional[str] = "Anonymous"
    citizen_contact: Optional[str] = ""
    channel: Optional[str] = "web"
    raw_text: str = Field(..., min_length=5)
    attachment_note: Optional[str] = ""
    # Location is now mandatory so cases can be routed and mapped to a ward.
    location: str = Field(..., min_length=2, description="Required: area / ward / landmark")


class StatusUpdate(BaseModel):
    status: str


class OfficialLogin(BaseModel):
    password: str


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

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, value: dt.datetime) -> str:
        # Treat any stored naive datetime as UTC, then emit an ISO string with a
        # 'Z' so the browser can convert it to the viewer's timezone (IST) reliably.
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    class Config:
        from_attributes = True
