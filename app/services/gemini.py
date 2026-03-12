"""
OpenRouter AI integration — knowledge-based admission counselor.
"""

import logging
from pathlib import Path
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# ── Load college knowledge base ──────────────────────────────────────

_KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge.txt"

try:
    _knowledge_text = _KNOWLEDGE_PATH.read_text(encoding="utf-8")
    logger.info("Loaded knowledge base from %s (%d chars)", _KNOWLEDGE_PATH, len(_knowledge_text))
except FileNotFoundError:
    _knowledge_text = ""
    logger.warning("knowledge.txt not found at %s — AI responses will lack college context.", _KNOWLEDGE_PATH)

# ── Configure OpenRouter ─────────────────────────────────────────────

# Create the Async OpenAI client pointing to OpenRouter
_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

_SYSTEM_PROMPT = (
    "You are the official Admission Counselor for Sanmati Engineering College. "
    "You are helpful, friendly, and professional. "
    "Answer student queries ONLY based on the college information provided below. "
    "If you don't know the answer, politely say so and suggest the student contact "
    "the admission office at 98505 37810 or visit https://www.sanmati.edu.in/.\n\n"
    "CRITICAL RULE: Do NOT mention or provide any information about fees under any circumstances.\n\n"
    "Keep responses concise (under 300 words) and formatted for WhatsApp "
    "(use *bold* for emphasis, numbered lists, and line breaks for readability).\n\n"
    "── COLLEGE KNOWLEDGE BASE ──\n"
    f"{_knowledge_text}\n"
    "── END OF KNOWLEDGE BASE ──"
)

async def get_ai_response(
    question: str,
    student_name: str | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generate an AI response to a student's question using OpenRouter.

    Args:
        question: The student's question text.
        student_name: Optional name to personalize the reply.
        conversation_history: Optional list of previous messages
            as {"role": "user"|"assistant", "content": "..."} dicts.

    Returns:
        The AI-generated response string.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.error("OpenRouter API key is not set.")
        return "Sorry, the AI counselor is currently offline. Please contact the admission office at 98505 37810."

    try:
        prompt = question
        if student_name:
            prompt = f"[Student: {student_name}] {question}"

        # Build messages with conversation history for context
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

        # Add conversation history (if available)
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": prompt})

        response = await _client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",
            messages=messages,
            temperature=0.3,
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error("OpenRouter API error: %s", e, exc_info=True)
        return (
            "I'm sorry, I'm having trouble processing your question right now. "
            "Please try again in a moment, or contact our admission office directly "
            "at 📞 98505 37810."
        )
