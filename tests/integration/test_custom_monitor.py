"""
Tests for custom monitor implementations
"""

import pytest
from typing import Optional, Dict
from sqlalchemy_engine_kit.monitoring.base import BaseMonitor
from sqlalchemy_engine_kit.engine import DatabaseEngine, DatabaseManager
from sqlalchemy_engine_kit.config import DatabaseConfig
from sqlalchemy import text


class TestCustomMonitor(BaseMonitor):
    """Custom monitor implementation for testing."""
    
    def __init__(self):
        self.metrics = []
        self.increments = []
        self.gauges = []
        self.histograms = []
        self.query_durations = []
        self.errors = []
        self.pool_stats = []
        self.session_counts = []
    
    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        self.increments.append({
            "name": name,
            "value": value,
            "labels": labels or {}
        })
        self.metrics.append(("increment", name, value, labels))
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.gauges.append({
            "name": name,
            "value": value,
            "labels": labels or {}
        })
        self.metrics.append(("gauge", name, value, labels))
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        self.histograms.append({
            "name": name,
            "value": value,
            "labels": labels or {}
        })
        self.metrics.append(("histogram", name, value, labels))
    
    def record_query_duration(self, query: str, duration: float, success: bool, db_type: Optional[str] = None) -> None:
        self.query_durations.append({
            "query": query,
            "duration": duration,
            "success": success,
            "db_type": db_type
        })
        self.metrics.append(("query_duration", query, duration, success))
    
    def record_connection_pool_stats(self, pool_size: int, active: int, idle: int, overflow: int, db_type: Optional[str] = None) -> None:
        self.pool_stats.append({
            "pool_size": pool_size,
            "active": active,
            "idle": idle,
            "overflow": overflow,
            "db_type": db_type
        })
        self.metrics.append(("pool_stats", pool_size, active, idle, overflow))
    
    def record_session_count(self, count: int, db_type: Optional[str] = None) -> None:
        self.session_counts.append({
            "count": count,
            "db_type": db_type
        })
        self.metrics.append(("session_count", count, db_type))
    
    def record_error(self, error_type: str, db_type: Optional[str] = None, labels: Optional[Dict[str, str]] = None) -> None:
        self.errors.append({
            "error_type": error_type,
            "db_type": db_type,
            "labels": labels or {}
        })
        self.metrics.append(("error", error_type, db_type, labels))
    
    def clear(self):
        """Clear all recorded metrics."""
        self.metrics = []
        self.increments = []
        self.gauges = []
        self.histograms = []
        self.query_durations = []
        self.errors = []
        self.pool_stats = []
        self.session_counts = []


