"""
Pydantic schemas for request/response validation.
Covers both the WhatsApp webhook and the counselor dashboard API.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


# ── Webhook / Internal Schemas ───────────────────────────────────────

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


class WebhookVerification(BaseModel):
    """Query params from Meta's GET verification request."""
    hub_mode: str
    hub_verify_token: str
    hub_challenge: str


# ── Dashboard API Schemas ─────────────────────────────────────────────

class DashboardStudentCreate(BaseModel):
    """Payload for manually creating a student from the dashboard."""
    name: str
    phone: str
    course_interest: Optional[str] = None
    lead_status: str = "new"
    lead_score: Optional[float] = 0.0


class DashboardStudentUpdate(BaseModel):
    """Partial update for student fields from the dashboard."""
    name: Optional[str] = None
    phone: Optional[str] = None
    course_interest: Optional[str] = None
    lead_status: Optional[str] = None
    lead_score: Optional[float] = None


class StatusUpdate(BaseModel):
    lead_status: str


class StudentSummary(BaseModel):
    id: int
    name: Optional[str]
    phone: str
    course_interest: Optional[str]
    lead_score: float
    is_hot_lead: bool
    lead_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionPair(BaseModel):
    """A paired inbound+outbound interaction for the chat transcript view."""
    id: int
    student_id: int
    message: Optional[str]   # inbound message_body
    response: Optional[str]  # outbound message_body
    timestamp: datetime


class NoteCreate(BaseModel):
    content: str
    counselor_name: str


class NoteResponse(BaseModel):
    id: int
    student_id: int
    content: str
    counselor_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentDetail(StudentSummary):
    interactions: List[InteractionPair] = []
    notes: List[NoteResponse] = []


class StatsResponse(BaseModel):
    total_leads: int
    hot_leads: int
    admitted: int
    avg_score: float
    status_breakdown: Dict[str, int]
    course_breakdown: Dict[str, int]


# ── Campaign Schemas ──────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    message: str
    recipient_group: str  # all / interested / high_cet


class CampaignResponse(BaseModel):
    id: int
    message: str
    recipient_group: str
    recipient_count: int
    sent_at: datetime

    class Config:
        from_attributes = True


# ── Bulk Import ───────────────────────────────────────────────────────

class BulkStudentItem(BaseModel):
    name: str
    phone: str
    course_interest: Optional[str] = None
    lead_status: str = "new"
    lead_score: Optional[float] = 0.0


class BulkStudentCreate(BaseModel):
    students: List[BulkStudentItem]
