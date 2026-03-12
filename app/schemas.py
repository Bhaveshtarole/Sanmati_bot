"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Student Schemas ──────────────────────────────────────────────────

class StudentBase(BaseModel):
    name: Optional[str] = None
    phone: str
    exam_type: Optional[str] = None
    language: str = "en"


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    is_hot_lead: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Interaction Schemas ──────────────────────────────────────────────

class InteractionBase(BaseModel):
    message_direction: str
    message_body: Optional[str] = None
    message_type: str = "text"


class InteractionCreate(InteractionBase):
    student_id: int


class InteractionResponse(InteractionBase):
    id: int
    student_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Webhook Schemas ──────────────────────────────────────────────────

class WebhookVerification(BaseModel):
    """Query params from Meta's GET verification request."""
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str
