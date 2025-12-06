"""
Integration tests for monitoring
"""

import pytest
from sqlalchemy_engine_kit.monitoring import NoOpMonitor
from sqlalchemy_engine_kit.engine import DatabaseEngine
from sqlalchemy_engine_kit.config import DatabaseConfig


class TestNoOpMonitor:
    """Tests for NoOpMonitor."""
    
    def test_noop_monitor_initialization(self):
        """Test NoOpMonitor initialization."""
        monitor = NoOpMonitor()
        assert monitor is not None
    
    def test_noop_monitor_record_query_duration(self):
        """Test NoOpMonitor record_query_duration (no-op)."""
        monitor = NoOpMonitor()
        # Should not raise error
        monitor.record_query_duration("test_query", 1.5, True, "postgresql")
    
    def test_noop_monitor_record_error(self):
        """Test NoOpMonitor record_error (no-op)."""
        monitor = NoOpMonitor()
        # Should not raise error
        monitor.record_error("test_error", "postgresql")
    
    def test_noop_monitor_record_session_count(self):
        """Test NoOpMonitor record_session_count (no-op)."""
        monitor = NoOpMonitor()
        # Should not raise error
        monitor.record_session_count(5, "postgresql")
    
    def test_noop_monitor_record_connection_pool_stats(self):
        """Test NoOpMonitor record_connection_pool_stats (no-op)."""
        monitor = NoOpMonitor()
        # Should not raise error
        monitor.record_connection_pool_stats(
            pool_size=10,
            active=3,
            idle=5,
            overflow=2,
            db_type="postgresql"
        )


class TestMonitorIntegration:
    """Tests for monitor integration with DatabaseEngine."""
    
    def test_engine_with_noop_monitor(self, sqlite_memory_config):
        """Test DatabaseEngine with NoOpMonitor."""
        monitor = NoOpMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        assert engine._monitor is monitor
        
        # Should work without errors
        from sqlalchemy import text
        with engine.session_context() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        engine.stop()
    
    def test_engine_without_monitor(self, sqlite_memory_config):
        """Test DatabaseEngine without monitor (defaults to NoOpMonitor)."""
        engine = DatabaseEngine(sqlite_memory_config)
        engine.start()
        
        # Should default to NoOpMonitor
        assert engine._monitor is not None
        assert isinstance(engine._monitor, NoOpMonitor)
        
        engine.stop()


class TestPrometheusMonitor:
    """Tests for PrometheusMonitor (if available)."""
    
    def test_prometheus_monitor_availability(self):
        """Test if PrometheusMonitor is available."""
        try:
            from sqlalchemy_engine_kit.monitoring import PrometheusMonitor
            # If import succeeds, test basic functionality
            monitor = PrometheusMonitor()
            assert monitor is not None
        except ImportError:
            pytest.skip("Prometheus client not installed")
    
    def test_prometheus_monitor_integration(self, sqlite_memory_config):
        """Test PrometheusMonitor integration with engine."""
        try:
            from sqlalchemy_engine_kit.monitoring import PrometheusMonitor
            from sqlalchemy_engine_kit.engine import DatabaseEngine
            from prometheus_client import CollectorRegistry
            
            # Use a fresh registry to avoid duplicate metric errors between tests
            registry = CollectorRegistry()
            monitor = PrometheusMonitor(registry=registry)
            engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
            engine.start()
            
            assert engine._monitor is monitor
            
            # Should work without errors
            from sqlalchemy import text
            with engine.session_context() as session:
                result = session.execute(text("SELECT 1")).scalar()
                assert result == 1
            
            engine.stop()
        except ImportError:
            pytest.skip("Prometheus client not installed")
        except ValueError as e:
            # Handle duplicate metric errors (may occur if tests run in same process)
            if "Duplicated timeseries" in str(e):
                pytest.skip(f"Prometheus registry conflict: {e}")
            raise

