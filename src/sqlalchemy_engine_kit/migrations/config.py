"""
Alembic Configuration Generator

This module provides utilities to create Alembic configuration from
DatabaseEngine and DatabaseConfig instances.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING

from ..core.exceptions import DatabaseEngineError
from ..core.logging import LoggerAdapter
from .exceptions import DatabaseMigrationError

if TYPE_CHECKING:
    from ..engine.engine import DatabaseEngine
    from ..engine.manager import DatabaseManager
    from alembic.config import Config as AlembicConfig

_logger = LoggerAdapter.get_logger(__name__)

# Check if Alembic is available
try:
    from alembic.config import Config as AlembicConfigClass
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    AlembicConfigClass = None


def create_alembic_config(
    engine: 'DatabaseEngine',
    script_location: str = "alembic",
    version_path_separator: str = "os",
    file_template: str = "%%(rev)s_%%(slug)s",
    **kwargs
) -> 'AlembicConfig':
    """Create Alembic configuration from DatabaseEngine.
    
    This function creates a configured AlembicConfig instance using the
    connection string and settings from a DatabaseEngine instance.
    
    Args:
        engine: DatabaseEngine instance (must be started)
        script_location: Alembic script location directory (default: "alembic")
        version_path_separator: Version path separator (default: "os")
        file_template: Migration file template (default: "%%(rev)s_%%(slug)s")
        **kwargs: Additional Alembic config options to set
    
    Returns:
        AlembicConfig: Configured Alembic config instance
    
    Raises:
        DatabaseMigrationError: If Alembic is not installed
        DatabaseEngineError: If not started
    
    Examples:
        >>> # Basic usage
        >>> config = create_alembic_config(engine)
        >>> 
        >>> # Custom script location
        >>> config = create_alembic_config(engine, script_location="migrations")
        >>> 
        >>> # Additional options
        >>> config = create_alembic_config(
        ...     engine,
        ...     script_location="alembic",
        ...     compare_type=True,
        ...     compare_server_default=True
        ... )
    
    Note:
        - Engine must be started before calling this function
        - Alembic must be installed (pip install alembic)
        - Connection string is automatically extracted from engine
    """
    if not ALEMBIC_AVAILABLE:
        raise DatabaseMigrationError(
            message="Alembic not installed. Install with: pip install alembic",
            operation="create_alembic_config"
        )
    
    if not engine.is_alive:
        raise DatabaseEngineError(
            message="Engine not started. Call engine.start() first.",
            engine_state="stopped",
            operation="create_alembic_config"
        )
    
    # Get connection string from engine
    connection_string = engine._connection_string
    
    # Create Alembic config
    alembic_cfg = AlembicConfigClass()
    
    # Set script location (ensure it's a string)
    alembic_cfg.set_main_option("script_location", str(script_location))
    
    # Set database URL
    alembic_cfg.set_main_option("sqlalchemy.url", connection_string)
    
    # Set version path separator (must be string)
    alembic_cfg.set_main_option("version_path_separator", str(version_path_separator))
    
    # Set file template (must be string)
    alembic_cfg.set_main_option("file_template", str(file_template))
    
    # Apply additional options
    for key, value in kwargs.items():
        try:
            alembic_cfg.set_main_option(key, str(value))
        except Exception as e:
            _logger.warning(f"Failed to set Alembic option '{key}': {e}")
    
    _logger.info(f"Alembic config created for database: {engine.config.db_name}")
    
    return alembic_cfg


def get_alembic_config_from_manager(
    manager: 'DatabaseManager',
    script_location: str = "alembic",
    **kwargs
) -> 'AlembicConfig':
    """Create Alembic config from DatabaseManager (convenience function).
    
    This is a convenience function that extracts the engine from a
    DatabaseManager instance and creates an Alembic config.
    
    Args:
        manager: DatabaseManager instance
        script_location: Alembic script location directory
        **kwargs: Additional Alembic config options
    
    Returns:
        AlembicConfig: Configured Alembic config instance
    
    Raises:
        DatabaseMigrationError: If Alembic is not installed
        DatabaseEngineError: Engine not started
    
    Examples:
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        >>> 
        >>> alembic_cfg = get_alembic_config_from_manager(manager)
    """
    return create_alembic_config(
        manager.engine,
        script_location=script_location,
        **kwargs
    )