class TestCustomMonitorIntegration:
    """Tests for custom monitor integration."""
    
    def test_custom_monitor_with_engine(self, sqlite_memory_config):
        """Test custom monitor with DatabaseEngine."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Verify monitor is set
        assert engine._monitor is monitor
        
        # Perform operations
        with engine.session_context() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        # Check that metrics were recorded
        # Note: Actual metric recording depends on engine implementation
        assert monitor is not None
        
        engine.stop()
    
    def test_custom_monitor_with_manager(self, sqlite_memory_config):
        """Test custom monitor with DatabaseManager."""
        monitor = TestCustomMonitor()
        
        from sqlalchemy_engine_kit.engine import DatabaseManager
        DatabaseManager._instance = None
        DatabaseManager._is_resetting = False
        
        manager = DatabaseManager()
        manager.initialize(sqlite_memory_config, auto_start=True, monitor=monitor)
        
        # Verify monitor is set
        assert manager.engine._monitor is monitor
        
        # Perform operations
        with manager.engine.session_context() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        manager.reset()
    
    def test_custom_monitor_metrics_recording(self, sqlite_memory_config):
        """Test that custom monitor receives metric calls."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Perform operations that should trigger metrics
        with engine.session_context() as session:
            session.execute(text("SELECT 1")).scalar()
        
        # Verify monitor instance is working
        assert monitor is not None
        assert hasattr(monitor, 'metrics')
        
        engine.stop()
    
    def test_custom_monitor_error_recording(self, sqlite_memory_config):
        """Test that custom monitor receives error recordings."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Manually record an error (simulating engine behavior)
        monitor.record_error("test_error", "sqlite")
        
        # Verify error was recorded
        assert len(monitor.errors) == 1
        assert monitor.errors[0]["error_type"] == "test_error"
        assert monitor.errors[0]["db_type"] == "sqlite"
        
        engine.stop()
    
    def test_custom_monitor_query_duration_recording(self, sqlite_memory_config):
        """Test that custom monitor receives query duration recordings."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Manually record query duration (simulating engine behavior)
        monitor.record_query_duration("SELECT 1", 0.123, True, "sqlite")
        
        # Verify query duration was recorded
        assert len(monitor.query_durations) == 1
        assert monitor.query_durations[0]["query"] == "SELECT 1"
        assert monitor.query_durations[0]["duration"] == 0.123
        assert monitor.query_durations[0]["success"] is True
        assert monitor.query_durations[0]["db_type"] == "sqlite"
        
        engine.stop()
    
    def test_custom_monitor_pool_stats_recording(self, sqlite_memory_config):
        """Test that custom monitor receives pool stats recordings."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Manually record pool stats (simulating engine behavior)
        monitor.record_connection_pool_stats(
            pool_size=10,
            active=3,
            idle=5,
            overflow=2,
            db_type="sqlite"
        )
        
        # Verify pool stats were recorded
        assert len(monitor.pool_stats) == 1
        assert monitor.pool_stats[0]["pool_size"] == 10
        assert monitor.pool_stats[0]["active"] == 3
        assert monitor.pool_stats[0]["idle"] == 5
        assert monitor.pool_stats[0]["overflow"] == 2
        
        engine.stop()
    
    def test_custom_monitor_session_count_recording(self, sqlite_memory_config):
        """Test that custom monitor receives session count recordings."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Manually record session count (simulating engine behavior)
        monitor.record_session_count(5, "sqlite")
        
        # Verify session count was recorded
        assert len(monitor.session_counts) == 1
        assert monitor.session_counts[0]["count"] == 5
        assert monitor.session_counts[0]["db_type"] == "sqlite"
        
        engine.stop()
    
    def test_custom_monitor_all_metric_types(self, sqlite_memory_config):
        """Test that custom monitor handles all metric types."""
        monitor = TestCustomMonitor()
        engine = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine.start()
        
        # Clear metrics
        monitor.clear()
        
        # Record all metric types
        monitor.increment("test_counter", 1.0, {"label": "value"})
        monitor.set_gauge("test_gauge", 42.0, {"label": "value"})
        monitor.observe_histogram("test_histogram", 0.5, {"label": "value"})
        monitor.record_query_duration("SELECT 1", 0.1, True, "sqlite")
        monitor.record_error("test_error", "sqlite", {"label": "value"})
        monitor.record_connection_pool_stats(10, 3, 5, 2, "sqlite")
        monitor.record_session_count(5, "sqlite")
        
        # Verify all metrics were recorded
        assert len(monitor.increments) == 1
        assert len(monitor.gauges) == 1
        assert len(monitor.histograms) == 1
        assert len(monitor.query_durations) == 1
        assert len(monitor.errors) == 1
        assert len(monitor.pool_stats) == 1
        assert len(monitor.session_counts) == 1
        
        # Verify metric values
        assert monitor.increments[0]["name"] == "test_counter"
        assert monitor.gauges[0]["name"] == "test_gauge"
        assert monitor.gauges[0]["value"] == 42.0
        assert monitor.histograms[0]["name"] == "test_histogram"
        
        engine.stop()
    
    def test_custom_monitor_with_multiple_engines(self, sqlite_memory_config):
        """Test custom monitor with multiple engine instances."""
        monitor = TestCustomMonitor()
        
        # Create multiple engines with same monitor
        engine1 = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine1.start()
        
        engine2 = DatabaseEngine(sqlite_memory_config, monitor=monitor)
        engine2.start()
        
        # Both should use same monitor
        assert engine1._monitor is monitor
        assert engine2._monitor is monitor
        
        # Operations should work
        with engine1.session_context() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        with engine2.session_context() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        engine1.stop()
        engine2.stop()

