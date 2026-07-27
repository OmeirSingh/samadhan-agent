"""Database model for a citizen grievance / case."""
import datetime as dt
from sqlalchemy import Column, Integer, String, Text, DateTime
from .database import Base


class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)
    # Public-facing tracking id, e.g. SAM-2026-0001
    tracking_id = Column(String, unique=True, index=True)

    # Raw citizen input
    citizen_name = Column(String, default="Anonymous")
    citizen_contact = Column(String, default="")
    channel = Column(String, default="web")          # web | voice | image | letter
    raw_text = Column(Text, default="")              # transcribed / OCR'd / typed text
    attachment_note = Column(String, default="")     # description of any uploaded file

    # AI-extracted / agent output
    summary = Column(Text, default="")
    category = Column(String, default="General")
    department = Column(String, default="General Administration")
    priority = Column(String, default="Medium")      # Critical | High | Medium | Low
    sentiment = Column(String, default="Neutral")
    location = Column(String, default="")
    policy_basis = Column(Text, default="")          # RAG-grounded policy citation
    suggested_action = Column(Text, default="")
    ai_mode = Column(String, default="rule-based")   # llm | rule-based

    # Workflow
    status = Column(String, default="Submitted")     # Submitted | Routed | In Progress | Resolved | Rejected
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
