"""
Shared utility helpers.
"""

import logging

logger = logging.getLogger(__name__)


def extract_whatsapp_message(payload: dict) -> tuple[str | None, str | None, str | None]:
    """
    Extract sender phone, message text, and sender name from a WhatsApp
    Cloud API webhook payload.

    Args:
        payload: The full JSON body from Meta's POST /webhook.

    Returns:
        (phone, message_text, sender_name) — any may be None if not found.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None, None, None

        changes = entry[0].get("changes", [])
        if not changes:
            return None, None, None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None, None, None

        message = messages[0]
        phone = message.get("from")
        message_text = None
        sender_name = None

        # Extract text body based on message type
        msg_type = message.get("type")
        if msg_type == "text":
            message_text = message.get("text", {}).get("body")
        elif msg_type == "interactive":
            # Handle interactive button replies
            interactive = message.get("interactive", {})
            interactive_type = interactive.get("type")
            if interactive_type == "button_reply":
                message_text = interactive.get("button_reply", {}).get("id")
            elif interactive_type == "list_reply":
                message_text = interactive.get("list_reply", {}).get("id")

        # Extract sender profile name
        contacts = value.get("contacts", [])
        if contacts:
            profile = contacts[0].get("profile", {})
            sender_name = profile.get("name")

        return phone, message_text, sender_name

    except (IndexError, KeyError, TypeError) as e:
        logger.error("Failed to extract WhatsApp message: %s", e, exc_info=True)
        return None, None, None
