"""
SQLAlchemy ORM models — User, Student, Interaction, LeadNote.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Admin or Faculty user for the dashboard."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="faculty")  # admin / faculty
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assigned_leads = relationship("Student", back_populates="assigned_faculty")
    notes = relationship("LeadNote", back_populates="author")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Student(Base):
    """A prospective student (lead) who has interacted via WhatsApp."""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    exam_type = Column(String(30), nullable=True)  # CET / COMEDK / KCET
    language = Column(String(5), default="en")  # en / kn / hi
    is_hot_lead = Column(Boolean, default=False)

    # ── New lead management fields ───────────────────────────────────
    lead_score = Column(Integer, default=0)  # 0-10 AI intent score
    lead_status = Column(String(20), default="new")  # new / in_progress / visit_scheduled / admitted / not_interested
    course_interest = Column(String(100), nullable=True)  # e.g. "Engineering - CSE"
    source = Column(String(20), default="whatsapp")  # whatsapp / walk_in / broadcast
    message_count = Column(Integer, default=0)  # Total inbound messages
    first_contact = Column(DateTime, nullable=True)  # First message
    last_active = Column(DateTime, nullable=True)  # Most recent message
    total_session_minutes = Column(Integer, default=0)  # Active engagement time

    # ── Faculty assignment ───────────────────────────────────────────
    assigned_faculty_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    interactions = relationship("Interaction", back_populates="student")
    notes = relationship("LeadNote", back_populates="student", order_by="LeadNote.created_at.desc()")
    assigned_faculty = relationship("User", back_populates="assigned_leads")

    def __repr__(self):
        return f"<Student(id={self.id}, phone='{self.phone}', score={self.lead_score}, status='{self.lead_status}')>"


class Interaction(Base):
    """A single message exchanged with a student (inbound or outbound)."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    message_direction = Column(String(10), nullable=False)  # inbound / outbound
    message_body = Column(Text, nullable=True)
    message_type = Column(String(20), default="text")  # text / template / interactive
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    student = relationship("Student", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(id={self.id}, dir='{self.message_direction}', type='{self.message_type}')>"


class LeadNote(Base):
    """Faculty notes attached to a lead."""

    __tablename__ = "lead_notes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    student = relationship("Student", back_populates="notes")
    author = relationship("User", back_populates="notes")

    def __repr__(self):
        return f"<LeadNote(id={self.id}, student={self.student_id}, by={self.user_id})>"
