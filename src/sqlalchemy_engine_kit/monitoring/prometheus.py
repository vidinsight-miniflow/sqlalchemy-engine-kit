"""
Prometheus metrics implementation.

This module provides Prometheus-compatible metrics collection.
Requires: prometheus-client
"""

import os
import threading
from typing import Optional, Dict, Any, Tuple, FrozenSet

try:
    from prometheus_client import (
        Counter, Gauge, Histogram,
        CollectorRegistry, REGISTRY, push_to_gateway
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CollectorRegistry = None
    REGISTRY = None
    Counter = None
    Gauge = None
    Histogram = None
    push_to_gateway = None

from .base import BaseMonitor


class PrometheusMonitor(BaseMonitor):
    """Prometheus monitor that integrates with host system.
    
    Features:
        - Query metrics (count, duration, success/failure)
        - Connection pool metrics (size, active, idle, overflow)
        - Session metrics (active session count)
        - Error metrics (error counts by type)
        - Push gateway support (optional)
        - Dynamic metric creation with consistent label handling
    
    Args:
        registry: Prometheus registry (uses host system's if None)
        prefix: Metric name prefix (default: "engine_kit_")
        push_gateway: Push gateway URL (if using push model)
        job_name: Job name for push gateway
    """
    
    def __init__(
        self,
        registry: Optional[Any] = None,
        prefix: str = "engine_kit_",
        push_gateway: Optional[str] = None,
        job_name: Optional[str] = None
    ):
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "prometheus-client is required for Prometheus monitoring. "
                "Install it with: pip install prometheus-client"
            )
        
        self.registry = registry or REGISTRY or CollectorRegistry()
        self.prefix = prefix or os.getenv("ENGINE_KIT_METRICS_PREFIX", "engine_kit_")
        self.push_gateway = push_gateway or os.getenv("PROMETHEUS_PUSH_GATEWAY")
        self.job_name = job_name or os.getenv("PROMETHEUS_JOB_NAME", "engine_kit")
        
        # Thread-safe metric cache: key = (metric_name, frozenset(label_names))
        self._metric_cache: Dict[Tuple[str, FrozenSet[str]], Any] = {}
        self._cache_lock = threading.RLock()
        
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Query metrics
        self.query_counter = Counter(
            f"{self.prefix}queries_total",
            "Total number of database queries",
            ["query_type", "db_type", "status"],
            registry=self.registry
        )
        
        self.query_duration = Histogram(
            f"{self.prefix}query_duration_seconds",
            "Query execution duration in seconds",
            ["query_type", "db_type"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Connection pool metrics
        self.connection_pool_size = Gauge(
            f"{self.prefix}connection_pool_size",
            "Connection pool size",
            ["db_type"],
            registry=self.registry
        )
        
        self.connection_pool_active = Gauge(
            f"{self.prefix}connection_pool_active",
            "Active connections in pool",
            ["db_type"],
            registry=self.registry
        )
        
        self.connection_pool_idle = Gauge(
            f"{self.prefix}connection_pool_idle",
            "Idle connections in pool",
            ["db_type"],
            registry=self.registry
        )
        
        self.connection_pool_overflow = Gauge(
            f"{self.prefix}connection_pool_overflow",
            "Overflow connections in pool",
            ["db_type"],
            registry=self.registry
        )
        
        # Session metrics
        self.session_count = Gauge(
            f"{self.prefix}sessions_active",
            "Number of active sessions",
            ["db_type"],
            registry=self.registry
        )
        
        # Error metrics - dinamik label desteği için cache kullanılacak
        self._error_metrics: Dict[FrozenSet[str], Counter] = {}
    
    def _get_or_create_metric(
        self,
        metric_type: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Any:
        """Get or create a metric with consistent label handling.
        
        Args:
            metric_type: "counter", "gauge", or "histogram"
            name: Metric name (without prefix)
            labels: Labels dict
            
        Returns:
            The metric object
            
        Raises:
            ValueError: If same metric name used with different label sets
        """
        full_name = f"{self.prefix}{name}"
        label_names = frozenset(labels.keys()) if labels else frozenset()
        cache_key = (full_name, label_names)
        
        with self._cache_lock:
            # Check if metric exists with different labels
            existing_keys = [k for k in self._metric_cache if k[0] == full_name]
            if existing_keys and cache_key not in self._metric_cache:
                existing_labels = existing_keys[0][1]
                raise ValueError(
                    f"Metric '{full_name}' already exists with labels {set(existing_labels)}. "
                    f"Cannot create with different labels {set(label_names)}. "
                    f"Prometheus requires consistent label sets per metric."
                )
            
            if cache_key not in self._metric_cache:
                label_list = list(label_names)
                if metric_type == "counter":
                    self._metric_cache[cache_key] = Counter(
                        full_name,
                        f"Counter metric: {name}",
                        label_list,
                        registry=self.registry
                    )
                elif metric_type == "gauge":
                    self._metric_cache[cache_key] = Gauge(
                        full_name,
                        f"Gauge metric: {name}",
                        label_list,
                        registry=self.registry
                    )
                elif metric_type == "histogram":
                    self._metric_cache[cache_key] = Histogram(
                        full_name,
                        f"Histogram metric: {name}",
                        label_list,
                        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
                        registry=self.registry
                    )
            
            return self._metric_cache[cache_key]
    
    def push_metrics(self) -> None:
        """Push metrics to push gateway (if configured)."""
        if not self.push_gateway:
            return
        
        try:
            push_to_gateway(
                self.push_gateway,
                job=self.job_name,
                registry=self.registry
            )
        except Exception as e:
            from ..core.logging import LoggerAdapter
            logger = LoggerAdapter.get_logger(__name__)
            logger.error(
                f"Failed to push metrics to gateway {self.push_gateway}: {e}",
                exc_info=True,
                extra={
                    "push_gateway": self.push_gateway,
                    "job_name": self.job_name
                }
            )
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        counter = self._get_or_create_metric("counter", name, labels)
        
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        gauge = self._get_or_create_metric("gauge", name, labels)
        
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Observe a histogram metric."""
        histogram = self._get_or_create_metric("histogram", name, labels)
        
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)
    
    def record_query_duration(
        self,
        query: str,
        duration: float,
        success: bool,
        db_type: Optional[str] = None
    ) -> None:
        """Record query execution duration."""
        query_type = self.extract_query_type(query)
        status = "success" if success else "error"
        db_type = db_type or "unknown"
        
        self.query_counter.labels(
            query_type=query_type,
            db_type=db_type,
            status=status
        ).inc()
        
        self.query_duration.labels(
            query_type=query_type,
            db_type=db_type
        ).observe(duration)
        
        if not success:
            self.record_error("query_error", db_type=db_type)
    
    def record_connection_pool_stats(
        self,
        pool_size: int,
        active: int,
        idle: int,
        overflow: int,
        db_type: Optional[str] = None
    ) -> None:
        """Record connection pool statistics."""
        db_type = db_type or "unknown"
        
        self.connection_pool_size.labels(db_type=db_type).set(pool_size)
        self.connection_pool_active.labels(db_type=db_type).set(active)
        self.connection_pool_idle.labels(db_type=db_type).set(idle)
        self.connection_pool_overflow.labels(db_type=db_type).set(overflow)
    
    def record_session_count(
        self,
        count: int,
        db_type: Optional[str] = None
    ) -> None:
        """Record number of active sessions."""
        db_type = db_type or "unknown"
        self.session_count.labels(db_type=db_type).set(count)
    
    def record_error(
        self,
        error_type: str,
        db_type: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record an error occurrence.
        
        Args:
            error_type: Type of error
            db_type: Database type
            labels: Additional labels (merged with error_type and db_type)
        """
        db_type = db_type or "unknown"
        
        # Merge all labels
        all_labels = {"error_type": error_type, "db_type": db_type}
        if labels:
            all_labels.update(labels)
        
        label_names = frozenset(all_labels.keys())
        
        with self._cache_lock:
            if label_names not in self._error_metrics:
                self._error_metrics[label_names] = Counter(
                    f"{self.prefix}errors_total",
                    "Total number of errors",
                    list(label_names),
                    registry=self.registry
                )
            
            error_counter = self._error_metrics[label_names]
        
        error_counter.labels(**all_labels).inc()