"""
Dashboard API router — exposes REST endpoints consumed by the React counselor dashboard.

Endpoints:
  GET  /api/stats
  GET  /api/students
  GET  /api/students/export
  GET  /api/students/{id}
  POST /api/students
  POST /api/students/bulk
  PUT  /api/students/{id}
  DELETE /api/students/{id}
  PUT  /api/students/{id}/status
  POST /api/students/{id}/notes
  GET  /api/campaigns
  POST /api/campaigns
"""

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student, Interaction, LeadNote, User, Campaign
from app.schemas import (
    DashboardStudentCreate,
    DashboardStudentUpdate,
    StatusUpdate,
    StudentSummary,
    StudentDetail,
    InteractionPair,
    NoteCreate,
    NoteResponse,
    StatsResponse,
    CampaignCreate,
    CampaignResponse,
    BulkStudentCreate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["dashboard"])


# ── Helpers ───────────────────────────────────────────────────────────

def _get_or_create_system_user(db: Session) -> User:
    """Return the system counselor user, creating it on first call."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            name="Counselor",
            email="counselor@sanmati.edu",
            hashed_password="",
            role="faculty",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _pair_interactions(interactions: list) -> list[InteractionPair]:
    """
    Convert a flat list of Interaction ORM objects (alternating inbound/outbound)
    into paired InteractionPair objects for the chat transcript view.
    Each inbound message is paired with the immediately following outbound reply.
    Unpaired messages are included with None for the missing side.
    """
    pairs: list[InteractionPair] = []
    inbound_queue: list = []

    sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)

    for msg in sorted_interactions:
        if msg.message_direction == "inbound":
            inbound_queue.append(msg)
        elif msg.message_direction == "outbound":
            if inbound_queue:
                inb = inbound_queue.pop(0)
                pairs.append(InteractionPair(
                    id=inb.id,
                    student_id=inb.student_id,
                    message=inb.message_body,
                    response=msg.message_body,
                    timestamp=inb.timestamp,
                ))
            else:
                # Outbound with no prior inbound (e.g. broadcast)
                pairs.append(InteractionPair(
                    id=msg.id,
                    student_id=msg.student_id,
                    message=None,
                    response=msg.message_body,
                    timestamp=msg.timestamp,
                ))

    # Flush remaining unpaired inbound messages
    for inb in inbound_queue:
        pairs.append(InteractionPair(
            id=inb.id,
            student_id=inb.student_id,
            message=inb.message_body,
            response=None,
            timestamp=inb.timestamp,
        ))

    return pairs


def _note_to_response(note: LeadNote, db: Session) -> NoteResponse:
    """Convert a LeadNote ORM object to a NoteResponse schema."""
    author_name = "Counselor"
    # Extract counselor name from prefixed note text (e.g. "[Dr. Patil] Some note")
    content = note.note_text
    if content.startswith("[") and "] " in content:
        bracket_end = content.index("] ")
        author_name = content[1:bracket_end]
        content = content[bracket_end + 2:]
    return NoteResponse(
        id=note.id,
        student_id=note.student_id,
        content=content,
        counselor_name=author_name,
        created_at=note.created_at,
    )


def _student_to_summary(s: Student) -> StudentSummary:
    return StudentSummary(
        id=s.id,
        name=s.name,
        phone=s.phone,
        course_interest=s.course_interest,
        lead_score=float(s.lead_score or 0),
        is_hot_lead=bool(s.is_hot_lead),
        lead_status=s.lead_status or "new",
        created_at=s.created_at,
    )


# ── GET /api/stats ────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Return dashboard statistics: totals, hot leads, admissions, avg score."""
    total = db.query(func.count(Student.id)).scalar() or 0
    hot = db.query(func.count(Student.id)).filter(Student.is_hot_lead == True).scalar() or 0
    admitted = db.query(func.count(Student.id)).filter(Student.lead_status == "admitted").scalar() or 0
    avg_raw = db.query(func.avg(Student.lead_score)).scalar()
    avg_score = round(float(avg_raw) * 10, 1) if avg_raw else 0.0  # scale 0-10 → 0-100

    # Status breakdown
    status_rows = (
        db.query(Student.lead_status, func.count(Student.id))
        .group_by(Student.lead_status)
        .all()
    )
    status_breakdown = {row[0] or "new": row[1] for row in status_rows}

    # Course breakdown
    course_rows = (
        db.query(Student.course_interest, func.count(Student.id))
        .filter(Student.course_interest != None)
        .group_by(Student.course_interest)
        .all()
    )
    course_breakdown = {row[0]: row[1] for row in course_rows}

    return StatsResponse(
        total_leads=total,
        hot_leads=hot,
        admitted=admitted,
        avg_score=avg_score,
        status_breakdown=status_breakdown,
        course_breakdown=course_breakdown,
    )


