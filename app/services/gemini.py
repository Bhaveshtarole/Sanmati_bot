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
    timeout=15.0,  # 15-second timeout to avoid long waits
)

_SYSTEM_PROMPT = (
    "You are the official Admission Counselor for Sanmati Engineering College, Washim. "
    "You are helpful, friendly, and professional. "
    "Answer student queries ONLY based on the college information provided below.\n\n"
    "🔥 GOLDEN FORMULA (YOU MUST FOLLOW THIS STRICTLY IN EVERY RESPONSE):\n"
    "1. Give value (answer the user's question clearly in short bullet points).\n"
    "2. Ask a follow-up question (e.g., 'What would you like to know next?').\n"
    "3. Suggest options for them to reply with (e.g., 'Reply with: 1. Fees, 2. Admission Process, 3. Request Call').\n\n"
    "❌ NEVER send long paragraphs. NEVER send too much text.\n"
    "✅ Keep messages short, clear, and structured. Use emojis.\n\n"
    "── COLLEGE KNOWLEDGE BASE ──\n"
    f"{_knowledge_text}\n"
    "── END OF KNOWLEDGE BASE ──\n"
    "Remember: ALWAYS end your response with a follow-up question and exactly 2 or 3 suggested options they can reply with."
)

_LANGUAGE_INSTRUCTIONS = {
    "hi": (
        "\n\n🌐 LANGUAGE INSTRUCTION: You MUST respond in Hinglish (Hindi mixed with English). "
        "Use Devanagari script but keep English technical words as-is. "
        "Example: 'CSE branch में 60 seats available हैं। Fees structure के लिए admission office से contact करें।' "
        "Do NOT use pure Hindi. Mix Hindi and English naturally like students speak."
    ),
    "mr": (
        "\n\n🌐 LANGUAGE INSTRUCTION: You MUST respond in Marathlish (Marathi mixed with English). "
        "Use Devanagari script but keep English technical words as-is. "
        "Example: 'CSE branch मध्ये 60 seats available आहेत। Fees structure साठी admission office ला contact करा।' "
        "Do NOT use pure Marathi. Mix Marathi and English naturally like students speak."
    ),
}

async def get_ai_response(
    question: str,
    student_name: str | None = None,
    conversation_history: list[dict] | None = None,
    language: str = "en",
) -> str:
    """
    Generate an AI response to a student's question using OpenRouter.

    Args:
        question: The student's question text.
        student_name: Optional name to personalize the reply.
        conversation_history: Optional list of previous messages
            as {"role": "user"|"assistant", "content": "..."} dicts.
        language: Language code ("en", "hi", "mr") for response language.

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

        # Build system prompt with optional language instruction
        system_content = _SYSTEM_PROMPT
        lang_instruction = _LANGUAGE_INSTRUCTIONS.get(language)
        if lang_instruction:
            system_content = _SYSTEM_PROMPT + lang_instruction

        # Build messages with conversation history for context
        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (if available)
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": prompt})

        response = await _client.chat.completions.create(
            model="openrouter/owl-alpha",
            messages=messages,
            temperature=0.3,
            max_tokens=300,  # Keep replies short & fast for WhatsApp
        )
        
        reply = response.choices[0].message.content
        if not reply:
            logger.warning("OpenRouter returned empty response.")
            return "Could you please rephrase your question? I'd love to help! 😊"
        return reply.strip()

    except Exception as e:
        logger.error("OpenRouter API error (%s): %s", type(e).__name__, e, exc_info=True)
        return (
            "I'm sorry, I'm having trouble processing your question right now. "
            "Please try again in a moment, or contact our admission office directly "
            "at 📞 98505 37810."
        )

