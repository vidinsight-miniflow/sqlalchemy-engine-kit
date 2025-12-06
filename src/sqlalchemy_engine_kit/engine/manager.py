"""
Database Manager Module - Singleton Pattern ile Engine Yönetimi

Bu modül, application-wide database engine yönetimi için singleton pattern
implementasyonu sağlar. Thread-safe ve production-ready bir yapı sunar.
"""

import threading
from typing import Optional, Any
from ..config import DatabaseConfig
from ..monitoring import BaseMonitor, NoOpMonitor
from ..core.exceptions import (
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
)
from ..core.logging import LoggerAdapter
from .engine import DatabaseEngine


_logger = LoggerAdapter.get_logger(__name__)


class DatabaseManager:
    """Singleton pattern ile uygulama genelinde tek database engine instance'ı yönetir.
    
    Bu sınıf, thread-safe singleton pattern kullanarak uygulama genelinde
    tek bir DatabaseEngine instance'ı yönetir. Production-ready bir yapı
    sunar ve connection pooling verimliliği sağlar.
    
    Thread Safety:
        - Double-checked locking pattern kullanır
        - Thread-safe initialization
        - Thread-safe singleton access
    
    Lifecycle:
        1. __new__(): Singleton instance oluşturur
        2. initialize(): Engine'i başlatır
        3. start(): Engine'i başlatır (auto_start=False ise)
        4. stop(): Engine'i durdurur
        5. reset(): Engine'i temizler
    
    Examples:
        >>> # Initialize at application startup
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        >>> 
        >>> # Access anywhere in application
        >>> manager = DatabaseManager()  # Same instance
        >>> engine = manager.engine
        >>> 
        >>> # Use with decorators
        >>> from sqlalchemy_engine_kit import with_session
        >>> @with_session()
        >>> def my_function(session):
        ...     # Uses manager.engine automatically
        ...     pass
    """
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    _is_resetting = False
    
    def __new__(cls):
        """Singleton pattern - her zaman aynı instance'ı döndürür."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._engine: Optional[DatabaseEngine] = None
                    cls._instance._config: Optional[DatabaseConfig] = None
                    cls._instance._monitor: Optional[BaseMonitor] = None
        return cls._instance
    
    def __init__(self):
        """Initialize DatabaseManager (singleton pattern - instance zaten oluşturulmuş)."""
        # Singleton pattern - __new__ zaten instance oluşturdu
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized
    
    @property
    def engine(self) -> DatabaseEngine:
        """Get DatabaseEngine instance.
        
        Raises:
            DatabaseManagerNotInitializedError: If not initialized
        """
        if not self._initialized or self._engine is None:
            raise DatabaseManagerNotInitializedError(
                message="DatabaseManager not initialized. Call initialize() first."
            )
        return self._engine
    
    def initialize(
        self,
        config: DatabaseConfig,
        auto_start: bool = True,
        create_tables: Any = None,
        force_reinitialize: bool = False,
        monitor: Optional[BaseMonitor] = None
    ) -> None:
        """Initialize database engine.
        
        Args:
            config: Database configuration
            auto_start: Automatically start engine after initialization
            create_tables: Metadata object to create tables (optional)
            force_reinitialize: Force reinitialization if already initialized
            monitor: Custom monitor instance (default: NoOpMonitor)
        
        Raises:
            DatabaseManagerAlreadyInitializedError: If already initialized and force_reinitialize=False
        """
        if self._initialized and not force_reinitialize:
            raise DatabaseManagerAlreadyInitializedError(
                message="DatabaseManager already initialized. Use force_reinitialize=True to reinitialize."
            )
        
        # Reset if already initialized
        if self._initialized:
            self._reset_internal()
        
        # Store config and monitor
        self._config = config
        self._monitor = monitor or NoOpMonitor()
        
        # Create engine
        self._engine = DatabaseEngine(config, monitor=self._monitor)
        
        # Mark as initialized
        self._initialized = True
        
        # Auto start if requested
        if auto_start:
            self.start()
        
        # Create tables if requested
        if create_tables is not None:
            if self._engine._engine is None:
                self.start()
            self._engine._engine.create_all(create_tables)
        
        _logger.info("DatabaseManager initialized successfully")
    
    def start(self) -> None:
        """Start database engine.
        
        Raises:
            DatabaseManagerNotInitializedError: If not initialized
        """
        if not self._initialized or self._engine is None:
            raise DatabaseManagerNotInitializedError(
                message="DatabaseManager not initialized. Call initialize() first."
            )
        
        self._engine.start()
        _logger.info("DatabaseManager engine started")
    
    def stop(self) -> None:
        """Stop database engine (idempotent)."""
        if self._engine is not None:
            try:
                self._engine.stop()
                _logger.info("DatabaseManager engine stopped")
            except Exception as e:
                _logger.warning(f"Error stopping engine: {e}")
    
    def reset(self, full_reset: bool = False) -> None:
        """Reset database manager.
        
        Args:
            full_reset: If True, also reset singleton instance
        """
        self._reset_internal()
        
        if full_reset:
            with self._lock:
                DatabaseManager._instance = None
                DatabaseManager._is_resetting = False
    
    def _reset_internal(self) -> None:
        """Internal reset method."""
        if self._is_resetting:
            return
        
        self._is_resetting = True
        
        try:
            if self._engine is not None:
                self.stop()
                self._engine = None
            
            self._initialized = False
            self._config = None
            self._monitor = None
        finally:
            self._is_resetting = False
    
    def reload_config(
        self,
        config: DatabaseConfig,
        restart: bool = True
    ) -> None:
        """Reload configuration and optionally restart engine.
        
        Args:
            config: New database configuration
            restart: Restart engine after reload
        """
        if not self._initialized:
            self.initialize(config, auto_start=restart)
            return
        
        # Stop current engine
        self.stop()
        
        # Update config
        self._config = config
        
        # Create new engine
        self._engine = DatabaseEngine(config, monitor=self._monitor or NoOpMonitor())
        
        # Restart if requested
        if restart:
            self.start()
        
        _logger.info("DatabaseManager configuration reloaded")
    
    @classmethod
    def get_instance(
        cls,
        config: Optional[DatabaseConfig] = None,
        auto_start: bool = True
    ) -> 'DatabaseManager':
        """Get singleton instance.
        
        Args:
            config: Database configuration (required on first call)
            auto_start: Automatically start engine
        
        Returns:
            DatabaseManager: Singleton instance
        
        Raises:
            DatabaseManagerNotInitializedError: If not initialized and no config provided
        """
        instance = cls()
        
        if not instance._initialized:
            if config is None:
                raise DatabaseManagerNotInitializedError(
                    message="DatabaseManager not initialized. Provide config on first call."
                )
            instance.initialize(config, auto_start=auto_start)
        
        return instance


def get_database_manager(
    config: Optional[DatabaseConfig] = None,
    auto_start: bool = True
) -> DatabaseManager:
    """Convenience function to get DatabaseManager instance.
    
    Args:
        config: Database configuration (optional)
        auto_start: Automatically start engine
    
    Returns:
        DatabaseManager: Singleton instance
    """
    return DatabaseManager.get_instance(config, auto_start)

