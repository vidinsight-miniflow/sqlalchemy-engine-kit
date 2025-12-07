"""
Configuration module for engine-kit
"""

from .database_config import DatabaseConfig
from .database_type import DatabaseType
from .engine_config import EngineConfig
from .engine_config_presets import DB_ENGINE_CONFIGS
from .factories import (
    get_database_config,
    get_sqlite_config,
    get_postgresql_config,
    get_mysql_config,
)

# Optional env loader (requires python-dotenv)
try:
    from .env_loader import (
        get_config_from_env,
        load_config_from_file,
        ENV_LOADER_AVAILABLE,
    )
    _has_env_loader = True
except ImportError:
    ENV_LOADER_AVAILABLE = False
    def get_config_from_env(*args, **kwargs):
        raise ImportError("python-dotenv not installed. Install with: pip install python-dotenv")
    def load_config_from_file(*args, **kwargs):
        raise ImportError("python-dotenv not installed. Install with: pip install python-dotenv")
    _has_env_loader = False

__all__ = [
    'DatabaseConfig',
    'DatabaseType',
    'EngineConfig',
    'DB_ENGINE_CONFIGS',
    'get_database_config',
    'get_sqlite_config',
    'get_postgresql_config',
    'get_mysql_config',
    'ENV_LOADER_AVAILABLE',
    'get_config_from_env',
    'load_config_from_file',
]

