"""
Model Mixins for Common Functionality

This module provides reusable mixins for common model features like timestamps,
soft delete, and audit logging.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.orm import declared_attr


def _utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Mixin for automatic timestamp management."""
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=_utc_now,
            nullable=False,
            doc="Timestamp when the record was created"
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=_utc_now,
            onupdate=_utc_now,
            nullable=False,
            doc="Timestamp when the record was last updated"
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    @declared_attr
    def is_deleted(cls):
        return Column(
            Boolean,
            default=False,
            nullable=False,
            doc="Flag indicating if the record is soft-deleted"
        )
    
    @declared_attr
    def deleted_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=True,
            doc="Timestamp when the record was soft-deleted"
        )
    
    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin for audit logging fields."""
    
    @declared_attr
    def created_by(cls):
        return Column(
            String(255),
            nullable=True,
            doc="Username or user ID who created the record"
        )
    
    @declared_attr
    def updated_by(cls):
        return Column(
            String(255),
            nullable=True,
            doc="Username or user ID who last updated the record"
        )