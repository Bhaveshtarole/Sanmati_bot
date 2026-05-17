"""
Webhook router — handles Meta WhatsApp Cloud API verification and messages.

Features:
  - Language selection on first contact (English / Hindi / Marathi)
  - Multi-level interactive menu (category → branch → details)
  - All menu flows are static (zero AI calls)
  - Free-text questions use AI with conversation memory
  - Session-based interaction tracking
  - Lead scoring & course interest detection
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
    send_document_message,
    mark_as_read,
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
    "branch_ee": "Engineering - Electrical",
    "branch_me": "Engineering - ME",
    "branch_ce": "Engineering - CE",
    "branch_aids": "Engineering - AI&DS",
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
    "branch_cse": {
        "text": (
            "\U0001f4bb *Computer Science & Engineering (CSE)*\n\n"
            "\u23f3 Duration: 4 years\n"
            "\U0001f393 Seats: 60\n\n"
            "\U0001f4c8 *Career Opportunities:*\n"
            "\u2022 Software Development & Web Development\n"
            "\u2022 Data Science & Cloud Computing\n"
            "\u2022 Database Administration & IT Consulting\n\n"
            "*HOD:* Prof. S.R. Tayade\n"
            "\U0001f4de 855 284 1000"
        ),
    },
    "branch_ee": {
        "text": (
            "\u26a1 *Electrical Engineering (EE)*\n\n"
            "\u23f3 Duration: 4 years\n"
            "\U0001f393 Seats: 60\n\n"
            "\U0001f4c8 *Career Opportunities:*\n"
            "\u2022 Power Generation & Distribution\n"
            "\u2022 Renewable Energy Sector\n"
            "\u2022 Automation & Control Systems\n"
            "\u2022 Robotics & Smart Grid Technologies\n\n"
            "*HOD:* Prof. Nayanish Ambhore\n"
            "\U0001f4de +91 70382 38444"
        ),
    },
    "branch_me": {
        "text": (
            "\u2699\ufe0f *Mechanical Engineering (ME)*\n\n"
            "\u23f3 Duration: 4 years\n"
            "\U0001f393 Seats: 60\n\n"
            "\U0001f4c8 *Career Opportunities:*\n"
            "\u2022 Design Engineer, Manufacturing Engineer\n"
            "\u2022 Automotive & Energy Engineer\n"
            "\u2022 R&D, HVAC, Project Engineer\n\n"
            "*HOD:* Prof. Swapnil Kurhekar\n"
            "\U0001f4de +91 85509 90922"
        ),
    },
    "branch_ce": {
        "text": (
            "\U0001f3d7\ufe0f *Civil Engineering (CE)*\n\n"
            "\u23f3 Duration: 4 years\n"
            "\U0001f393 Seats: 60\n\n"
            "\U0001f4c8 *Career Opportunities:*\n"
            "\u2022 Construction & Infrastructure\n"
            "\u2022 Government Sector & Consulting\n"
            "\u2022 Environmental Engineering\n\n"
            "*HOD:* Prof. Kunal Ghadge\n"
            "\U0001f4de +91 7391060812"
        ),
    },
    "branch_aids": {
        "text": (
            "\U0001f916 *Artificial Intelligence & Data Science (AI&DS)*\n\n"
            "\u23f3 Duration: 4 years\n"
            "\U0001f393 Seats: 60\n\n"
            "\U0001f4c8 *Career Opportunities:*\n"
            "\u2022 Data Scientist, ML Engineer\n"
            "\u2022 AI Engineer, Big Data Engineer\n"
            "\u2022 Business Intelligence Analyst\n\n"
            "*HOD:* Prof. M.G. Jaiswal\n"
            "\U0001f4de +91 7391060816"
        ),
    },

    # ITI branches
    "branch_fitter": {"text": "\U0001f527 *Fitter (ITI)*\n\n\u23f3 Duration: 2 years\n\U0001f393 Seats: 40\n\nExcellent hands-on machinery training."},
    "branch_electrician": {"text": "\u26a1 *Electrician (ITI)*\n\n\u23f3 Duration: 2 years\n\U0001f393 Seats: 40\n\nPractical electrical systems training."},
    "branch_welder": {"text": "\U0001f525 *Welder (ITI)*\n\n\u23f3 Duration: 1 year\n\U0001f393 Seats: 20\n\nHigh industry demand for skilled welders."},
    "branch_turner": {"text": "\U0001f529 *Turner (ITI)*\n\n\u23f3 Duration: 2 years\n\U0001f393 Seats: 20\n\nPrecision machining and tooling focus."},
    "branch_copa": {"text": "\U0001f5a5\ufe0f *COPA (ITI)*\n\n\u23f3 Duration: 1 year\n\U0001f393 Seats: 40\n\nComputer Operator & Programming Assistant."},

    # Nursing branches
    "branch_bsc_nursing": {"text": "\U0001f469\u200d\u2695\ufe0f *B.Sc Nursing*\n\n\u23f3 Duration: 4 years\n\U0001f393 Seats: 60\n\nClinical training at premier hospitals."},
    "branch_gnm": {"text": "\U0001f3e5 *GNM*\n\n\u23f3 Duration: 3.5 years\n\U0001f393 Seats: 40\n\nGeneral Nursing & Midwifery."},
    "branch_anm": {"text": "\U0001f489 *ANM*\n\n\u23f3 Duration: 2 years\n\U0001f393 Seats: 30\n\nAuxiliary Nursing & Midwifery."},
}


# ── Level 1: Category menus (send sub-buttons) ──────────────────────

async def _send_courses_categories(phone: str) -> str:
    """Send Course categories as buttons (Workaround for Meta's 10-row list limit)."""
    body_content = (
        "\U0001f393 *Explore Our Programs*\n\n"
        "*Engineering (B.E.)*\n"
        "\u2022 Computer Science (CSE)\n"
        "\u2022 Electrical Engineering\n"
        "\u2022 Mechanical (ME)\n"
        "\u2022 Civil (CE)\n"
        "\u2022 AI & Data Science (AI&DS)\n\n"
        "*Nursing*\n"
        "\u2022 B.Sc Nursing\n"
        "\u2022 GNM\n"
        "\u2022 ANM\n\n"
        "*ITI Trades*\n"
        "\u2022 Fitter\n"
        "\u2022 Electrician\n"
        "\u2022 COPA\n\n"
        "\U0001f447 Select a category below to view program details:"
    )
    
    result = await send_interactive_buttons(
        phone=phone,
        body_text=body_content,
        buttons=[
            {"id": "btn_cat_eng", "title": "\u2699\ufe0f Engineering"},
            {"id": "btn_cat_nur", "title": "\U0001f3e5 Nursing"},
            {"id": "btn_cat_iti", "title": "\U0001f527 ITI Trades"},
        ]
    )
    
    if "error" in result:
        logger.warning("Interactive categories failed, sending plain text.")
        fallback = "Reply with your branch name to get details (e.g. CSE, ITI Fitter, B.Sc Nursing)."
        await send_text_message(phone, fallback)
        return fallback

    return "[Interactive: Course Categories]"

async def _send_eng_list(phone: str) -> str:
    result = await send_interactive_list(
        phone=phone,
        body_text="\u2699\ufe0f *Engineering Programs (B.E.)*\n\nTap to select a branch:",
        button_text="View Branches",
        sections=[{
            "title": "Engineering (B.E.)",
            "rows": [
                {"id": "branch_cse",  "title": "CSE"},
                {"id": "branch_ee",   "title": "Electrical"},
                {"id": "branch_me",   "title": "Mechanical"},
                {"id": "branch_ce",   "title": "Civil"},
                {"id": "branch_aids", "title": "AI & DS"},
            ]
        }],
        header_text="Engineering",
    )
    return "[Interactive: Engineering List]"

async def _send_nur_list(phone: str) -> str:
    result = await send_interactive_list(
        phone=phone,
        body_text="\U0001f3e5 *Nursing Programs*\n\nTap to select a program:",
        button_text="View Nursing",
        sections=[{
            "title": "Nursing Programs",
            "rows": [
                {"id": "branch_bsc_nursing", "title": "B.Sc Nursing"},
                {"id": "branch_gnm",         "title": "GNM"},
                {"id": "branch_anm",         "title": "ANM"},
            ]
        }],
        header_text="Nursing",
    )
    return "[Interactive: Nursing List]"

async def _send_iti_list(phone: str) -> str:
    result = await send_interactive_list(
        phone=phone,
        body_text="\U0001f527 *ITI Trades*\n\nTap to select a trade:",
        button_text="View ITI Trades",
        sections=[{
            "title": "ITI Trades",
            "rows": [
                {"id": "branch_fitter",      "title": "Fitter"},
                {"id": "branch_electrician",  "title": "Electrician"},
                {"id": "branch_copa",         "title": "COPA"},
            ]
        }],
        header_text="ITI Trades",
    )
    return "[Interactive: ITI List]"


# ── Map category IDs to submenu handlers ─────────────────────────────

CATEGORY_HANDLERS = {
    "btn_courses": _send_courses_categories,
    "btn_cat_eng": _send_eng_list,
    "btn_cat_nur": _send_nur_list,
    "btn_cat_iti": _send_iti_list,
}

# Map old-style text inputs ("1", "2", "3") to button IDs
TEXT_TO_BUTTON_ID = {
    "1": "btn_courses",
    "2": "btn_campus",
    "3": "btn_brochure",
}

WELCOME_BODY = (
    "\U0001f64f *Welcome to Sanmati Engineering College, Washim!*\n\n"
    "I'm your AI Admission Counselor\n\n"
    "I can help you with:\n"
    "\U0001f393 Courses & branches\n"
    "\U0001f4b0 Fees & scholarships\n"
    "\U0001f3eb Campus & hostel\n"
    "\U0001f4c8 Placements\n\n"
    "\U0001f447 Tap a button below to explore programs or ask me anything."
)

# ── Language selection ────────────────────────────────────────────────

LANG_SELECTION_BODY = (
    "\U0001f64f *Sanmati Engineering College, Washim*\n\n"
    "\u0915\u0943\u092a\u092f\u093e \u0906\u092a\u0932\u0940 language select \u0915\u0930\u093e / \u0905\u092a\u0928\u0940 language \u091a\u0941\u0928\u0947\u0902 \U0001f447\n"
    "Please select your preferred language \U0001f447"
)

LANG_BUTTON_IDS = {"lang_en", "lang_hi", "lang_mr"}
LANG_MAP = {"lang_en": "en", "lang_hi": "hi", "lang_mr": "mr"}

# ── Localized messages ───────────────────────────────────────────────

MESSAGES = {
    "en": {
        "welcome_body": (
            "\U0001f64f *Welcome to Sanmati Engineering College, Washim!*\n\n"
            "I'm your AI Admission Counselor\n\n"
            "I can help you with:\n"
            "\U0001f393 Courses & branches\n"
            "\U0001f4b0 Fees & scholarships\n"
            "\U0001f3eb Campus & hostel\n"
            "\U0001f4c8 Placements\n\n"
            "\U0001f447 Tap a button below to explore programs or ask me anything."
        ),
        "fallback_welcome": (
            "\U0001f64f *Welcome to Sanmati Engineering College!*\n\n"
            "I'm your AI Admission Counselor. How can I help?\n\n"
            "\U0001f4cb *Quick Menu:*\n"
            "Type *1* \u2014 Courses\n"
            "Type *2* \u2014 Campus & Fees\n"
            "Type *3* \u2014 Brochure\n\n"
            "Or simply ask me any question! \U0001f4ac"
        ),
        "campus_text": (
            "\U0001f3eb *Campus Highlights:*\n\n"
            "\u2022 10-12 acre modern campus\n"
            "\u2022 16 digital classrooms & labs\n"
            "\u2022 Central Library with 15,000+ books\n"
            "\u2022 Separate boys & girls hostels\n"
            "\u2022 Clean canteen & auditorium\n"
            "\u2022 Transport facility available\n\n"
            "\U0001f4f8 Check out our brochure for campus pictures!"
        ),
        "conversion_text": (
            "\U0001f393 Admissions are open for 2025!\n\n"
            "If you want personal guidance, our admission counselor can help you.\n\n"
            "\U0001f447 Choose an option:"
        ),
        "lead_capture_text": (
            "\U0001f4de Great! Our admission team will contact you shortly.\n\n"
            "Please confirm:\n"
            "\u2022 Your name\n"
            "\u2022 Preferred course\n\n"
            "Our counselor will guide you step-by-step."
        ),
        "visit_text": (
            "\U0001f3eb You can visit our campus and meet faculty.\n\n"
            "This helps you understand facilities and placements better.\n\n"
            "Reply *VISIT* or tell us your preferred date to schedule your campus tour."
        ),
        "follow_up_body": "What would you like to know next?",
        "brochure_caption": "Here is the official 2025 Admission Brochure for Sanmati College! \U0001f393",
        "footer_text": "Or type any question below",
    },
    "hi": {
        "welcome_body": (
            "\U0001f64f *Sanmati Engineering College, Washim mein aapka swagat hai!*\n\n"
            "Main aapka AI Admission Counselor hoon\n\n"
            "Main aapki help kar sakta hoon:\n"
            "\U0001f393 Courses & branches\n"
            "\U0001f4b0 Fees & scholarships\n"
            "\U0001f3eb Campus & hostel\n"
            "\U0001f4c8 Placements\n\n"
            "\U0001f447 Neeche button tap karein ya koi bhi question poochein."
        ),
        "fallback_welcome": (
            "\U0001f64f *Sanmati Engineering College mein aapka swagat!*\n\n"
            "Main aapka AI Admission Counselor hoon.\n\n"
            "\U0001f4cb *Quick Menu:*\n"
            "Type *1* \u2014 Courses\n"
            "Type *2* \u2014 Campus & Fees\n"
            "Type *3* \u2014 Brochure\n\n"
            "Ya koi bhi question puchiye! \U0001f4ac"
        ),
        "campus_text": (
            "\U0001f3eb *Campus Highlights:*\n\n"
            "\u2022 10-12 acre ka modern campus\n"
            "\u2022 16 digital classrooms & labs\n"
            "\u2022 Central Library mein 15,000+ books\n"
            "\u2022 Boys & Girls ke liye alag hostels\n"
            "\u2022 Clean canteen & auditorium\n"
            "\u2022 Transport facility available\n\n"
            "\U0001f4f8 Campus photos ke liye brochure dekhiye!"
        ),
        "conversion_text": (
            "\U0001f393 2025 ke liye Admissions open hain!\n\n"
            "Agar aapko personal guidance chahiye, toh hamare admission counselor help karenge.\n\n"
            "\U0001f447 Ek option choose karein:"
        ),
        "lead_capture_text": (
            "\U0001f4de Bahut accha! Hamari admission team aapko jaldi contact karegi.\n\n"
            "Please confirm karein:\n"
            "\u2022 Aapka name\n"
            "\u2022 Preferred course\n\n"
            "Hamare counselor aapko step-by-step guide karenge."
        ),
        "visit_text": (
            "\U0001f3eb Aap hamare campus visit kar sakte hain aur faculty se mil sakte hain.\n\n"
            "Isse aapko facilities aur placements better samajh aayenge.\n\n"
            "*VISIT* type karein ya apni preferred date batayein campus tour schedule karne ke liye."
        ),
        "follow_up_body": "Aage aur kya jaanna chahenge?",
        "brochure_caption": "Yeh Sanmati College ka official 2025 Admission Brochure hai! \U0001f393",
        "footer_text": "Ya koi bhi question type karein",
    },
    "mr": {
        "welcome_body": (
            "\U0001f64f *Sanmati Engineering College, Washim madhye aaple swagat!*\n\n"
            "Mi tumcha AI Admission Counselor aahe\n\n"
            "Mi tumhala help karu shakto:\n"
            "\U0001f393 Courses & branches\n"
            "\U0001f4b0 Fees & scholarships\n"
            "\U0001f3eb Campus & hostel\n"
            "\U0001f4c8 Placements\n\n"
            "\U0001f447 Khalche button tap kara kinva kontahi question vichara."
        ),
        "fallback_welcome": (
            "\U0001f64f *Sanmati Engineering College madhye swagat!*\n\n"
            "Mi tumcha AI Admission Counselor aahe.\n\n"
            "\U0001f4cb *Quick Menu:*\n"
            "Type *1* \u2014 Courses\n"
            "Type *2* \u2014 Campus & Fees\n"
            "Type *3* \u2014 Brochure\n\n"
            "Kinva kontahi question vichara! \U0001f4ac"
        ),
        "campus_text": (
            "\U0001f3eb *Campus Highlights:*\n\n"
            "\u2022 10-12 acre cha modern campus\n"
            "\u2022 16 digital classrooms & labs\n"
            "\u2022 Central Library madhye 15,000+ books\n"
            "\u2022 Boys & Girls sathi separate hostels\n"
            "\u2022 Clean canteen & auditorium\n"
            "\u2022 Transport facility available\n\n"
            "\U0001f4f8 Campus photos sathi brochure bagha!"
        ),
        "conversion_text": (
            "\U0001f393 2025 sathi Admissions open aahet!\n\n"
            "Jar tumhala personal guidance have asel, tar aamche admission counselor help kartil.\n\n"
            "\U0001f447 Ek option nivda:"
        ),
        "lead_capture_text": (
            "\U0001f4de Chhan! Aamchi admission team tumhala lavkarach contact karel.\n\n"
            "Please confirm kara:\n"
            "\u2022 Tumche name\n"
            "\u2022 Preferred course\n\n"
            "Aamche counselor tumhala step-by-step guide kartil."
        ),
        "visit_text": (
            "\U0001f3eb Tumhi aamcha campus visit karu shakta aani faculty la bhetu shakta.\n\n"
            "Yamule tumhala facilities aani placements changalya prakare samjatil.\n\n"
            "*VISIT* type kara kinva tumchi preferred date sanga campus tour schedule karnyasathi."
        ),
        "follow_up_body": "Pudhe ajun kay janun ghyayche aahe?",
        "brochure_caption": "He Sanmati College che official 2025 Admission Brochure aahe! \U0001f393",
        "footer_text": "Kinva kontahi question type kara",
    },
}


def _msg(lang: str, key: str) -> str:
    """Get a localized message. Falls back to English."""
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"][key])


GREETING_WORDS = {"hi", "hii", "hello", "hey", "start", "menu", "namaste", "namaskar"}

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

    logger.warning("Webhook verification failed \u2014 token mismatch.")
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


# ── Helper: send welcome menu ────────────────────────────────────────

async def _send_welcome_menu(phone: str, lang: str, request: Request) -> tuple[str, str]:
    """Send the welcome menu in the student's language. Returns (response_text, msg_type)."""
    base_url = str(request.base_url).rstrip('/')
    image_url = f"{base_url}/static/campus.jpg"

    send_result = await send_interactive_buttons(
        phone=phone,
        body_text=_msg(lang, "welcome_body"),
        buttons=[
            {"id": "btn_courses",  "title": "\U0001f393 Courses"},
            {"id": "btn_campus",   "title": "\U0001f3eb Campus & Fees"},
            {"id": "btn_brochure", "title": "\U0001f4e5 Brochure"},
        ],
        header_image_url=image_url,
        footer_text=_msg(lang, "footer_text"),
    )
    logger.info("\U0001f4e4 SEND RESULT for interactive greeting: %s", send_result)

    if "error" in send_result:
        logger.warning("Interactive buttons failed, sending plain text fallback.")
        fallback = _msg(lang, "fallback_welcome")
        await send_text_message(phone, fallback)
        return fallback, "text"

    return "[Interactive Welcome Menu]", "interactive"


# ── Deduplication cache ──────────────────────────────────────────────
# Meta retries webhook calls if response is slow. This prevents
# processing the same message multiple times and sending duplicate replies.
import time as _time

_processed_messages: dict[str, float] = {}  # message_id -> timestamp
_DEDUP_WINDOW_SECONDS = 300  # 5 minutes


def _cleanup_old_messages():
    """Remove entries older than the dedup window to prevent memory leak."""
    cutoff = _time.time() - _DEDUP_WINDOW_SECONDS
    stale = [mid for mid, ts in _processed_messages.items() if ts < cutoff]
    for mid in stale:
        del _processed_messages[mid]


# ── POST /webhook — Incoming messages ───────────────────────────────

@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Process incoming WhatsApp messages with language selection and multi-level menu.

    Flow:
      first message -> language selection [English] [Hindi] [Marathi]
      select language -> welcome menu in chosen language
      greeting -> [\U0001f393 Courses] [\U0001f3eb Campus] [\U0001f4e5 Brochure]     (Level 0)
      tap Courses -> [Engineering] [Nursing] [ITI]                (Level 0.5)
      tap Engineering -> [CSE] [EE] [ME] [CE] [AI&DS]            (Level 1)
      tap CSE -> detailed info + follow-up prompt                 (Level 2)
      free-text -> AI with conversation memory                    (AI path)
    """
    payload = await request.json()
    logger.info("\U0001f4e8 RAW WEBHOOK PAYLOAD: %s", payload)

    phone, message_text, sender_name, message_id = extract_whatsapp_message(payload)
    logger.info("\U0001f4cb Extracted \u2014 phone: %s, text: %s, name: %s", phone, message_text, sender_name)

    # Ignore payloads without a message (e.g., status updates)
    if not phone or not message_text:
        logger.info("\u23ed\ufe0f Ignoring payload \u2014 no phone or message_text")
        return {"status": "ignored"}

    # ── Deduplication: skip if we already processed this message ──────
    if message_id and message_id in _processed_messages:
        logger.info("\u23ed\ufe0f Skipping duplicate message: %s", message_id)
        return {"status": "duplicate"}

    if message_id:
        _processed_messages[message_id] = _time.time()
        _cleanup_old_messages()

    # Mark message as read immediately (shows blue ticks)
    await mark_as_read(message_id)

    logger.info("Message from %s (%s): %s", phone, sender_name, message_text)

    # ── Get or create student record ─────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    student = db.query(Student).filter(Student.phone == phone).first()

    is_new_student = False
    if not student:
        student = Student(
            phone=phone,
            name=sender_name,
            first_contact=now,
            last_active=now,
            source="whatsapp",
            language=None,  # Not set yet — will trigger language selection
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        logger.info("New student created: %s", student)
        is_new_student = True

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

    logger.info("\U0001f4ca Lead score: %d | Session: %d min | Messages: %d",
                student.lead_score or 0, student.total_session_minutes or 0, student.message_count or 0)

    # ── Get student language (default to None if not set) ────────────
    lang = student.language or "en"
    clean_text = message_text.strip()

    # ── LANGUAGE SELECTION FLOW ──────────────────────────────────────
    # If language not set: on first message send language picker,
    # on language button tap save preference and show welcome menu.

    if not student.language:
        resolved_lang = clean_text  # Could be a button ID like "lang_en"

        if resolved_lang in LANG_BUTTON_IDS:
            # Student tapped a language button
            student.language = LANG_MAP[resolved_lang]
            db.commit()
            lang = student.language
            logger.info("Language set to: %s for student %s", lang, student.phone)

            # Send welcome menu in chosen language
            response_text, msg_type = await _send_welcome_menu(phone, lang, request)

        else:
            # First message from new user — send language selection
            await send_interactive_buttons(
                phone=phone,
                body_text=LANG_SELECTION_BODY,
                buttons=[
                    {"id": "lang_en", "title": "English"},
                    {"id": "lang_hi", "title": "Hindi"},
                    {"id": "lang_mr", "title": "Marathi"},
                ],
            )
            response_text = "[Language Selection Sent]"
            msg_type = "interactive"

        # Log outbound and return
        outbound = Interaction(
            student_id=student.id,
            message_direction="outbound",
            message_body=response_text,
            message_type=msg_type,
        )
        db.add(outbound)
        db.commit()
        return {"status": "processed"}

    # ── Route message (language is already set) ──────────────────────
    # Normalize: map "1"->"btn_courses", "2"->"btn_campus", "3"->"btn_brochure"
    resolved_id = TEXT_TO_BUTTON_ID.get(clean_text, clean_text)

    if resolved_id in CATEGORY_HANDLERS:
        # ── Level 1: Category selected -> show sub-menu ───────────────
        handler = CATEGORY_HANDLERS[resolved_id]
        response_text = await handler(phone)
        msg_type = "interactive"
        # Track course interest
        if resolved_id in BUTTON_TO_COURSE:
            student.course_interest = BUTTON_TO_COURSE[resolved_id]
            db.commit()

    elif resolved_id in BRANCH_DETAILS:
        # ── Level 2: Specific branch selected -> show details ─────────
        branch = BRANCH_DETAILS[resolved_id]
        await send_text_message(phone, branch["text"])
        
        # Follow-up interactive message (Message 2)
        buttons = [
            {"id": "btn_fees", "title": "\U0001f4b0 Fees"},
            {"id": "btn_admission", "title": "\U0001f4c4 Admission"},
            {"id": "btn_call", "title": "\U0001f4de Request Call"}
        ]
        
        await send_interactive_buttons(
            phone=phone,
            body_text=_msg(lang, "follow_up_body"),
            buttons=buttons
        )
        response_text = branch["text"]
        msg_type = "interactive"
        # Track specific branch interest
        if resolved_id in BUTTON_TO_COURSE:
            student.course_interest = BUTTON_TO_COURSE[resolved_id]
            db.commit()

    elif resolved_id == "btn_campus":
        await send_text_message(phone, _msg(lang, "campus_text"))
        
        buttons = [
            {"id": "btn_call", "title": "\U0001f4de Request Call"},
            {"id": "btn_visit", "title": "\U0001f3eb Visit Campus"},
            {"id": "btn_admission", "title": "\U0001f4c4 Admission"}
        ]
        await send_interactive_buttons(phone, body_text=_msg(lang, "conversion_text"), buttons=buttons)
        response_text = "[Campus Highlights Menu]"
        msg_type = "interactive"

    elif resolved_id == "btn_brochure":
        base_url = str(request.base_url).rstrip('/')
        doc_url = f"{base_url}/static/brochure.pdf"
        
        await send_document_message(
            phone=phone,
            document_url=doc_url,
            filename="Sanmati_College_Brochure_2025.pdf",
            caption=_msg(lang, "brochure_caption"),
        )
        response_text = "[Brochure PDF Sent]"
        msg_type = "document"

    elif resolved_id == "btn_call":
        await send_text_message(phone, _msg(lang, "lead_capture_text"))
        response_text = "[Lead Capture Triggered]"
        msg_type = "text"
        
    elif resolved_id == "btn_visit":
        await send_text_message(phone, _msg(lang, "visit_text"))
        response_text = "[Campus Visit Triggered]"
        msg_type = "text"

    elif clean_text.lower() in GREETING_WORDS:
        # ── Level 0: Welcome -> Send interactive buttons ──────────────
        response_text, msg_type = await _send_welcome_menu(phone, lang, request)

    elif resolved_id in ["btn_fees", "btn_admission", "btn_hostel"]:
        # ── Route specific buttons to the AI via fake natural prompts ─
        prompts = {
            "btn_fees": "What is the detailed fee structure and also the scholarship options?",
            "btn_admission": "What is the step-by-step admission process and eligibility?",
            "btn_hostel": "Tell me about the hostel and campus facilities."
        }
        fake_prompt = prompts[resolved_id]
        history = _build_conversation_history(db, student.id)
        ai_reply = await get_ai_response(fake_prompt, student.name, history, language=lang)
        await send_text_message(phone, ai_reply)
        response_text = ai_reply
        msg_type = "text"

    else:
        # ── Free-text question -> AI with conversation memory ─────────
        history = _build_conversation_history(db, student.id)
        ai_reply = await get_ai_response(clean_text, student.name, history, language=lang)
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
