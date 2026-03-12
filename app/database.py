"""
SQLAlchemy database engine, session factory, and dependency.

Reads DATABASE_URL from environment. Defaults to SQLite.
Switch to PostgreSQL by changing only the .env file.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sanmati.db")

# SQLite needs check_same_thread=False; PostgreSQL does not
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and auto-closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
