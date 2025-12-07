"""
High-level Migration Commands

This module provides convenience functions for common migration operations.
These functions work with both DatabaseEngine and DatabaseManager instances.
"""

from typing import Optional, Union, TYPE_CHECKING

# MigrationManager may not exist - handle gracefully
try:
from .manager import MigrationManager
except ImportError:
    # MigrationManager not implemented yet
    MigrationManager = None
from .exceptions import DatabaseMigrationError

if TYPE_CHECKING:
    from ..engine.engine import DatabaseEngine
    from ..engine.manager import DatabaseManager
    EngineOrManager = Union['DatabaseEngine', 'DatabaseManager']


def run_migrations(
    engine_or_manager: 'EngineOrManager',
    revision: str = "head",
    script_location: str = "alembic"
) -> None:
    """Run migrations to specified revision (convenience function).
    
    This is a convenience function that creates a MigrationManager and
    runs migrations. It accepts either a DatabaseEngine or DatabaseManager
    instance for flexibility.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        revision: Target revision (default: "head" for latest)
        script_location: Alembic script location directory
    
    Raises:
        DatabaseMigrationError: Invalid argument or migration failed
    
    Examples:
        >>> # Using DatabaseEngine
        >>> engine.start()
        >>> run_migrations(engine, revision="head")
        >>> 
        >>> # Using DatabaseManager
        >>> manager.initialize(config, auto_start=True)
        >>> run_migrations(manager, revision="head")
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    mgr.upgrade(revision)


def create_migration(
    engine_or_manager: 'EngineOrManager',
    message: str,
    autogenerate: bool = True,
    script_location: str = "alembic"
) -> str:
    """Create new migration (convenience function).
    
    This is a convenience function that creates a MigrationManager and
    creates a new migration file.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        message: Migration message/description
        autogenerate: Auto-generate migration from models (default: True)
        script_location: Alembic script location directory
    
    Returns:
        Created migration file path (informational)
    
    Raises:
        DatabaseMigrationError: Invalid argument or migration creation failed
    
    Examples:
        >>> # Create migration with DatabaseManager
        >>> create_migration(manager, "add_user_table", autogenerate=True)
        >>> 
        >>> # Create manual migration
        >>> create_migration(engine, "custom_changes", autogenerate=False)
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    return mgr.create_migration(message, autogenerate=autogenerate)


def get_current_revision(
    engine_or_manager: 'EngineOrManager',
    script_location: str = "alembic"
) -> Optional[str]:
    """Get current database revision (convenience function).
    
    This is a convenience function that creates a MigrationManager and
    retrieves the current database revision.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        script_location: Alembic script location directory
    
    Returns:
        Current revision string or None if no migrations applied
    
    Raises:
        DatabaseMigrationError: Invalid argument or failed to get revision
    
    Examples:
        >>> # Get current revision
        >>> current = get_current_revision(manager)
        >>> if current:
        ...     print(f"Current revision: {current}")
        >>> else:
        ...     print("No migrations applied")
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    return mgr.get_current_revision()


def get_head_revision(
    engine_or_manager: 'EngineOrManager',
    script_location: str = "alembic"
) -> Optional[str]:
    """Get head revision (latest migration) (convenience function).
    
    This is a convenience function that creates a MigrationManager and
    retrieves the head (latest) migration revision.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        script_location: Alembic script location directory
    
    Returns:
        Head revision string or None if no migrations exist
    
    Raises:
        DatabaseMigrationError: Invalid argument or failed to get revision
    
    Examples:
        >>> # Get head revision
        >>> head = get_head_revision(manager)
        >>> print(f"Latest migration: {head}")
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    return mgr.get_head_revision()


def upgrade_dry_run(
    engine_or_manager: 'EngineOrManager',
    revision: str = "head",
    script_location: str = "alembic"
) -> str:
    """Dry-run upgrade - show SQL that would be executed (convenience function).
    
    This is a convenience function that performs a dry-run upgrade, showing
    the SQL statements that would be executed without actually applying them.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        revision: Target revision (default: "head" for latest)
        script_location: Alembic script location directory
    
    Returns:
        SQL statements that would be executed (as string)
    
    Raises:
        DatabaseMigrationError: Invalid argument or dry-run failed
    
    Examples:
        >>> # See what would be executed
        >>> sql = upgrade_dry_run(manager, revision="head")
        >>> print(sql)
        >>> 
        >>> # Review before applying
        >>> if review_sql(sql):
        ...     run_migrations(manager, revision="head")
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    return mgr.upgrade_dry_run(revision)


def upgrade_safe(
    engine_or_manager: 'EngineOrManager',
    revision: str = "head",
    verify: bool = True,
    script_location: str = "alembic"
) -> bool:
    """Safe upgrade with verification (convenience function).
    
    This is a convenience function that performs an upgrade with safety
    checks and verification.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
        revision: Target revision (default: "head" for latest)
        verify: Verify upgrade success (default: True)
        script_location: Alembic script location directory
    
    Returns:
        True if upgrade successful
    
    Raises:
        DatabaseMigrationError: Invalid argument or upgrade failed
    """
    if MigrationManager is None:
        raise ImportError(
            "MigrationManager is not available. "
            "Alembic may not be installed or MigrationManager implementation is missing. "
            "Install with: pip install alembic"
        )
    
    engine = _extract_engine(engine_or_manager)
    mgr = MigrationManager(engine, script_location=script_location)
    return mgr.upgrade_safe(revision, verify=verify)


def _extract_engine(engine_or_manager: 'EngineOrManager') -> 'DatabaseEngine':
    """Extract DatabaseEngine from argument.
    
    Args:
        engine_or_manager: DatabaseEngine or DatabaseManager instance
    
    Returns:
        DatabaseEngine instance
    
    Raises:
        DatabaseMigrationError: Invalid argument type
    """
    # Import here to avoid circular imports
    from ..engine.engine import DatabaseEngine
    from ..engine.manager import DatabaseManager
    
    if isinstance(engine_or_manager, DatabaseManager):
        return engine_or_manager.engine
    elif isinstance(engine_or_manager, DatabaseEngine):
        return engine_or_manager
    else:
        raise DatabaseMigrationError(
            message=f"Invalid argument type. Expected DatabaseEngine or DatabaseManager, got {type(engine_or_manager).__name__}",
            operation="_extract_engine"
        )