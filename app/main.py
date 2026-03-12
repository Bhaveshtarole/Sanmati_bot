"""
Sanmati Admission Bot + Dashboard — FastAPI entry point.
"""

import logging

from fastapi import FastAPI

from app.database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sanmati Admission Bot", version="2.0.1")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created / verified.")
    logger.info("🚀 Sanmati Admission Bot is running!")


# ── Routers ─────────────────────────────────────────────────────────
from app.routers import webhook  # noqa: E402

app.include_router(webhook.router)


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Sanmati Admission Bot", "version": "2.0.0"}
