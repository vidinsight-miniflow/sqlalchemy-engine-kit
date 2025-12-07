"""
Integration tests for DatabaseManager
"""

import pytest
import threading
from sqlalchemy_engine_kit.engine import DatabaseManager
from sqlalchemy_engine_kit.config import DatabaseConfig, DatabaseType
from sqlalchemy_engine_kit.core.exceptions import (
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
)


class TestSingletonPattern:
    """Tests for singleton pattern enforcement."""
    
    def test_singleton_instance(self, sqlite_memory_config):
        """Test that DatabaseManager returns same instance."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager1 = DatabaseManager()
        manager2 = DatabaseManager()
        
        assert manager1 is manager2
        assert id(manager1) == id(manager2)
    
    def test_singleton_after_initialize(self, sqlite_memory_config):
        """Test singleton after initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager1 = DatabaseManager()
        manager1.initialize(sqlite_memory_config, auto_start=True)
        
        manager2 = DatabaseManager()
        
        assert manager1 is manager2
        assert manager2.is_initialized


class TestInitialization:
    """Tests for manager initialization."""
    
    def test_initialize(self, sqlite_memory_config):
        """Test manager initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        assert manager.is_initialized
        assert manager.engine is not None
        assert manager.engine._engine is not None
    
    def test_initialize_without_auto_start(self, sqlite_memory_config):
        """Test initialization without auto_start."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=False)
        
        assert manager.is_initialized
        assert manager.engine is not None
        assert manager.engine._engine is None
    
    def test_double_initialize_raises_error(self, sqlite_memory_config):
        """Test that double initialization raises error."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        with pytest.raises(DatabaseManagerAlreadyInitializedError):
            manager.initialize(sqlite_memory_config, auto_start=True)
    
    def test_force_reinitialize(self, sqlite_memory_config):
        """Test force reinitialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        # Force reinitialize
        manager.initialize(sqlite_memory_config, auto_start=True, force_reinitialize=True)
        
        assert manager.is_initialized


class TestManagerLifecycle:
    """Tests for manager lifecycle."""
    
    def test_manager_start_stop(self, sqlite_memory_config):
        """Test manager start and stop."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=False)
        
        manager.start()
        assert manager.engine._engine is not None
        
        manager.stop()
        assert manager.engine._engine is None
    
    def test_reset(self, sqlite_memory_config):
        """Test manager reset."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        assert manager.is_initialized
        
        manager.reset()
        
        assert not manager.is_initialized
        assert manager._engine is None
    
    def test_reset_full(self, sqlite_memory_config):
        """Test full reset."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager1 = DatabaseManager()
        manager1.initialize(sqlite_memory_config, auto_start=True)
        
        manager1.reset()
        
        # After full reset, new instance should be created
        manager2 = DatabaseManager()
        assert manager2 is not manager1 or not manager2.is_initialized


class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_initialization(self, sqlite_memory_config):
        """Test concurrent initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        errors = []
        results = []
        
        def init_manager():
            try:
                manager = DatabaseManager()
                manager.initialize(sqlite_memory_config, auto_start=True)
                results.append(manager.is_initialized)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=init_manager)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have no errors (or only AlreadyInitializedError)
        assert len([e for e in errors if not isinstance(e, DatabaseManagerAlreadyInitializedError)]) == 0
        # At least one should succeed
        assert len(results) > 0
    
    def test_concurrent_access(self, sqlite_memory_config):
        """Test concurrent access to manager."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        def access_engine():
            engine = manager.engine
            assert engine is not None
            assert engine._engine is not None
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_engine)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_access_before_initialize(self):
        """Test accessing engine before initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        
        with pytest.raises(DatabaseManagerNotInitializedError):
            _ = manager.engine
    
    def test_start_before_initialize(self, sqlite_memory_config):
        """Test starting before initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        
        with pytest.raises(DatabaseManagerNotInitializedError):
            manager.start()
    
    def test_stop_before_initialize(self):
        """Test stopping before initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        
        # Should not raise error (idempotent)
        manager.stop()


class TestGetInstance:
    """Tests for get_instance class method."""
    
    def test_get_instance_with_config(self, sqlite_memory_config):
        """Test get_instance with config."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager.get_instance(sqlite_memory_config, auto_start=True)
        
        assert manager.is_initialized
        assert manager.engine._engine is not None
    
    def test_get_instance_without_config(self, sqlite_memory_config):
        """Test get_instance without config (after initialization)."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        # Initialize first
        manager1 = DatabaseManager.get_instance(sqlite_memory_config, auto_start=True)
        
        # Get instance without config
        manager2 = DatabaseManager.get_instance()
        
        assert manager1 is manager2
        assert manager2.is_initialized
    
    def test_get_instance_before_init(self):
        """Test get_instance before initialization."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        with pytest.raises(DatabaseManagerNotInitializedError):
            DatabaseManager.get_instance()


class TestReloadConfig:
    """Tests for reload_config method."""
    
    def test_reload_config(self, sqlite_memory_config):
        """Test reloading configuration."""
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True)
        
        # Create new config
        new_config = DatabaseConfig.for_testing("new_test.db")
        
        manager.reload_config(new_config, restart=True)
        
        assert manager.is_initialized
        assert manager.engine._engine is not None

