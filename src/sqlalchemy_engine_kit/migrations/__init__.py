"""
Alembic Migration Utilities

This module provides Alembic integration for engine-kit.
Alembic is an optional dependency - install with: pip install alembic
"""

# Check Alembic availability
try:
    from alembic import config as alembic_config
    from alembic import command
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    alembic_config = None
    command = None

# Always export exception
from .exceptions import DatabaseMigrationError

# Export based on availability
if ALEMBIC_AVAILABLE:
    from .config import (
        create_alembic_config,
        get_alembic_config_from_manager,
    )
    from .manager import MigrationManager
    from .commands import (
        run_migrations,
        create_migration,
        get_current_revision,
        get_head_revision,
        upgrade_dry_run,
        upgrade_safe,
    )
    from .utils import init_alembic, init_alembic_auto
    
    __all__ = [
        'ALEMBIC_AVAILABLE',
        'DatabaseMigrationError',
        'MigrationManager',
        'create_alembic_config',
        'get_alembic_config_from_manager',
        'run_migrations',
        'create_migration',
        'get_current_revision',
        'get_head_revision',
        'upgrade_dry_run',
        'upgrade_safe',
        'init_alembic',
        'init_alembic_auto',
    ]
else:
    # Provide helpful error when trying to use migrations without Alembic
    def _alembic_not_installed(*args, **kwargs):
        raise ImportError(
            "Alembic is not installed. Install with: pip install alembic"
        )
    
    # Placeholder classes/functions for better error messages
    MigrationManager = _alembic_not_installed
    run_migrations = _alembic_not_installed
    create_migration = _alembic_not_installed
    create_alembic_config = _alembic_not_installed
    
    __all__ = [
        'ALEMBIC_AVAILABLE',
        'DatabaseMigrationError',
        'MigrationManager',
        'run_migrations',
        'create_migration',
        'create_alembic_config',
    ]