"""
Application configuration — loads environment variables.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment."""

    # WhatsApp Cloud API
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "")

    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///sanmati.db")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "sanmati-jwt-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

    # WhatsApp API base URL
    WA_API_BASE: str = "https://graph.facebook.com/v21.0"

    @property
    def wa_messages_url(self) -> str:
        return f"{self.WA_API_BASE}/{self.WHATSAPP_PHONE_NUMBER_ID}/messages"

    @property
    def wa_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }


settings = Settings()
