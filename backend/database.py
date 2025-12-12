"""Database connection and initialization."""
from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
import os

settings = get_settings()

# Get database URL with fallback
database_url = os.getenv("DATABASE_URL") or settings.database_url

# Handle PostgreSQL URL format (Render uses postgres:// but SQLAlchemy needs postgresql://)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate connection args based on database type
if database_url and "postgresql://" in database_url:
    # PostgreSQL configuration for production
    engine = create_engine(
        database_url,
        echo=settings.log_level == "DEBUG",
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
else:
    # SQLite configuration for development
    engine = create_engine(
        database_url or "sqlite:///./logsentinel.db",
        echo=settings.log_level == "DEBUG",
        connect_args={"check_same_thread": False}
    )


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
