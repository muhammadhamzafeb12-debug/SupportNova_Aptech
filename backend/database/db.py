"""
Database connection and session initialization.
Supports PostgreSQL with fallback to SQLite for local development.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to SQLite local file if DATABASE_URL or Streamlit secrets not set
DB_URL = os.getenv("DATABASE_URL", "sqlite:///supportnova_dev.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency generator for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
