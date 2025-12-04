"""
Base Model Class for SQLAlchemy ORM

This module provides the declarative base class for all ORM models.
"""

try:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()