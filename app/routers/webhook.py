"""
Webhook router — handles Meta WhatsApp Cloud API verification and messages.

Features:
  - Multi-level interactive menu (category → branch → details)
  - All menu flows are static (zero AI calls)
  - Free-text questions use AI with conversation memory
  - Session-based interaction tracking
  - Lead scoring & course interest detection
  - SSE push for hot lead notifications
"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Student, Interaction
from app.services.whatsapp import (
    send_text_message,
    send_template_message,
    send_interactive_buttons,
    send_interactive_list,
)
from app.services.gemini import get_ai_response
from app.services.lead_detector import detect_hot_lead
from app.utils.helpers import extract_whatsapp_message
logger = logging.getLogger(__name__)
router = APIRouter()

# ── Course interest mapping ──────────────────────────────────────────
BUTTON_TO_COURSE = {
    "btn_engineering": "Engineering",
    "btn_iti": "ITI",
    "btn_nursing": "Nursing",
    "branch_cse": "Engineering - CSE",
    "branch_ece": "Engineering - ECE",
    "branch_me": "Engineering - ME",
    "branch_ce": "Engineering - CE",
    "branch_aiml": "Engineering - AI&ML",
    "branch_fitter": "ITI - Fitter",
    "branch_electrician": "ITI - Electrician",
    "branch_welder": "ITI - Welder",
    "branch_turner": "ITI - Turner",
    "branch_copa": "ITI - COPA",
    "branch_bsc_nursing": "Nursing - B.Sc",
    "branch_gnm": "Nursing - GNM",
    "branch_anm": "Nursing - ANM",
}

# Session timeout for interaction time calculation (30 minutes)
SESSION_TIMEOUT_MINUTES = 30


# ═══════════════════════════════════════════════════════════════════════
#  STRUCTURED MENU DATA — No AI calls needed
# ═══════════════════════════════════════════════════════════════════════

# ── Level 2: Detailed branch info ────────────────────────────────────

BRANCH_DETAILS = {
    # Engineering branches
    "branch_cse": {
        "text": (
            "💻 *Computer Science & Engineering (CSE)*\n\n"
            "• Duration: 4 years (8 semesters)\n"
            "• Seats: 120\n"
            "• Fee: ₹75,000/year\n"
            "• Affiliation: VTU, Belagavi\n\n"
            "📊 *Placements:*\n"
            "• Avg Package: ₹4.5 LPA\n"
            "• Highest: ₹12 LPA (Infosys)\n"
            "• Recruiters: TCS, Wipro, Infosys, Cognizant\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCM with 45% (40% reserved)\n"
            "• Valid CET / COMEDK / JEE Main score\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Would you like to know about *fees*, *placements*, or *how to apply*? Just type your question! 💬",
    },
    "branch_ece": {
        "text": (
            "📡 *Electronics & Communication (ECE)*\n\n"
            "• Duration: 4 years (8 semesters)\n"
            "• Seats: 60\n"
            "• Fee: ₹65,000/year\n"
            "• Affiliation: VTU, Belagavi\n\n"
            "📊 *Placements:*\n"
            "• Recruiters: Bosch, Siemens, L&T, HCL\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCM with 45% (40% reserved)\n"
            "• Valid CET / COMEDK / JEE Main score\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Want details about *scholarships* or *hostel*? Just ask! 💬",
    },
    "branch_me": {
        "text": (
            "⚙️ *Mechanical Engineering (ME)*\n\n"
            "• Duration: 4 years (8 semesters)\n"
            "• Seats: 60\n"
            "• Fee: ₹55,000/year\n"
            "• Affiliation: VTU, Belagavi\n\n"
            "📊 *Placements:*\n"
            "• Recruiters: L&T, Godrej, Kirloskar, Bosch\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCM with 45% (40% reserved)\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Want to know about *campus facilities* or *admission process*? Just ask! 💬",
    },
    "branch_ce": {
        "text": (
            "🏗️ *Civil Engineering (CE)*\n\n"
            "• Duration: 4 years (8 semesters)\n"
            "• Seats: 60\n"
            "• Fee: ₹55,000/year\n"
            "• Affiliation: VTU, Belagavi\n\n"
            "📊 *Placements:*\n"
            "• Recruiters: L&T, Godrej, Shapoorji Pallonji\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCM with 45% (40% reserved)\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },
    "branch_aiml": {
        "text": (
            "🤖 *AI & Machine Learning (AI&ML)*\n\n"
            "• Duration: 4 years (8 semesters)\n"
            "• Seats: 60\n"
            "• Fee: ₹75,000/year\n"
            "• Affiliation: VTU, Belagavi\n\n"
            "📊 *Placements:*\n"
            "• Recruiters: Infosys, TCS, Tech Mahindra\n"
            "• High demand in AI/Data Science sector\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCM with 45% (40% reserved)\n"
            "• Valid CET / COMEDK / JEE Main score\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Interested in *scholarships* or *hostel facilities*? Just ask! 💬",
    },

    # ITI branches
    "branch_fitter": {
        "text": (
            "🔧 *Fitter (ITI)*\n\n"
            "• Duration: 2 years\n"
            "• Seats: 40\n"
            "• Fee: ₹15,000/year\n"
            "• Affiliation: NCVT\n"
            "• Eligibility: 10th pass\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Want to know about other ITI trades? Type *menu* to go back! 💬",
    },
    "branch_electrician": {
        "text": (
            "⚡ *Electrician (ITI)*\n\n"
            "• Duration: 2 years\n"
            "• Seats: 40\n"
            "• Fee: ₹15,000/year\n"
            "• Affiliation: NCVT\n"
            "• Eligibility: 10th pass\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Want to know about other ITI trades? Type *menu* to go back! 💬",
    },
    "branch_welder": {
        "text": (
            "🔥 *Welder (ITI)*\n\n"
            "• Duration: 1 year\n"
            "• Seats: 20\n"
            "• Fee: ₹12,000/year\n"
            "• Affiliation: NCVT\n"
            "• Eligibility: 8th pass\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },
    "branch_turner": {
        "text": (
            "🔩 *Turner (ITI)*\n\n"
            "• Duration: 2 years\n"
            "• Seats: 20\n"
            "• Fee: ₹15,000/year\n"
            "• Affiliation: NCVT\n"
            "• Eligibility: 10th pass\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },
    "branch_copa": {
        "text": (
            "🖥️ *COPA — Computer Operator & Programming (ITI)*\n\n"
            "• Duration: 1 year\n"
            "• Seats: 40\n"
            "• Fee: ₹18,000/year\n"
            "• Affiliation: NCVT\n"
            "• Eligibility: 10th pass\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },

    # Nursing branches
    "branch_bsc_nursing": {
        "text": (
            "👩‍⚕️ *B.Sc Nursing*\n\n"
            "• Duration: 4 years\n"
            "• Seats: 60\n"
            "• Fee: ₹85,000/year\n"
            "• Affiliation: MUHS, Nashik\n"
            "• Clinical training at Sanmati Hospital (500-bed)\n\n"
            "📋 *Eligibility:*\n"
            "• 12th PCB with 45% minimum\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Want to know about *hostel* or *scholarships*? Just ask! 💬",
    },
    "branch_gnm": {
        "text": (
            "🏥 *GNM — General Nursing & Midwifery*\n\n"
            "• Duration: 3.5 years (includes 6-month internship)\n"
            "• Seats: 40\n"
            "• Fee: ₹45,000/year\n\n"
            "📋 *Eligibility:*\n"
            "• 12th pass (any stream) with 40% minimum\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },
    "branch_anm": {
        "text": (
            "💉 *ANM — Auxiliary Nursing & Midwifery*\n\n"
            "• Duration: 2 years\n"
            "• Seats: 30\n"
            "• Fee: ₹35,000/year\n\n"
            "📋 *Eligibility:*\n"
            "• 10th pass with 40% minimum\n\n"
            "📞 Helpline: +91 98765 43210"
        ),
        "follow_up": "Have more questions? Just type them! 💬",
    },
}


# ── Level 1: Category menus (send sub-buttons) ──────────────────────

async def _send_engineering_submenu(phone: str) -> str:
    """Send engineering branches as a scrollable list."""
    result = await send_interactive_list(
        phone=phone,
        body_text=(
            "🎓 *ENGINEERING PROGRAMS*\n\n"
            "Sanmati Engineering College offers 5 B.E. programs "
            "(4-year, VTU affiliated).\n\n"
            "Tap below to see details about a specific branch:"
        ),
        button_text="📋 View Branches",
        sections=[{
            "title": "Engineering Branches",
            "rows": [
                {"id": "branch_cse",  "title": "💻 CSE",   "description": "120 seats — ₹75,000/yr"},
                {"id": "branch_ece",  "title": "📡 ECE",   "description": "60 seats — ₹65,000/yr"},
                {"id": "branch_me",   "title": "⚙️ ME",    "description": "60 seats — ₹55,000/yr"},
                {"id": "branch_ce",   "title": "🏗️ CE",    "description": "60 seats — ₹55,000/yr"},
                {"id": "branch_aiml", "title": "🤖 AI&ML", "description": "60 seats — ₹75,000/yr"},
            ],
        }],
        header_text="Sanmati Engineering College",
        footer_text="📞 Helpline: +91 98765 43210",
    )

    # Fallback to plain text if interactive list fails
    if "error" in result:
        logger.warning("Interactive list failed, sending plain text.")
        fallback = (
            "🎓 *ENGINEERING PROGRAMS*\n\n"
            "1. CSE — 120 seats — ₹75,000/yr\n"
            "2. ECE — 60 seats — ₹65,000/yr\n"
            "3. ME — 60 seats — ₹55,000/yr\n"
            "4. CE — 60 seats — ₹55,000/yr\n"
            "5. AI&ML — 60 seats — ₹75,000/yr\n\n"
            "Which branch would you like to know more about? 💬"
        )
        await send_text_message(phone, fallback)
        return fallback

    return "[Interactive: Engineering Branch List]"


async def _send_iti_submenu(phone: str) -> str:
    """Send ITI trades as a scrollable list."""
    result = await send_interactive_list(
        phone=phone,
        body_text=(
            "🔧 *ITI COURSES*\n\n"
            "NCVT-affiliated trade courses.\n\n"
            "Tap below to see details about a specific trade:"
        ),
        button_text="📋 View Trades",
        sections=[{
            "title": "ITI Trades",
            "rows": [
                {"id": "branch_fitter",      "title": "🔧 Fitter",      "description": "2 yrs — ₹15,000/yr"},
                {"id": "branch_electrician",  "title": "⚡ Electrician",  "description": "2 yrs — ₹15,000/yr"},
                {"id": "branch_welder",       "title": "🔥 Welder",      "description": "1 yr — ₹12,000/yr"},
                {"id": "branch_turner",       "title": "🔩 Turner",      "description": "2 yrs — ₹15,000/yr"},
                {"id": "branch_copa",         "title": "🖥️ COPA",        "description": "1 yr — ₹18,000/yr"},
            ],
        }],
        header_text="Sanmati ITI",
        footer_text="📞 Helpline: +91 98765 43210",
    )

    if "error" in result:
        logger.warning("Interactive list failed, sending plain text.")
        fallback = (
            "🔧 *ITI COURSES*\n\n"
            "1. Fitter — 2 yrs — ₹15,000/yr\n"
            "2. Electrician — 2 yrs — ₹15,000/yr\n"
            "3. Welder — 1 yr — ₹12,000/yr\n"
            "4. Turner — 2 yrs — ₹15,000/yr\n"
            "5. COPA — 1 yr — ₹18,000/yr\n\n"
            "Which trade interests you? 💬"
        )
        await send_text_message(phone, fallback)
        return fallback

    return "[Interactive: ITI Trades List]"


async def _send_nursing_submenu(phone: str) -> str:
    """Send nursing programs as buttons (only 3 — perfect for buttons)."""
    result = await send_interactive_buttons(
        phone=phone,
        body_text=(
            "🏥 *NURSING PROGRAMS*\n\n"
            "Clinical training at Sanmati Hospital (500-bed).\n\n"
            "Tap a program to see full details:"
        ),
        buttons=[
            {"id": "branch_bsc_nursing", "title": "👩‍⚕️ B.Sc Nursing"},
            {"id": "branch_gnm",         "title": "🏥 GNM"},
            {"id": "branch_anm",         "title": "💉 ANM"},
        ],
        header_text="Sanmati Nursing College",
        footer_text="📞 Helpline: +91 98765 43210",
    )

    if "error" in result:
        logger.warning("Interactive buttons failed, sending plain text.")
        fallback = (
            "🏥 *NURSING PROGRAMS*\n\n"
            "1. B.Sc Nursing — 4 yrs — ₹85,000/yr\n"
            "2. GNM — 3.5 yrs — ₹45,000/yr\n"
            "3. ANM — 2 yrs — ₹35,000/yr\n\n"
            "Which program interests you? 💬"
        )
        await send_text_message(phone, fallback)
        return fallback

    return "[Interactive: Nursing Programs Buttons]"


# ── Map category IDs to submenu handlers ─────────────────────────────

CATEGORY_HANDLERS = {
    "btn_engineering": _send_engineering_submenu,
    "btn_iti":         _send_iti_submenu,
    "btn_nursing":     _send_nursing_submenu,
}

# Map old-style text inputs ("1", "2", "3") to button IDs
TEXT_TO_BUTTON_ID = {
    "1": "btn_engineering",
    "2": "btn_iti",
    "3": "btn_nursing",
}

WELCOME_BODY = (
    "I'm your AI Admission Counselor. How can I help you today?\n\n"
    "Tap a button below, or simply type any question about "
    "admissions, fees, placements, hostel, or campus life! 💬"
)

GREETING_WORDS = {"hi", "hii", "hello", "hey", "start", "menu"}

# Maximum number of past messages to feed to AI for context
CONVERSATION_MEMORY_LIMIT = 10


# ═══════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

# ── GET /webhook — Meta verification ────────────────────────────────

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta sends a GET request to verify the webhook URL.
    We must return hub.challenge if the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning("Webhook verification failed — token mismatch.")
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Helper: build conversation history for AI ────────────────────────

def _build_conversation_history(db: Session, student_id: int) -> list[dict]:
    """
    Load recent interactions from the database and format them as
    OpenAI-style messages for conversation context.
    """
    recent = (
        db.query(Interaction)
        .filter(Interaction.student_id == student_id)
        .order_by(Interaction.timestamp.desc())
        .limit(CONVERSATION_MEMORY_LIMIT)
        .all()
    )

    # Reverse to chronological order (oldest first)
    messages = []
    for msg in reversed(recent):
        role = "user" if msg.message_direction == "inbound" else "assistant"
        if msg.message_body:
            messages.append({"role": role, "content": msg.message_body})

    return messages


# ── POST /webhook — Incoming messages ───────────────────────────────

@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Process incoming WhatsApp messages with multi-level menu support.

    Flow:
      greeting → [🎓 Engineering] [🔧 ITI] [🏥 Nursing]       (Level 0 — buttons)
      tap Engineering → [CSE] [ECE] [ME] [CE] [AI&ML]          (Level 1 — list)
      tap CSE → detailed info + follow-up prompt               (Level 2 — text)
      free-text → AI with conversation memory                  (AI path)
    """
    payload = await request.json()
    logger.info("📨 RAW WEBHOOK PAYLOAD: %s", payload)

    phone, message_text, sender_name = extract_whatsapp_message(payload)
    logger.info("📋 Extracted — phone: %s, text: %s, name: %s", phone, message_text, sender_name)

    # Ignore payloads without a message (e.g., status updates)
    if not phone or not message_text:
        logger.info("⏭️ Ignoring payload — no phone or message_text")
        return {"status": "ignored"}

    logger.info("Message from %s (%s): %s", phone, sender_name, message_text)

    # ── Get or create student record ─────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    student = db.query(Student).filter(Student.phone == phone).first()
    if not student:
        student = Student(
            phone=phone,
            name=sender_name,
            first_contact=now,
            last_active=now,
            source="whatsapp",
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        logger.info("New student created: %s", student)

    # Update name if we didn't have it
    if sender_name and not student.name:
        student.name = sender_name

    # ── Session-based interaction time tracking ──────────────────────
    if student.last_active:
        gap_minutes = (now - student.last_active).total_seconds() / 60
        if gap_minutes < SESSION_TIMEOUT_MINUTES:
            student.total_session_minutes = (student.total_session_minutes or 0) + int(gap_minutes)
    student.last_active = now
    if not student.first_contact:
        student.first_contact = now
    student.message_count = (student.message_count or 0) + 1
    db.commit()

    # ── Log inbound interaction ──────────────────────────────────────
    inbound = Interaction(
        student_id=student.id,
        message_direction="inbound",
        message_body=message_text,
        message_type="text",
    )
    db.add(inbound)
    db.commit()

    # ── Lead scoring ─────────────────────────────────────────────────
    score = 0
    if detect_hot_lead(message_text):
        score += 3  # high-intent keyword
    if (student.message_count or 0) > 5:
        score += 2  # engaged
    if (student.message_count or 0) > 15:
        score += 1  # highly engaged
    if (student.total_session_minutes or 0) > 10:
        score += 2  # spent real time
    if student.course_interest:
        score += 2  # drilled into a specific branch
    score = min(score, 10)

    if score > (student.lead_score or 0):
        student.lead_score = score
    student.is_hot_lead = (student.lead_score or 0) >= 7
    db.commit()



    logger.info("📊 Lead score: %d | Session: %d min | Messages: %d",
                student.lead_score or 0, student.total_session_minutes or 0, student.message_count or 0)

    # ── Route message ────────────────────────────────────────────────
    clean_text = message_text.strip()

    # Normalize: map "1"→"btn_engineering", "2"→"btn_iti", "3"→"btn_nursing"
    resolved_id = TEXT_TO_BUTTON_ID.get(clean_text, clean_text)

    if resolved_id in CATEGORY_HANDLERS:
        # ── Level 1: Category selected → show sub-menu ───────────────
        handler = CATEGORY_HANDLERS[resolved_id]
        response_text = await handler(phone)
        msg_type = "interactive"
        # Track course interest
        if resolved_id in BUTTON_TO_COURSE:
            student.course_interest = BUTTON_TO_COURSE[resolved_id]
            db.commit()

    elif resolved_id in BRANCH_DETAILS:
        # ── Level 2: Specific branch selected → show details ─────────
        branch = BRANCH_DETAILS[resolved_id]
        await send_text_message(phone, branch["text"])
        await send_text_message(phone, branch["follow_up"])
        response_text = branch["text"]
        msg_type = "text"
        # Track specific branch interest
        if resolved_id in BUTTON_TO_COURSE:
            student.course_interest = BUTTON_TO_COURSE[resolved_id]
            db.commit()

    elif clean_text.lower() in GREETING_WORDS:
        # ── Level 0: Welcome → Send interactive buttons ──────────────
        send_result = await send_interactive_buttons(
            phone=phone,
            body_text=WELCOME_BODY,
            buttons=[
                {"id": "btn_engineering", "title": "🎓 Engineering"},
                {"id": "btn_iti",         "title": "🔧 ITI Courses"},
                {"id": "btn_nursing",     "title": "🏥 Nursing"},
            ],
            header_text="🙏 Welcome to Sanmati College!",
            footer_text="Or type any question below",
        )
        logger.info("📤 SEND RESULT for interactive greeting: %s", send_result)

        # If interactive buttons failed, fall back to plain text
        if "error" in send_result:
            logger.warning("Interactive buttons failed, sending plain text fallback.")
            fallback = (
                "🙏 *Welcome to Sanmati Engineering College!*\n\n"
                "I'm your AI Admission Counselor. How can I help?\n\n"
                "📋 *Quick Menu:*\n"
                "Type *1* — Engineering Programs\n"
                "Type *2* — ITI Courses\n"
                "Type *3* — Nursing Programs\n\n"
                "Or simply ask me any question! 💬"
            )
            await send_text_message(phone, fallback)
            response_text = fallback
        else:
            response_text = "[Interactive Welcome Menu]"
        msg_type = "interactive"

    else:
        # ── Free-text question → AI with conversation memory ─────────
        history = _build_conversation_history(db, student.id)
        ai_reply = await get_ai_response(clean_text, student.name, history)
        await send_text_message(phone, ai_reply)
        response_text = ai_reply
        msg_type = "text"

    # ── Log outbound interaction ─────────────────────────────────────
    outbound = Interaction(
        student_id=student.id,
        message_direction="outbound",
        message_body=response_text,
        message_type=msg_type,
    )
    db.add(outbound)
    db.commit()

    return {"status": "processed"}
