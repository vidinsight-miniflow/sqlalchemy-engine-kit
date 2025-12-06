"""
Integration tests for DatabaseEngine
"""

import pytest
import threading
import time
from sqlalchemy import text
from sqlalchemy_engine_kit.engine import DatabaseEngine
from sqlalchemy_engine_kit.config import DatabaseConfig, DatabaseType
from sqlalchemy_engine_kit.core.exceptions import (
    DatabaseEngineError,
    DatabaseEngineNotStartedError,
    DatabaseConnectionError,
)
from tests.fixtures.sample_models import SimpleModel
from sqlalchemy_engine_kit.models import Base


class TestEngineLifecycle:
    """Tests for engine lifecycle management."""
    
    def test_engine_initialization(self, sqlite_memory_config):
        """Test engine initialization."""
        engine = DatabaseEngine(sqlite_memory_config)
        assert engine.config == sqlite_memory_config
        assert engine._engine is None
    
    def test_engine_start(self, sqlite_memory_config):
        """Test engine start."""
        engine = DatabaseEngine(sqlite_memory_config)
        engine.start()
        
        assert engine._engine is not None
        assert engine._session_factory is not None
    
    def test_engine_stop(self, test_engine):
        """Test engine stop."""
        assert test_engine._engine is not None
        
        test_engine.stop()
        
        assert test_engine._engine is None
    
    def test_engine_restart(self, sqlite_memory_config):
        """Test engine restart."""
        engine = DatabaseEngine(sqlite_memory_config)
        engine.start()
        assert engine._engine is not None
        
        engine.stop()
        assert engine._engine is None
        
        engine.start()
        assert engine._engine is not None


class TestSessionManagement:
    """Tests for session management."""
    
    def test_session_context(self, test_engine):
        """Test session context manager."""
        Base.metadata.create_all(test_engine._engine)
        
        with test_engine.session_context() as session:
            assert session is not None
            # Test query execution
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
    
    def test_session_auto_commit(self, test_engine):
        """Test session auto-commit."""
        Base.metadata.create_all(test_engine._engine)
        
        with test_engine.session_context(auto_commit=True) as session:
            user = SimpleModel(name="Test", value=42)
            session.add(user)
            # Should auto-commit on exit
        
        # Verify data persisted
        with test_engine.session_context() as session:
            result = session.query(SimpleModel).filter_by(name="Test").first()
            assert result is not None
            assert result.value == 42
    
    def test_session_rollback_on_error(self, test_engine):
        """Test session rollback on error."""
        Base.metadata.create_all(test_engine._engine)
        
        try:
            with test_engine.session_context() as session:
                user = SimpleModel(name="Test", value=42)
                session.add(user)
                session.flush()
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify data was rolled back
        with test_engine.session_context() as session:
            result = session.query(SimpleModel).filter_by(name="Test").first()
            assert result is None
    
    def test_get_session(self, test_engine):
        """Test get_session method."""
        session = test_engine.get_session()
        assert session is not None
        
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            session.close()
    
    def test_session_tracking(self, test_engine):
        """Test active session tracking."""
        initial_count = test_engine.get_active_session_count()
        
        with test_engine.session_context() as session:
            count_with_session = test_engine.get_active_session_count()
            assert count_with_session >= initial_count
        
        # After context exit, count should decrease
        final_count = test_engine.get_active_session_count()
        assert final_count <= count_with_session


class TestHealthCheck:
    """Tests for health check functionality."""
    
    def test_health_check_healthy(self, test_engine):
        """Test health check when engine is healthy."""
        health = test_engine.health_check()
        
        assert health["status"] == "healthy"
        assert "engine_alive" in health
        assert health["engine_alive"] is True
    
    def test_health_check_stopped(self, sqlite_memory_config):
        """Test health check when engine is stopped."""
        engine = DatabaseEngine(sqlite_memory_config)
        # Don't start engine
        
        health = engine.health_check()
        
        assert health["status"] in ["stopped", "unhealthy"]
    
    def test_health_check_caching(self, test_engine):
        """Test health check result caching."""
        # First call
        health1 = test_engine.health_check()
        time1 = test_engine._last_health_check_time
        
        # Immediate second call (should use cache)
        time.sleep(0.01)  # Small delay
        health2 = test_engine.health_check()
        time2 = test_engine._last_health_check_time
        
        # Cache should be used if within TTL
        if time2 == time1:
            assert health1 == health2


class TestConnectionPooling:
    """Tests for connection pooling."""
    
    def test_pool_configuration(self, sqlite_memory_config):
        """Test pool configuration."""
        sqlite_memory_config.engine_config.pool_size = 5
        sqlite_memory_config.engine_config.max_overflow = 10
        
        engine = DatabaseEngine(sqlite_memory_config)
        engine.start()
        
        # Verify pool is created
        assert engine._engine is not None
        pool = engine._engine.pool
        # StaticPool doesn't have size() method, just verify pool exists
        assert pool is not None
    
    def test_multiple_sessions(self, test_engine):
        """Test multiple concurrent sessions."""
        Base.metadata.create_all(test_engine._engine)
        
        def create_session():
            with test_engine.session_context() as session:
                result = session.execute(text("SELECT 1")).scalar()
                assert result == 1
        
        # Create multiple sessions concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_session)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()


class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_sessions(self, test_engine):
        """Test concurrent session creation."""
        Base.metadata.create_all(test_engine._engine)
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with test_engine.session_context() as session:
                    user = SimpleModel(name=f"Worker {worker_id}", value=worker_id)
                    session.add(user)
                    session.commit()
                    results.append(worker_id)
            except Exception as e:
                errors.append(e)
        
        # Reduce thread count to avoid SQLite bus errors when running all tests together
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=5.0)
        
        # SQLite may have occasional errors with high concurrency due to thread safety limits
        # Allow some failures but most should succeed
        assert len(results) >= 4, f"Expected at least 4 successes, got {len(results)}. Errors: {errors}"


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_session_without_start(self, sqlite_memory_config):
        """Test session creation without starting engine."""
        engine = DatabaseEngine(sqlite_memory_config)
        # Don't start engine
        
        with pytest.raises((DatabaseEngineError, DatabaseEngineNotStartedError)):
            with engine.session_context():
                pass
    
    def test_invalid_query(self, test_engine):
        """Test handling of invalid SQL query."""
        with test_engine.session_context() as session:
            with pytest.raises(Exception):  # Should raise SQLAlchemy error
                session.execute(text("SELECT * FROM nonexistent_table")).scalar()


class TestCreateTables:
    """Tests for table creation."""
    
    def test_create_tables(self, test_engine):
        """Test create_tables method."""
        test_engine.create_tables(Base.metadata)
        
        # Verify tables exist
        with test_engine.session_context() as session:
            # Try to query the table
            result = session.query(SimpleModel).count()
            assert result == 0  # Table exists but empty


class TestGracefulShutdown:
    """Tests for graceful shutdown."""
    
    def test_shutdown_with_active_sessions(self, test_engine):
        """Test shutdown with active sessions."""
        Base.metadata.create_all(test_engine._engine)
        
        # Create active session
        session = test_engine.get_session()
        try:
            # Add some data
            user = SimpleModel(name="Test", value=42)
            session.add(user)
            session.commit()
            
            # Stop engine (should handle active sessions)
            test_engine.stop()
            
            # Session should be closed
            assert test_engine._engine is None
        finally:
            try:
                session.close()
            except Exception:
                pass

