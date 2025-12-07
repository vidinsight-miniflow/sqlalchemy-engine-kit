"""
VidInsight SQLAlchemy Engine Kit

Easy-to-use database session management and connection pooling for SQLAlchemy.
Production-ready with logging, monitoring, and comprehensive error handling.
"""

# Version
__version__ = "0.1.0"

# Config exports
from .config import (
    DatabaseConfig,
    DatabaseType,
    EngineConfig,
    get_database_config,
    get_sqlite_config,
    get_postgresql_config,
    get_mysql_config,
    DB_ENGINE_CONFIGS,
    ENV_LOADER_AVAILABLE,
    get_config_from_env,
    load_config_from_file,
)

# Engine exports
from .engine import (
    DatabaseEngine,
    DatabaseManager,
    get_database_manager,
    with_retry,
)

# Decorators exports
from .engine.decorators import (
    with_session,
    with_transaction_session as with_transaction,
    with_readonly_session,
    with_retry_session,
    inject_session,
)

# Core exports
from .core import (
    EngineKitError,
    InvalidInputError,
    DatabaseConfigError,
    DatabaseConfigurationError,
    DatabaseEngineErrorBase,
    DatabaseEngineError,
    DatabaseEngineNotStartedError,
    DatabaseEngineInitializationError,
    DatabaseSessionError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabasePoolError,
    DatabaseHealthError,
    DatabaseManagerError,
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
    DatabaseManagerResetError,
    DatabaseDecoratorError,
    DatabaseDecoratorSignatureError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorRetryError,
    DatabaseError,
    LoggerAdapter,
)

# Monitoring exports (conditional)
try:
    from .monitoring import (
        BaseMonitor,
        MetricType,
        NoOpMonitor,
        PrometheusMonitor,
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    PrometheusMonitor = None

# Models exports
from .models import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    model_to_dict,
    model_to_json,
    models_to_list,
)

# Repositories module not included in this version
REPOSITORIES_AVAILABLE = False
BaseRepository = None
QueryBuilder = None
bulk_insert = None
bulk_update = None
bulk_delete = None
bulk_upsert = None
PaginationResult = None
paginate_with_meta = None
with_relationships = None
eager_load = None

# Migrations exports (conditional)
try:
    from .migrations import (
        ALEMBIC_AVAILABLE,
        DatabaseMigrationError,
        MigrationManager,
        run_migrations,
        create_migration,
        get_current_revision,
        get_head_revision,
        upgrade_dry_run,
        upgrade_safe,
        init_alembic,
        init_alembic_auto,
    )
except ImportError:
    ALEMBIC_AVAILABLE = False
    DatabaseMigrationError = None
    MigrationManager = None
    run_migrations = None
    create_migration = None
    get_current_revision = None
    get_head_revision = None
    upgrade_dry_run = None
    upgrade_safe = None
    init_alembic = None
    init_alembic_auto = None

__all__ = [
    # Version
    '__version__',
    # Config
    'DatabaseConfig',
    'DatabaseType',
    'EngineConfig',
    'get_database_config',
    'get_sqlite_config',
    'get_postgresql_config',
    'get_mysql_config',
    'DB_ENGINE_CONFIGS',
    'ENV_LOADER_AVAILABLE',
    'get_config_from_env',
    'load_config_from_file',
    # Engine
    'DatabaseEngine',
    'DatabaseManager',
    'get_database_manager',
    'with_retry',
    # Decorators
    'with_session',
    'with_transaction',
    'with_readonly_session',
    'with_retry_session',
    'inject_session',
    # Core
    'EngineKitError',
    'InvalidInputError',
    'DatabaseConfigError',
    'DatabaseConfigurationError',
    'DatabaseEngineErrorBase',
    'DatabaseEngineError',
    'DatabaseEngineNotStartedError',
    'DatabaseEngineInitializationError',
    'DatabaseSessionError',
    'DatabaseConnectionError',
    'DatabaseQueryError',
    'DatabaseTransactionError',
    'DatabasePoolError',
    'DatabaseHealthError',
    'DatabaseManagerError',
    'DatabaseManagerNotInitializedError',
    'DatabaseManagerAlreadyInitializedError',
    'DatabaseManagerResetError',
    'DatabaseDecoratorError',
    'DatabaseDecoratorSignatureError',
    'DatabaseDecoratorManagerError',
    'DatabaseDecoratorRetryError',
    'DatabaseError',
    'LoggerAdapter',
    # Models
    'Base',
    'TimestampMixin',
    'SoftDeleteMixin',
    'AuditMixin',
    'model_to_dict',
    'model_to_json',
    'models_to_list',
    # Monitoring
    'BaseMonitor',
    'MetricType',
    'NoOpMonitor',
    'MONITORING_AVAILABLE',
    # Migrations
    'ALEMBIC_AVAILABLE',
    'DatabaseMigrationError',
    'MigrationManager',
    'run_migrations',
    'create_migration',
    'get_current_revision',
    'get_head_revision',
    'upgrade_dry_run',
    'upgrade_safe',
    'init_alembic',
    'init_alembic_auto',
]

# Repositories not included in this version
# Repository pattern will be available in future versions

# Add PrometheusMonitor if available
if MONITORING_AVAILABLE and PrometheusMonitor is not None:
    __all__.append('PrometheusMonitor')

