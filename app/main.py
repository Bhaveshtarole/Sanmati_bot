"""
Sanmati Admission Bot + Dashboard — FastAPI entry point.

Local:      uvicorn app.main:app --reload --port 8000
Railway:    Procfile / railway.toml handles this automatically
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sanmati Admission Bot",
    version="2.1.0",
    description="WhatsApp Admission Bot + Counselor Dashboard API for Sanmati College",
)

# ── CORS ──────────────────────────────────────────────────────────────
# ALLOWED_ORIGINS env var: comma-separated list, or "*" for all (dev default)
# Railway: set ALLOWED_ORIGINS=https://your-app.vercel.app
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")

if _raw_origins.strip() == "*":
    # Development mode — allow everything
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # credentials not allowed with wildcard
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production mode — explicit origins (Vercel domain etc.)
    _origins = [o.strip() for o in _raw_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Static Files (brochure PDF, campus image) ────────────────────────
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created / verified.")
    logger.info("🚀 Sanmati Admission Bot + Dashboard API is running!")


# ── Routers ──────────────────────────────────────────────────────────
from app.routers import webhook    # noqa: E402
from app.routers import dashboard  # noqa: E402

app.include_router(webhook.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Sanmati Admission Bot + Dashboard API",
        "version": "2.1.0",
    }


@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "Sanmati Admission Bot + Dashboard API",
        "version": "2.1.0",
    }
