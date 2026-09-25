"""
Database connection and session initialization.
Supports PostgreSQL with fallback to SQLite for local development.
Includes defensive import guards if SQLAlchemy is not yet installed in runtime env.
"""
import os

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

if HAS_SQLALCHEMY:
    DB_URL = os.getenv("DATABASE_URL", "sqlite:///supportnova_dev.db")
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    engine = None
    SessionLocal = None
    Base = None

def get_db():
    """Dependency generator for database session."""
    if not HAS_SQLALCHEMY:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
