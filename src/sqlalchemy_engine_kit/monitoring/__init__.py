"""
Monitoring Module - Metrics Collection Interface

This module provides pluggable monitoring/metrics collection for engine-kit.
It supports integration with host system's monitoring infrastructure, including
Prometheus, StatsD, and custom monitoring systems.

Supported Implementations:
    - PrometheusMonitor: Prometheus metrics (requires prometheus-client)
    - NoOpMonitor: No-op implementation (default, no dependencies)
    - Custom: Implement BaseMonitor interface for custom monitoring

Usage:
    >>> from engine_kit.monitoring import PrometheusMonitor, NoOpMonitor
    >>> from prometheus_client import REGISTRY
    >>> 
    >>> # Use host system's Prometheus registry
    >>> monitor = PrometheusMonitor(registry=REGISTRY)
    >>> 
    >>> # Or use default no-op monitor
    >>> monitor = NoOpMonitor()
"""

from .base import BaseMonitor, MetricType
from .noop import NoOpMonitor

# PrometheusMonitor is conditionally imported (requires prometheus-client)
try:
    from .prometheus import PrometheusMonitor
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    PrometheusMonitor = None

__all__ = [
    'BaseMonitor',
    'MetricType',
    'NoOpMonitor',
]

if PROMETHEUS_AVAILABLE:
    __all__.append('PrometheusMonitor')