# ── GET /api/students/export ─────────────────────────────────────────
# NOTE: Must be defined BEFORE /api/students/{id} to avoid routing conflict

@router.get("/students/export")
def export_students_csv(db: Session = Depends(get_db)):
    """Stream all students as a CSV file download."""
    students = db.query(Student).order_by(Student.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Phone", "Course Interest", "Lead Score", "Hot Lead", "Status", "Source", "Created At"])
    for s in students:
        writer.writerow([
            s.id, s.name or "", s.phone, s.course_interest or "",
            s.lead_score or 0, "Yes" if s.is_hot_lead else "No",
            s.lead_status or "new", s.source or "whatsapp",
            s.created_at.isoformat() if s.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"},
    )


# ── GET /api/students ─────────────────────────────────────────────────

@router.get("/students", response_model=list[StudentSummary])
def get_students(
    status: Optional[str] = Query(None),
    course: Optional[str] = Query(None),
    is_hot_lead: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return a paginated, filtered list of students."""
    q = db.query(Student)

    if status:
        q = q.filter(Student.lead_status == status)
    if course:
        q = q.filter(Student.course_interest.ilike(f"%{course}%"))
    if is_hot_lead is not None:
        q = q.filter(Student.is_hot_lead == is_hot_lead)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (Student.name.ilike(pattern)) | (Student.phone.ilike(pattern))
        )

    offset = (page - 1) * limit
    students = q.order_by(Student.created_at.desc()).offset(offset).limit(limit).all()
    return [_student_to_summary(s) for s in students]


# ── GET /api/students/{id} ────────────────────────────────────────────

@router.get("/students/{student_id}", response_model=StudentDetail)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Return full student detail including interaction transcript and notes."""
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    pairs = _pair_interactions(s.interactions)
    notes = [_note_to_response(n, db) for n in s.notes]

    return StudentDetail(
        **_student_to_summary(s).model_dump(),
        interactions=pairs,
        notes=notes,
    )


# ── POST /api/students ────────────────────────────────────────────────

@router.post("/students", response_model=StudentSummary, status_code=201)
def create_student(payload: DashboardStudentCreate, db: Session = Depends(get_db)):
    """Manually create a student record from the dashboard."""
    existing = db.query(Student).filter(Student.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="A student with this phone number already exists")

    now = datetime.now(timezone.utc)
    s = Student(
        name=payload.name,
        phone=payload.phone,
        course_interest=payload.course_interest,
        lead_status=payload.lead_status,
        lead_score=int((payload.lead_score or 0) / 10),  # store 0-10 internally
        source="walk_in",
        first_contact=now,
        last_active=now,
        created_at=now,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    logger.info("Dashboard: created student id=%d phone=%s", s.id, s.phone)
    return _student_to_summary(s)


# ── POST /api/students/bulk ───────────────────────────────────────────

@router.post("/students/bulk", status_code=201)
def bulk_create_students(payload: BulkStudentCreate, db: Session = Depends(get_db)):
    """Bulk-import students (CSV/Excel upload processed client-side)."""
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0

    for item in payload.students:
        existing = db.query(Student).filter(Student.phone == item.phone).first()
        if existing:
            skipped += 1
            continue
        s = Student(
            name=item.name,
            phone=item.phone,
            course_interest=item.course_interest,
            lead_status=item.lead_status,
            lead_score=int((item.lead_score or 0) / 10),
            source="walk_in",
            first_contact=now,
            last_active=now,
            created_at=now,
        )
        db.add(s)
        created += 1

    db.commit()
    logger.info("Bulk import: created=%d, skipped=%d", created, skipped)
    return {"created": created, "skipped": skipped}


# ── PUT /api/students/{id} ────────────────────────────────────────────

@router.put("/students/{student_id}", response_model=StudentSummary)
def update_student(student_id: int, payload: DashboardStudentUpdate, db: Session = Depends(get_db)):
    """Edit student details."""
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.name is not None:
        s.name = payload.name
    if payload.phone is not None:
        s.phone = payload.phone
    if payload.course_interest is not None:
        s.course_interest = payload.course_interest
    if payload.lead_status is not None:
        s.lead_status = payload.lead_status
    if payload.lead_score is not None:
        s.lead_score = int(payload.lead_score / 10)

    db.commit()
    db.refresh(s)
    return _student_to_summary(s)


# ── DELETE /api/students/{id} ─────────────────────────────────────────

@router.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student and all associated interactions and notes."""
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    db.query(Interaction).filter(Interaction.student_id == student_id).delete()
    db.query(LeadNote).filter(LeadNote.student_id == student_id).delete()
    db.delete(s)
    db.commit()
    return {"message": "Student deleted"}


# ── PUT /api/students/{id}/status ────────────────────────────────────

@router.put("/students/{student_id}/status")
def update_status(student_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Update a student's lead status."""
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    valid_statuses = {"new", "in_progress", "visit_scheduled", "admitted", "not_interested"}
    if payload.lead_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}")

    s.lead_status = payload.lead_status
    db.commit()
    return {"message": "Status updated"}


# ── POST /api/students/{id}/notes ─────────────────────────────────────

@router.post("/students/{student_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(student_id: int, payload: NoteCreate, db: Session = Depends(get_db)):
    """Add a counselor note to a student."""
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    # Ensure system user exists (id=1)
    system_user = _get_or_create_system_user(db)

    # Prefix counselor name into note text for storage
    prefixed_text = f"[{payload.counselor_name}] {payload.content}"

    note = LeadNote(
        student_id=student_id,
        user_id=system_user.id,
        note_text=prefixed_text,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return NoteResponse(
        id=note.id,
        student_id=note.student_id,
        content=payload.content,
        counselor_name=payload.counselor_name,
        created_at=note.created_at,
    )


# ── GET /api/campaigns ────────────────────────────────────────────────

@router.get("/campaigns", response_model=list[CampaignResponse])
def get_campaigns(db: Session = Depends(get_db)):
    """Return campaign history."""
    campaigns = db.query(Campaign).order_by(Campaign.sent_at.desc()).all()
    return campaigns


# ── POST /api/campaigns ───────────────────────────────────────────────

@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    """Record a WhatsApp campaign and compute recipient count."""
    # Determine recipient count from DB
    q = db.query(func.count(Student.id))
    if payload.recipient_group == "interested":
        q = q.filter(Student.lead_status.in_(["in_progress", "visit_scheduled"]))
    elif payload.recipient_group == "high_cet":
        q = q.filter(Student.lead_score >= 8)  # 8/10 ≈ 80% = high score
    # "all" → no additional filter

    count = q.scalar() or 0

    campaign = Campaign(
        message=payload.message,
        recipient_group=payload.recipient_group,
        recipient_count=count,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    logger.info("Campaign created: id=%d, group=%s, recipients=%d", campaign.id, payload.recipient_group, count)
    return campaign
