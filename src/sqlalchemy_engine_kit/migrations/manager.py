"""
Migration Manager

This module provides a high-level interface for managing Alembic migrations
with DatabaseEngine integration.
"""

from typing import Optional, List, Dict, Any, Iterator, TYPE_CHECKING

from ..core.logging import LoggerAdapter
from .config import create_alembic_config, ALEMBIC_AVAILABLE
from .exceptions import DatabaseMigrationError

if TYPE_CHECKING:
    from ..engine.engine import DatabaseEngine
    from alembic.config import Config as AlembicConfig

_logger = LoggerAdapter.get_logger(__name__)

# Import Alembic components if available
if ALEMBIC_AVAILABLE:
    from alembic import command
    from alembic.config import Config as AlembicConfigClass
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
else:
    AlembicConfigClass = None
    command = None
    ScriptDirectory = None
    MigrationContext = None


class MigrationManager:
    """Alembic migration manager with DatabaseEngine integration.
    
    This class provides a high-level interface for managing Alembic migrations.
    It integrates seamlessly with DatabaseEngine and DatabaseManager instances.
    
    Features:
        - Upgrade/downgrade migrations
        - Create new migrations
        - Check current and head revisions
        - Migration history
        - Database stamping
        - Safe upgrade with verification
        - Dry-run support
    
    Examples:
        >>> # Basic usage
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        >>> 
        >>> migration_mgr = MigrationManager(manager.engine)
        >>> migration_mgr.upgrade("head")
        >>> 
        >>> # Create new migration
        >>> migration_mgr.create_migration("add_user_table", autogenerate=True)
        >>> 
        >>> # Check revisions
        >>> current = migration_mgr.get_current_revision()
        >>> head = migration_mgr.get_head_revision()
        >>> print(f"Current: {current}, Head: {head}")
    
    Note:
        - Alembic must be installed (pip install alembic)
        - Engine must be started before using migration operations
        - Script location defaults to "alembic" directory
    """
    
    def __init__(
        self,
        engine: 'DatabaseEngine',
        script_location: str = "alembic"
    ):
        """Initialize MigrationManager.
        
        Args:
            engine: DatabaseEngine instance (must be started)
            script_location: Alembic script location directory (default: "alembic")
        
        Raises:
            DatabaseMigrationError: If Alembic is not installed
        """
        if not ALEMBIC_AVAILABLE:
            raise DatabaseMigrationError(
                message="Alembic not installed. Install with: pip install alembic",
                operation="__init__"
            )
        
        self.engine = engine
        self.script_location = str(script_location)
        self._config: Optional['AlembicConfig'] = None
        self._logger = LoggerAdapter.get_logger(__name__)
    
    def _ensure_engine_started(self, operation: str) -> None:
        """Ensure engine is started before operation.
        
        Args:
            operation: Name of the operation for error message
            
        Raises:
            DatabaseMigrationError: If engine is not started
        """
        if not self.engine.is_alive:
            # Import here to avoid circular imports
            from ..core.exceptions import DatabaseEngineError
            raise DatabaseEngineError(
                message="Engine not started. Call engine.start() first.",
                engine_state="stopped",
                operation=operation
            )
    
    @property
    def config(self) -> 'AlembicConfig':
        """Get or create Alembic config.
        
        Returns:
            AlembicConfig: Configured Alembic config instance
        
        Raises:
            DatabaseMigrationError: If config creation fails
        """
        if self._config is None:
            self._config = create_alembic_config(
                self.engine,
                script_location=self.script_location
            )
        return self._config
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision.
        
        This method queries the database to determine which migration revision
        is currently applied. Uses SQLAlchemy 2.0 compatible approach by
        directly querying the alembic_version table.
        
        Returns:
            Current revision string or None if no migrations have been applied
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Failed to get current revision
        
        Examples:
            >>> current = migration_mgr.get_current_revision()
            >>> if current is None:
            ...     print("No migrations applied yet")
            >>> else:
            ...     print(f"Current revision: {current}")
        
        Note:
            - SQLAlchemy 2.0 compatible implementation
            - Directly queries alembic_version table
            - Returns None if table doesn't exist (no migrations applied)
        """
        self._ensure_engine_started("get_current_revision")
        
        try:
            from sqlalchemy import text, inspect
            
            with self.engine._engine.connect() as connection:
                # Check if alembic_version table exists
                inspector = inspect(connection)
                table_names = inspector.get_table_names()
                
                if 'alembic_version' not in table_names:
                    return None
                
                # Query alembic_version table directly (SQLAlchemy 2.0 compatible)
                result = connection.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                row = result.fetchone()
                
                if row:
                    return row[0]
                else:
                    return None
                    
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Failed to get current revision: {e}",
                operation="get_current_revision",
                original_error=e
            )
    
    def get_head_revision(self) -> Optional[str]:
        """Get head revision (latest migration).
        
        This method reads the Alembic script directory to determine the
        latest (head) migration revision.
        
        Returns:
            Head revision string or None if no migrations exist
        
        Raises:
            DatabaseMigrationError: Failed to get head revision
        
        Examples:
            >>> head = migration_mgr.get_head_revision()
            >>> if head is None:
            ...     print("No migrations found")
            >>> else:
            ...     print(f"Head revision: {head}")
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            head = script.get_current_head()
            return head if head else None
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Failed to get head revision: {e}",
                operation="get_head_revision",
                original_error=e
            )
    
    def is_up_to_date(self) -> bool:
        """Check if database is up to date with latest migration.
        
        Returns:
            True if current revision equals head revision
        
        Examples:
            >>> if migration_mgr.is_up_to_date():
            ...     print("Database is up to date")
            >>> else:
            ...     print("Migrations pending")
        """
        current = self.get_current_revision()
        head = self.get_head_revision()
        
        if head is None:
            return True  # No migrations exist
        
        return current == head
    
    def get_pending_revisions(self) -> List[str]:
        """Get list of pending migration revisions.
        
        Returns:
            List of revision strings that need to be applied
        
        Examples:
            >>> pending = migration_mgr.get_pending_revisions()
            >>> if pending:
            ...     print(f"Pending migrations: {pending}")
        """
        try:
            current = self.get_current_revision()
            script = ScriptDirectory.from_config(self.config)
            
            pending = []
            for rev in script.walk_revisions():
                if current is None or rev.revision != current:
                    pending.append(rev.revision)
                else:
                    break
            
            return list(reversed(pending))
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Failed to get pending revisions: {e}",
                operation="get_pending_revisions",
                original_error=e
            )
    
    def upgrade(self, revision: str = "head", **kwargs) -> None:
        """Upgrade database to specified revision.
        
        This method runs Alembic upgrade command to apply migrations up to
        the specified revision.
        
        Args:
            revision: Target revision (default: "head" for latest)
            **kwargs: Additional Alembic upgrade options
                - sql: If True, output SQL without executing (dry-run)
                - tag: Tag to apply to migration
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Migration upgrade failed
        
        Examples:
            >>> # Upgrade to latest
            >>> migration_mgr.upgrade("head")
            >>> 
            >>> # Upgrade to specific revision
            >>> migration_mgr.upgrade("abc123")
            >>> 
            >>> # Upgrade with tag
            >>> migration_mgr.upgrade("head", tag="v1.0.0")
        """
        self._ensure_engine_started("upgrade")
        
        try:
            self._logger.info(f"Upgrading database to revision: {revision}")
            command.upgrade(self.config, revision, **kwargs)
            self._logger.info(f"Database upgraded successfully to revision: {revision}")
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Migration upgrade failed: {e}",
                operation="upgrade",
                revision=revision,
                original_error=e
            )
    
    def upgrade_safe(self, revision: str = "head", verify: bool = True) -> bool:
        """Safe upgrade with verification.
        
        This method performs an upgrade with additional safety checks
        and optional verification that the upgrade succeeded.
        
        Args:
            revision: Target revision (default: "head" for latest)
            verify: Verify upgrade success (default: True)
        
        Returns:
            True if upgrade successful
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Migration upgrade failed or verification failed
        
        Examples:
            >>> # Safe upgrade with verification
            >>> success = migration_mgr.upgrade_safe("head", verify=True)
            >>> if success:
            ...     print("Upgrade completed and verified")
            
            >>> # Safe upgrade without verification
            >>> migration_mgr.upgrade_safe("head", verify=False)
        """
        self._ensure_engine_started("upgrade_safe")
        
        try:
            # Get current state before upgrade
            current_before = self.get_current_revision()
            target = revision if revision != "head" else self.get_head_revision()
            
            self._logger.info(f"Safe upgrade: {current_before} -> {target}")
            
            # Perform upgrade
            self.upgrade(revision)
            
            # Verify if requested
            if verify:
                current_after = self.get_current_revision()
                
                if revision == "head":
                    head = self.get_head_revision()
                    if current_after != head:
                        raise DatabaseMigrationError(
                            message=f"Upgrade verification failed: expected {head}, got {current_after}",
                            operation="upgrade_safe",
                            revision=revision
                        )
                else:
                    if current_after != revision:
                        raise DatabaseMigrationError(
                            message=f"Upgrade verification failed: expected {revision}, got {current_after}",
                            operation="upgrade_safe",
                            revision=revision
                        )
                
                self._logger.info(f"Upgrade verified: now at revision {current_after}")
            
            return True
            
        except DatabaseMigrationError:
            raise
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Safe upgrade failed: {e}",
                operation="upgrade_safe",
                revision=revision,
                original_error=e
            )
    
    def upgrade_dry_run(self, revision: str = "head") -> str:
        """Dry-run upgrade - show SQL that would be executed.
        
        This method performs a dry-run upgrade, showing the SQL statements
        that would be executed without actually applying them.
        
        Args:
            revision: Target revision (default: "head" for latest)
        
        Returns:
            SQL statements that would be executed (as string)
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Dry-run failed
        
        Examples:
            >>> # See what would be executed
            >>> sql = migration_mgr.upgrade_dry_run("head")
            >>> print(sql)
            >>> 
            >>> # Review before applying
            >>> if review_sql(sql):
            ...     migration_mgr.upgrade("head")
        """
        self._ensure_engine_started("upgrade_dry_run")
        
        try:
            from io import StringIO
            import sys
            
            # Capture stdout to capture SQL output
            old_stdout = sys.stdout
            sql_output = StringIO()
            sys.stdout = sql_output
            
            try:
                self._logger.info(f"Dry-run upgrade to revision: {revision}")
                command.upgrade(self.config, revision, sql=True)
                sql_statements = sql_output.getvalue()
                self._logger.info("Dry-run completed successfully")
                return sql_statements
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Dry-run upgrade failed: {e}",
                operation="upgrade_dry_run",
                revision=revision,
                original_error=e
            )
    
    def downgrade(self, revision: str, **kwargs) -> None:
        """Downgrade database to specified revision.
        
        This method runs Alembic downgrade command to rollback migrations
        to the specified revision.
        
        ⚠️ WARNING: Downgrading can cause data loss!
        
        Args:
            revision: Target revision to downgrade to
            **kwargs: Additional Alembic downgrade options
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Migration downgrade failed
        
        Examples:
            >>> # Downgrade one revision
            >>> migration_mgr.downgrade("-1")
            >>> 
            >>> # Downgrade to specific revision
            >>> migration_mgr.downgrade("abc123")
            >>> 
            >>> # Downgrade to base (remove all migrations)
            >>> migration_mgr.downgrade("base")
        """
        self._ensure_engine_started("downgrade")
        
        try:
            self._logger.warning(f"Downgrading database to revision: {revision}")
            command.downgrade(self.config, revision, **kwargs)
            self._logger.info(f"Database downgraded successfully to revision: {revision}")
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Migration downgrade failed: {e}",
                operation="downgrade",
                revision=revision,
                original_error=e
            )
    
    def create_migration(
        self,
        message: str,
        autogenerate: bool = True,
        **kwargs
    ) -> str:
        """Create new migration.
        
        This method creates a new Alembic migration file. If autogenerate
        is True, it will automatically detect model changes.
        
        Args:
            message: Migration message/description
            autogenerate: Auto-generate migration from models (default: True)
            **kwargs: Additional Alembic revision options
        
        Returns:
            Created migration file path (informational)
        
        Raises:
            DatabaseMigrationError: Migration creation failed
        
        Examples:
            >>> # Auto-generate migration
            >>> migration_mgr.create_migration("add_user_table", autogenerate=True)
            >>> 
            >>> # Manual migration
            >>> migration_mgr.create_migration("custom_migration", autogenerate=False)
        """
        try:
            self._logger.info(f"Creating migration: {message}")
            command.revision(
                self.config,
                message=message,
                autogenerate=autogenerate,
                **kwargs
            )
            self._logger.info(f"Migration created successfully: {message}")
            return f"Migration '{message}' created in {self.script_location}/versions/"
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Migration creation failed: {e}",
                operation="create_migration",
                migration_message=message,
                original_error=e
            )
    
    def history(self, verbose: bool = False) -> Iterator[Dict[str, Any]]:
        """Get migration history as generator (memory efficient).
        
        This method retrieves the complete migration history from the
        Alembic script directory. Returns a generator for memory efficiency,
        especially useful for large migration histories.
        
        Args:
            verbose: Include detailed information (default: False)
        
        Yields:
            Dict[str, Any]: Migration history entries with revision, down_revision, doc, etc.
        
        Raises:
            DatabaseMigrationError: Failed to get migration history
        
        Examples:
            >>> # Get history (generator - memory efficient)
            >>> for entry in migration_mgr.history():
            ...     print(f"{entry['revision']}: {entry['doc']}")
            
            >>> # Convert to list if needed
            >>> history_list = list(migration_mgr.history())
            
            >>> # Verbose mode
            >>> for entry in migration_mgr.history(verbose=True):
            ...     print(f"{entry['revision']}: {entry['doc']} (head: {entry['is_head']})")
        
        Note:
            - Returns generator for memory efficiency (lazy evaluation)
            - Use list() to convert to list if needed
            - Memory efficient for large migration histories
        """
        try:
            script = ScriptDirectory.from_config(self.config)
            history = script.walk_revisions()
            
            for rev in history:
                entry = {
                    "revision": rev.revision,
                    "down_revision": rev.down_revision,
                    "doc": rev.doc or "",
                    "branch_labels": list(rev.branch_labels) if rev.branch_labels else [],
                }
                if verbose:
                    entry.update({
                        "module_path": str(rev.module_path) if hasattr(rev, 'module_path') and rev.module_path else None,
                        "is_head": rev.is_head if hasattr(rev, 'is_head') else False,
                        "is_branch_point": rev.is_branch_point if hasattr(rev, 'is_branch_point') else False,
                    })
                yield entry
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Failed to get migration history: {e}",
                operation="history",
                original_error=e
            )
    
    def stamp(self, revision: str) -> None:
        """Stamp database with revision (without running migrations).
        
        This method marks the database as being at a specific revision
        without actually running the migrations. Useful for initializing
        a database that already has the schema.
        
        Args:
            revision: Revision to stamp database with
        
        Raises:
            DatabaseEngineError: Engine not started
            DatabaseMigrationError: Stamping failed
        
        Examples:
            >>> # Stamp database as being at head
            >>> migration_mgr.stamp("head")
            >>> 
            >>> # Stamp with specific revision
            >>> migration_mgr.stamp("abc123")
        """
        self._ensure_engine_started("stamp")
        
        try:
            self._logger.info(f"Stamping database with revision: {revision}")
            command.stamp(self.config, revision)
            self._logger.info(f"Database stamped successfully with revision: {revision}")
        except Exception as e:
            raise DatabaseMigrationError(
                message=f"Stamping failed: {e}",
                operation="stamp",
                revision=revision,
                original_error=e
            )