"""
No-op monitoring implementation (default).

This is the default monitoring implementation that does nothing.
Useful when monitoring is not needed or not configured.
It has zero overhead and no dependencies.
"""

from typing import Optional, Dict, Any
from .base import BaseMonitor


class NoOpMonitor(BaseMonitor):
    """No-op monitor that does nothing.
    
    This monitor implementation performs no operations. It's used as the
    default when no monitoring is configured. It has zero overhead and
    can be safely used in all scenarios.
    
    Examples:
        >>> # Default usage (no monitoring)
        >>> monitor = NoOpMonitor()
        >>> monitor.increment("queries_total")  # Does nothing
        >>> monitor.set_gauge("pool_size", 10)  # Does nothing
    
    Note:
        - Zero overhead: All methods are no-ops
        - No dependencies: Pure Python, no external libraries
        - Thread-safe: Can be used from any thread
        - Default: Used when no monitor is explicitly configured
    """
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def record_query_duration(
        self,
        query: str,
        duration: float,
        success: bool,
        db_type: Optional[str] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def record_connection_pool_stats(
        self,
        pool_size: int,
        active: int,
        idle: int,
        overflow: int,
        db_type: Optional[str] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def record_session_count(
        self,
        count: int,
        db_type: Optional[str] = None
    ) -> None:
        """No-op: Does nothing."""
        pass
    
    def record_error(
        self,
        error_type: str,
        db_type: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """No-op: Does nothing."""
        pass

