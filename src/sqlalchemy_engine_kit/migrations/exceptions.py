"""
Migration-specific exceptions

This module provides exception classes for Alembic migration operations.
"""

from typing import Optional, Dict, Any

from ..core.exceptions import DatabaseError


class DatabaseMigrationError(DatabaseError):
    """Exception raised when migration operations fail.
    
    This exception is raised when there's an issue with Alembic migration
    operations, such as migration failures, revision conflicts, or Alembic
    configuration problems.
    
    Attributes:
        operation (str, optional): Migration operation that failed
        revision (str, optional): Revision involved in the error
        migration_message (str, optional): Migration message (for create_migration)
    
    Examples:
        >>> # Migration upgrade failed
        >>> raise DatabaseMigrationError(
        ...     message="Migration upgrade failed",
        ...     operation="upgrade",
        ...     revision="head",
        ...     context={"error": "Connection timeout"}
        ... )
        
        >>> # Migration creation failed
        >>> raise DatabaseMigrationError(
        ...     message="Failed to create migration",
        ...     operation="create_migration",
        ...     migration_message="add_user_table",
        ...     context={"error": "No changes detected"}
        ... )
    
    Note:
        - Use this for all migration-related errors
        - Include operation and revision information when available
        - Provide context for debugging migration issues
    """
    
    def __init__(
        self,
        message: str = "Migration operation failed",
        operation: Optional[str] = None,
        revision: Optional[str] = None,
        migration_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseMigrationError.
        
        Args:
            message: Error message
            operation: Migration operation that failed (upgrade, downgrade, create_migration, etc.)
            revision: Revision involved in the error
            migration_message: Migration message (for create_migration operations)
            context: Additional context information
            original_error: Original exception
        """
        self.operation = operation
        self.revision = revision
        self.migration_message = migration_message
        
        full_context = context or {}
        if operation:
            full_context["operation"] = operation
        if revision:
            full_context["revision"] = revision
        if migration_message:
            full_context["migration_message"] = migration_message
        
        super().__init__(
            message=message,
            operation=operation or "migration",
            context=full_context,
            original_error=original_error
        )

