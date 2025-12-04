"""
Base interface for monitoring/metrics collection.

This module defines the interface that all monitoring implementations
must follow. This allows for pluggable monitoring backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum


class MetricType(Enum):
    """Metric types supported by monitoring systems."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class BaseMonitor(ABC):
    """Base class for monitoring implementations.
    
    This abstract base class defines the interface that all monitoring
    implementations must follow. It provides methods for recording various
    types of metrics related to database operations.
    
    Implementations:
        - PrometheusMonitor: Prometheus-compatible metrics
        - NoOpMonitor: No-op implementation (default)
        - Custom: Implement this interface for custom monitoring systems
    """
    
    @abstractmethod
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        pass
    
    @abstractmethod
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        pass
    
    @abstractmethod
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Observe a histogram metric."""
        pass
    
    @abstractmethod
    def record_query_duration(
        self,
        query: str,
        duration: float,
        success: bool,
        db_type: Optional[str] = None
    ) -> None:
        """Record query execution duration."""
        pass
    
    @abstractmethod
    def record_connection_pool_stats(
        self,
        pool_size: int,
        active: int,
        idle: int,
        overflow: int,
        db_type: Optional[str] = None
    ) -> None:
        """Record connection pool statistics."""
        pass
    
    @abstractmethod
    def record_session_count(
        self,
        count: int,
        db_type: Optional[str] = None
    ) -> None:
        """Record number of active sessions."""
        pass
    
    @abstractmethod
    def record_error(
        self,
        error_type: str,
        db_type: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record an error occurrence."""
        pass

    @staticmethod
    def extract_query_type(query: str) -> str:
        """Extract query type from SQL query.
        
        Args:
            query: SQL query string
            
        Returns:
            Query type: "select", "insert", "update", "delete", or "other"
        """
        if not query:
            return "other"
        
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return "select"
        elif query_upper.startswith("INSERT"):
            return "insert"
        elif query_upper.startswith("UPDATE"):
            return "update"
        elif query_upper.startswith("DELETE"):
            return "delete"
        else:
            return "other"