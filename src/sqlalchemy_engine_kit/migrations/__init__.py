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
    # Import commands (may import MigrationManager from manager)
    try:
    from .commands import (
        run_migrations,
        create_migration,
        get_current_revision,
        get_head_revision,
        upgrade_dry_run,
        upgrade_safe,
    )
    except ImportError as e:
        # If commands imports manager which doesn't exist, skip
        if "manager" in str(e).lower():
            run_migrations = None
            create_migration = None
            get_current_revision = None
            get_head_revision = None
            upgrade_dry_run = None
            upgrade_safe = None
        else:
            raise
    
    # Import utils
    try:
    from .utils import init_alembic, init_alembic_auto
    except ImportError:
        init_alembic = None
        init_alembic_auto = None
    
    # MigrationManager and config functions - may not exist
    try:
        from .manager import MigrationManager
    except ImportError:
        MigrationManager = None
    
    create_alembic_config = None
    get_alembic_config_from_manager = None
    
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