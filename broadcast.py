"""
broadcast.py — Marketing Broadcast Tool for Sanmati Engineering College

Reads a CSV/Excel file of student contacts and sends WhatsApp template
messages in rate-limited batches (100 per hour).

Usage:
    python broadcast.py --file students.csv --template admission_welcome
    python broadcast.py --file students.xlsx --template admission_welcome --batch-size 50
"""

import argparse
import logging
import os
import time
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WA_API_BASE = "https://graph.facebook.com/v21.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("broadcast")


# ── Send template message (sync) ────────────────────────────────────

def send_template(phone: str, template_name: str, language: str = "en") -> bool:
    """
    Send a WhatsApp template message to a single phone number.

    Returns True on success, False on failure.
    """
    url = f"{WA_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": str(phone),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
        },
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        if response.status_code == 200:
            logger.info("✅ Sent to %s", phone)
            return True
        else:
            logger.error("❌ Failed for %s: %s — %s", phone, response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("❌ Error sending to %s: %s", phone, e)
        return False


# ── Load student data ────────────────────────────────────────────────

def load_students(file_path: str) -> pd.DataFrame:
    """Load student data from CSV or Excel file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    # Validate required column
    if "phone" not in df.columns:
        raise ValueError("File must contain a 'phone' column.")

    # Clean phone numbers — remove spaces, ensure string type
    df["phone"] = df["phone"].astype(str).str.strip().str.replace(" ", "", regex=False)

    logger.info("Loaded %d students from %s", len(df), file_path)
    return df


# ── Broadcast function ───────────────────────────────────────────────

def broadcast(
    file_path: str,
    template_name: str,
    batch_size: int = 100,
    delay_seconds: int = 3600,
):
    """
    Send WhatsApp template messages in rate-limited batches.

    Args:
        file_path: Path to CSV/Excel file with student data.
        template_name: Name of the approved WhatsApp template.
        batch_size: Number of messages per batch (default: 100).
        delay_seconds: Seconds to wait between batches (default: 3600 = 1 hour).
    """
    df = load_students(file_path)

    total = len(df)
    success_count = 0
    fail_count = 0

    logger.info(
        "📢 Starting broadcast: %d students, template='%s', batch_size=%d",
        total, template_name, batch_size,
    )

    for batch_num, start in enumerate(range(0, total, batch_size), start=1):
        batch = df.iloc[start : start + batch_size]
        logger.info(
            "── Batch %d: Sending to students %d–%d of %d ──",
            batch_num, start + 1, min(start + batch_size, total), total,
        )

        for _, row in batch.iterrows():
            phone = row["phone"]
            language = row.get("language", "en")

            if send_template(phone, template_name, language):
                success_count += 1
            else:
                fail_count += 1

            # Small delay between individual messages to avoid rate limits
            time.sleep(0.5)

        # If there are more batches, wait before continuing
        remaining = total - (start + batch_size)
        if remaining > 0:
            logger.info(
                "⏳ Batch %d complete. Waiting %d seconds before next batch… (%d remaining)",
                batch_num, delay_seconds, remaining,
            )
            time.sleep(delay_seconds)

    # ── Summary ──────────────────────────────────────────────────────
    logger.info("═" * 50)
    logger.info("📊 BROADCAST COMPLETE")
    logger.info("   Total: %d  |  ✅ Success: %d  |  ❌ Failed: %d", total, success_count, fail_count)
    logger.info("═" * 50)


# ── CLI entry point ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sanmati College — WhatsApp Marketing Broadcast Tool",
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to CSV or Excel file with student data (must have 'phone' column).",
    )
    parser.add_argument(
        "--template", "-t",
        required=True,
        help="Name of the approved WhatsApp template to send.",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=100,
        help="Number of messages per batch (default: 100).",
    )
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=3600,
        help="Delay in seconds between batches (default: 3600 = 1 hour).",
    )

    args = parser.parse_args()

    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error(
            "❌ WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set in .env file."
        )
        return

    broadcast(
        file_path=args.file,
        template_name=args.template,
        batch_size=args.batch_size,
        delay_seconds=args.delay,
    )


if __name__ == "__main__":
    main()
