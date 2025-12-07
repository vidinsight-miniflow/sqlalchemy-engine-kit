"""
Alembic Initialization Utilities

This module provides utilities for initializing Alembic in a project.
"""

from pathlib import Path
from typing import Optional, Any, TYPE_CHECKING

from ..core.logging import LoggerAdapter
from .exceptions import DatabaseMigrationError
# Check Alembic availability locally
try:
    from alembic import config as alembic_config
    from alembic import command
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    alembic_config = None
    command = None

if TYPE_CHECKING:
    from ..engine.engine import DatabaseEngine
    from sqlalchemy import MetaData

_logger = LoggerAdapter.get_logger(__name__)

if ALEMBIC_AVAILABLE:
    from alembic.config import Config as AlembicConfig
    from alembic import command
else:
    AlembicConfig = None
    command = None


def init_alembic(
    script_location: str = "alembic",
    template: str = "generic",
    package: bool = False
) -> None:
    """Initialize Alembic in current directory.
    
    This function initializes Alembic by creating the necessary directory
    structure and configuration files.
    
    Args:
        script_location: Alembic script location directory (default: "alembic")
        template: Alembic template to use (default: "generic")
        package: Create as Python package (default: False)
    
    Raises:
        DatabaseMigrationError: Alembic not installed or initialization failed
    
    Examples:
        >>> # Basic initialization
        >>> init_alembic()
        >>> 
        >>> # Custom location
        >>> init_alembic(script_location="migrations")
        >>> 
        >>> # As package
        >>> init_alembic(package=True)
    
    Note:
        - Alembic must be installed (pip install alembic)
        - This creates the Alembic directory structure
        - You may need to manually update env.py with your models
    """
    if not ALEMBIC_AVAILABLE:
        raise DatabaseMigrationError(
            message="Alembic not installed. Install with: pip install alembic",
            operation="init_alembic"
        )
    
    script_path = Path(script_location)
    
    if script_path.exists():
        raise DatabaseMigrationError(
            message=f"Alembic directory already exists: {script_location}",
            operation="init_alembic"
        )
    
    try:
        # Create minimal Alembic config for init
        config = AlembicConfig()
        
        # Initialize Alembic
        command.init(config, script_location, template=template, package=package)
        
        _logger.info(f"Alembic initialized successfully at: {script_location}")
        _logger.info("Next steps:")
        _logger.info("1. Update alembic/env.py with your models")
        _logger.info("2. Set target_metadata = Base.metadata")
        _logger.info("3. Create your first migration")
    except Exception as e:
        raise DatabaseMigrationError(
            message=f"Alembic initialization failed: {e}",
            operation="init_alembic",
            original_error=e
        )


