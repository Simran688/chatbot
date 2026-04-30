"""
Database initialization utilities.
"""

from app.db.base import Base, engine
from app.models import User, Document, ChatHistory  # noqa: F401


def init_db() -> None:
    """
    Create all database tables.
    Run this once to initialize the database schema.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
