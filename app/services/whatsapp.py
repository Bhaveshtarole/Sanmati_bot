"""
WhatsApp Cloud API service — send text and template messages.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_text_message(phone: str, text: str) -> dict:
    """
    Send a plain text message to a WhatsApp number.

    Args:
        phone: Recipient phone number in international format (e.g. "919876543210").
        text: The message body.

    Returns:
        Meta API response as dict.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.wa_messages_url,
            headers=settings.wa_headers,
            json=payload,
        )

    if response.status_code != 200:
        logger.error(
            "WhatsApp text send failed: %s — %s",
            response.status_code,
            response.text,
        )

    return response.json()


async def send_template_message(
    phone: str,
    template_name: str,
    language_code: str = "en",
    components: list | None = None,
) -> dict:
    """
    Send a pre-approved WhatsApp template message.

    Args:
        phone: Recipient phone number (international format).
        template_name: Name of the approved template in Meta Business Manager.
        language_code: Template language code (default "en").
        components: Optional template components (header/body parameters).

    Returns:
        Meta API response as dict.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    if components:
        payload["template"]["components"] = components

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.wa_messages_url,
            headers=settings.wa_headers,
            json=payload,
        )

    if response.status_code != 200:
        logger.error(
            "WhatsApp template send failed: %s — %s",
            response.status_code,
            response.text,
        )

    return response.json()


async def send_interactive_buttons(
    phone: str,
    body_text: str,
    buttons: list[dict],
    header_text: str | None = None,
    footer_text: str | None = None,
) -> dict:
    """
    Send an interactive button message (max 3 buttons).

    Args:
        phone: Recipient phone number.
        body_text: Main message body.
        buttons: List of dicts with 'id' and 'title' keys (max 3).
        header_text: Optional header text.
        footer_text: Optional footer text.

    Returns:
        Meta API response as dict.
    """
    interactive = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                for btn in buttons[:3]  # WhatsApp allows max 3 buttons
            ]
        },
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": interactive,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.wa_messages_url,
            headers=settings.wa_headers,
            json=payload,
        )

    if response.status_code != 200:
        logger.error(
            "WhatsApp interactive buttons send failed: %s — %s",
            response.status_code,
            response.text,
        )

    return response.json()


async def send_interactive_list(
    phone: str,
    body_text: str,
    button_text: str,
    sections: list[dict],
    header_text: str | None = None,
    footer_text: str | None = None,
) -> dict:
    """
    Send an interactive list message (scrollable menu).

    Args:
        phone: Recipient phone number.
        body_text: Main message body.
        button_text: Text on the list open button (max 20 chars).
        sections: List of section dicts with 'title' and 'rows'.
                  Each row has 'id', 'title', and optional 'description'.
        header_text: Optional header text.
        footer_text: Optional footer text.

    Returns:
        Meta API response as dict.
    """
    interactive = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_text,
            "sections": sections,
        },
    }

    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"text": footer_text}

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": interactive,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.wa_messages_url,
            headers=settings.wa_headers,
            json=payload,
        )

    if response.status_code != 200:
        logger.error(
            "WhatsApp interactive list send failed: %s — %s",
            response.status_code,
            response.text,
        )

    return response.json()
