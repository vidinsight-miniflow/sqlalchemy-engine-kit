"""
Shared fixtures and test configuration for engine-kit tests
"""

import pytest
import tempfile
import os
from typing import Generator

from sqlalchemy_engine_kit.config import DatabaseConfig, DatabaseType, EngineConfig
from sqlalchemy_engine_kit.engine import DatabaseEngine, DatabaseManager
from sqlalchemy_engine_kit.monitoring import NoOpMonitor
from sqlalchemy.orm import Session


@pytest.fixture
def sqlite_memory_config() -> DatabaseConfig:
    """In-memory SQLite configuration for fast unit tests."""
    return DatabaseConfig.for_testing(":memory:")


@pytest.fixture
def sqlite_file_config() -> DatabaseConfig:
    """File-based SQLite configuration for persistence tests."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    config = DatabaseConfig.for_testing(path)
    
    yield config
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def test_engine(sqlite_memory_config: DatabaseConfig) -> Generator[DatabaseEngine, None, None]:
    """Pre-configured DatabaseEngine instance."""
    engine = DatabaseEngine(sqlite_memory_config, monitor=NoOpMonitor())
    engine.start()
    
    yield engine
    
    # Cleanup
    if engine._engine is not None:
        engine.stop()


@pytest.fixture
def test_manager(sqlite_memory_config: DatabaseConfig) -> Generator[DatabaseManager, None, None]:
    """Pre-configured DatabaseManager instance."""
    # Reset singleton before test
    DatabaseManager._instance = None
    DatabaseManager._is_resetting = False
    
    manager = DatabaseManager()
    manager.initialize(sqlite_memory_config, auto_start=True)
    
    yield manager
    
    # Cleanup
    try:
        manager.reset(full_reset=True)
    except Exception:
        pass


@pytest.fixture
def test_session(test_engine: DatabaseEngine) -> Generator[Session, None, None]:
    """SQLAlchemy session fixture."""
    with test_engine.session_context() as session:
        yield session


@pytest.fixture
def mock_monitor():
    """Mock monitoring instance."""
    return NoOpMonitor()


@pytest.fixture(autouse=True)
def cleanup_manager():
    """Auto-cleanup DatabaseManager singleton after each test."""
    yield
    # Reset singleton after test
    try:
        if DatabaseManager._instance is not None:
            DatabaseManager._instance.reset(full_reset=True)
    except Exception:
        pass
    DatabaseManager._instance = None
    DatabaseManager._is_resetting = False