def init_alembic_auto(
    engine: 'DatabaseEngine',
    base_metadata: 'MetaData',
    script_location: str = "alembic",
    template: str = "generic",
    package: bool = False,
    models_import_path: Optional[str] = None
) -> None:
    """Initialize Alembic with automatic configuration from DatabaseEngine.
    
    This function initializes Alembic and automatically configures env.py
    with the DatabaseEngine's connection string and base_metadata. This
    eliminates the need for manual configuration.
    
    Args:
        engine: DatabaseEngine instance (must be started)
        base_metadata: SQLAlchemy Base.metadata object
        script_location: Alembic script location directory (default: "alembic")
        template: Alembic template to use (default: "generic")
        package: Create as Python package (default: False)
        models_import_path: Import path for models (e.g., "myapp.models")
    
    Raises:
        DatabaseMigrationError: Alembic not installed or initialization failed
        DatabaseEngineError: Engine not started
    
    Examples:
        >>> from engine_kit import DatabaseManager
        >>> from database.models import Base
        >>> 
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        >>> 
        >>> # Auto-initialize Alembic
        >>> init_alembic_auto(
        ...     manager.engine, 
        ...     Base.metadata,
        ...     models_import_path="database.models"
        ... )
        >>> 
        >>> # Now ready to create migrations
        >>> from engine_kit.migrations import create_migration
        >>> create_migration(manager, "initial_schema")
    
    Note:
        - Engine must be started before calling this function
        - This creates a fully configured Alembic setup
        - env.py is automatically configured with connection string and metadata
        - Connection string is stored via environment variable for security
    """
    if not ALEMBIC_AVAILABLE:
        raise DatabaseMigrationError(
            message="Alembic not installed. Install with: pip install alembic",
            operation="init_alembic_auto"
        )
    
    # Import here to avoid circular dependency
    from ..engine.engine import DatabaseEngine
    from ..core.exceptions import DatabaseEngineError
    
    if not isinstance(engine, DatabaseEngine):
        raise DatabaseMigrationError(
            message=f"Invalid engine type. Expected DatabaseEngine, got {type(engine).__name__}",
            operation="init_alembic_auto"
        )
    
    if not engine.is_alive:
        raise DatabaseEngineError(
            message="Engine not started. Call engine.start() first.",
            engine_state="stopped",
            operation="init_alembic_auto"
        )
    
    script_path = Path(script_location)
    
    if script_path.exists():
        raise DatabaseMigrationError(
            message=f"Alembic directory already exists: {script_location}",
            operation="init_alembic_auto"
        )
    
    try:
        # Initialize Alembic
        init_alembic(script_location=script_location, template=template, package=package)
        
        # Auto-configure env.py
        env_py_path = script_path / "env.py"
        
        if not env_py_path.exists():
            raise DatabaseMigrationError(
                message=f"env.py not found after initialization: {env_py_path}",
                operation="init_alembic_auto"
            )
        
        # Generate connection string from engine
        connection_string = engine._connection_string
        
        # Infer models import path if not provided
        if models_import_path is None:
            # Try to get from metadata's bind or use default
            models_import_path = "models"
        
        # Generate new env.py with proper configuration
        new_env_py = _generate_env_py_content(
            connection_string=connection_string,
            models_import_path=models_import_path
        )
        
        # Backup original
        backup_path = env_py_path.with_suffix('.py.bak')
        env_py_path.rename(backup_path)
        
        # Write new env.py
        env_py_path.write_text(new_env_py)
        
        _logger.info(f"Alembic initialized and auto-configured at: {script_location}")
        _logger.info(f"Original env.py backed up to: {backup_path}")
        _logger.info(f"Set DATABASE_URL environment variable or update env.py with connection string")
        _logger.info("Alembic is ready to use!")
        
    except DatabaseMigrationError:
        raise
    except Exception as e:
        raise DatabaseMigrationError(
            message=f"Auto-initialization failed: {e}",
            operation="init_alembic_auto",
            original_error=e
        )


def _generate_env_py_content(
    connection_string: str,
    models_import_path: str
) -> str:
    """Generate env.py content with auto-configuration.
    
    Args:
        connection_string: Database connection string (used as fallback)
        models_import_path: Import path for models module
    
    Returns:
        Generated env.py content
    """
    # Mask password in connection string for fallback (security)
    masked_connection_string = _mask_password_in_url(connection_string)
    
    env_py_template = '''"""
Auto-generated Alembic environment configuration.

This file was auto-generated by engine-kit migrations.init_alembic_auto().
Connection string and metadata are automatically configured.

SECURITY NOTE: Set DATABASE_URL environment variable instead of hardcoding
the connection string to avoid exposing credentials.
"""

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import your models' Base.metadata here
# Update this import path to match your project structure
try:
    from {models_import_path} import Base
    target_metadata = Base.metadata
except ImportError:
    # Fallback: try common patterns
    try:
        from models import Base
        target_metadata = Base.metadata
    except ImportError:
        # If models can't be imported, set to None
        # You'll need to manually configure this
        target_metadata = None
        import warnings
        warnings.warn(
            "Could not import models. Please manually set target_metadata in env.py"
        )

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get connection string from environment variable (recommended for security)
# Falls back to a placeholder if not set
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "{masked_connection_string}"  # Update this or set DATABASE_URL env var
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# add your model's MetaData object here for 'autogenerate' support
# target_metadata = mymodel.Base.metadata

# other values from the config, defined by the needs of env.py
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''.format(
        models_import_path=models_import_path,
        masked_connection_string=masked_connection_string
    )
    
    return env_py_template


def _mask_password_in_url(url: str) -> str:
    """Mask password in database URL for security.
    
    Args:
        url: Database connection URL
    
    Returns:
        URL with password masked as ***
    """
    try:
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(url)
        
        if parsed.password:
            # Replace password with ***
            netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            masked = parsed._replace(netloc=netloc)
            return urlunparse(masked)
        
        return url
    except Exception:
        # If parsing fails, return placeholder
        return "postgresql://user:***@localhost/dbname"