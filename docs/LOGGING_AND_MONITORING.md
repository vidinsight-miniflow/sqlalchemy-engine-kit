# Logging and Monitoring Configuration Guide

## Overview

The engine-kit provides **modular logging and monitoring** that integrates seamlessly with your existing infrastructure. You can use your own logger and monitoring systems, or let engine-kit create defaults for you.

---

## Logging Configuration

### Modularity Principle
Engine-kit's logging follows a **priority-based system**:
1. **Your custom logger** (if injected) - HIGHEST PRIORITY
2. **Environment variable logger** (if specified)
3. **Root logger** (if your app configured it)
4. **Default engine-kit logger** (auto-configured) - LOWEST PRIORITY

### Option 1: Inject Your Logger (Recommended for Production)

```python
import logging
from sqlalchemy_engine_kit import LoggerAdapter, DatabaseManager

# Configure your application's logger
app_logger = logging.getLogger("myapp")
app_logger.setLevel(logging.INFO)

# Add your handlers, formatters, etc.
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app_logger.addHandler(handler)

# Inject into engine_kit - all engine_kit logs will use your logger
LoggerAdapter.set_logger(app_logger)

# Now initialize your database
manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# All database logs appear in your application logger
```

**Use Case**: You have an existing logging infrastructure (ELK, Splunk, CloudWatch, etc.)

### Option 2: Use Environment Variable

```bash
# Set environment variable
export ENGINE_KIT_LOGGER_NAME=myapp.database
```

```python
from sqlalchemy_engine_kit import DatabaseManager

# engine_kit automatically uses logging.getLogger("myapp.database")
manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# Configure the logger in your app's logging config
logging.config.dictConfig({
    'version': 1,
    'loggers': {
        'myapp.database': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        }
    }
})
```

**Use Case**: You use declarative logging configuration (YAML, dict config, etc.)

### Option 3: Use Root Logger (Automatic Integration)

```python
import logging

# Configure root logger in your application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# engine_kit automatically detects and uses it
from sqlalchemy_engine_kit import DatabaseManager
manager = DatabaseManager()
# Logs appear automatically in your root logger
```

**Use Case**: Simple applications with basic logging needs

### Option 4: Use Default (No Configuration)

```python
# Do nothing - engine_kit creates its own logger
from sqlalchemy_engine_kit import DatabaseManager
manager = DatabaseManager()
# Logs to stdout with basic formatting
```

**Use Case**: Quick prototyping, development, testing

---

## Monitoring Configuration

### Modularity Principle
Engine-kit's monitoring is **completely pluggable**:
- **No monitor** (default): Uses `NoOpMonitor` - zero overhead
- **Your monitor**: Implement `BaseMonitor` interface
- **Prometheus** (built-in): Use `PrometheusMonitor`

### Option 1: Inject Your Monitoring System (Recommended for Production)

```python
from sqlalchemy_engine_kit import DatabaseManager, BaseMonitor
from typing import Optional, Dict

class DatadogMonitor(BaseMonitor):
    """Integrate with Datadog metrics."""
    
    def __init__(self, statsd_client):
        self.statsd = statsd_client
    
    def increment(self, name: str, value: float = 1.0, 
                  labels: Optional[Dict[str, str]] = None) -> None:
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        self.statsd.increment(name, value, tags=tags)
    
    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> None:
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        self.statsd.gauge(name, value, tags=tags)
    
    def observe_histogram(self, name: str, value: float,
                         labels: Optional[Dict[str, str]] = None) -> None:
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        self.statsd.histogram(name, value, tags=tags)
    
    def record_query_duration(self, query: str, duration: float,
                             success: bool, db_type: Optional[str] = None) -> None:
        tags = [
            f"success:{success}",
            f"db_type:{db_type or 'unknown'}",
            f"query_type:{self._extract_query_type(query)}"
        ]
        self.statsd.histogram("db.query.duration", duration, tags=tags)
        
        if not success:
            self.statsd.increment("db.query.errors", tags=tags)
    
    def record_error(self, error_type: str, db_type: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None) -> None:
        tags = [f"error_type:{error_type}", f"db_type:{db_type or 'unknown'}"]
        if labels:
            tags.extend([f"{k}:{v}" for k, v in labels.items()])
        self.statsd.increment("db.errors", tags=tags)
    
    def record_connection_pool_stats(self, pool_size: int, active: int,
                                    idle: int, overflow: int,
                                    db_type: Optional[str] = None) -> None:
        tags = [f"db_type:{db_type or 'unknown'}"]
        self.statsd.gauge("db.pool.size", pool_size, tags=tags)
        self.statsd.gauge("db.pool.active", active, tags=tags)
        self.statsd.gauge("db.pool.idle", idle, tags=tags)
        self.statsd.gauge("db.pool.overflow", overflow, tags=tags)
    
    def record_session_count(self, count: int, db_type: Optional[str] = None) -> None:
        tags = [f"db_type:{db_type or 'unknown'}"]
        self.statsd.gauge("db.sessions.active", count, tags=tags)
    
    @staticmethod
    def _extract_query_type(query: str) -> str:
        """Extract query type (SELECT, INSERT, UPDATE, DELETE)."""
        query_upper = query.strip().upper()
        for qtype in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
            if query_upper.startswith(qtype):
                return qtype.lower()
        return 'other'

# Initialize with your monitoring
from datadog import statsd
monitor = DatadogMonitor(statsd)

manager = DatabaseManager()
manager.initialize(config, auto_start=True, monitor=monitor)
```

#### CloudWatch Example

```python
import boto3
from sqlalchemy_engine_kit import BaseMonitor
from typing import Optional, Dict

class CloudWatchMonitor(BaseMonitor):
    """Integrate with AWS CloudWatch metrics."""
    
    def __init__(self, namespace: str = "MyApp/Database"):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
    
    def increment(self, name: str, value: float = 1.0,
                  labels: Optional[Dict[str, str]] = None) -> None:
        self._put_metric(name, value, 'Count', labels)
    
    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> None:
        self._put_metric(name, value, 'None', labels)
    
    def observe_histogram(self, name: str, value: float,
                         labels: Optional[Dict[str, str]] = None) -> None:
        self._put_metric(name, value, 'Milliseconds', labels)
    
    def record_query_duration(self, query: str, duration: float,
                             success: bool, db_type: Optional[str] = None) -> None:
        self._put_metric(
            'QueryDuration',
            duration * 1000,  # Convert to milliseconds
            'Milliseconds',
            {'Success': str(success), 'DBType': db_type or 'unknown'}
        )
    
    def record_error(self, error_type: str, db_type: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None) -> None:
        all_labels = {'ErrorType': error_type, 'DBType': db_type or 'unknown'}
        if labels:
            all_labels.update(labels)
        self._put_metric('DatabaseErrors', 1, 'Count', all_labels)
    
    def record_connection_pool_stats(self, pool_size: int, active: int,
                                    idle: int, overflow: int,
                                    db_type: Optional[str] = None) -> None:
        labels = {'DBType': db_type or 'unknown'}
        self._put_metric('PoolSize', pool_size, 'Count', labels)
        self._put_metric('PoolActive', active, 'Count', labels)
        self._put_metric('PoolIdle', idle, 'Count', labels)
        self._put_metric('PoolOverflow', overflow, 'Count', labels)
    
    def record_session_count(self, count: int, db_type: Optional[str] = None) -> None:
        self._put_metric(
            'ActiveSessions', 
            count, 
            'Count', 
            {'DBType': db_type or 'unknown'}
        )
    
    def _put_metric(self, name: str, value: float, unit: str,
                   labels: Optional[Dict[str, str]] = None) -> None:
        """Put metric to CloudWatch."""
        dimensions = []
        if labels:
            dimensions = [{'Name': k, 'Value': v} for k, v in labels.items()]
        
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[{
                'MetricName': name,
                'Value': value,
                'Unit': unit,
                'Dimensions': dimensions
            }]
        )

# Use it
monitor = CloudWatchMonitor(namespace="MyApp/Database")
manager.initialize(config, monitor=monitor)
```

### Option 2: Use Prometheus (Built-in)

```python
from sqlalchemy_engine_kit import PrometheusMonitor, DatabaseManager

# Initialize Prometheus monitoring
monitor = PrometheusMonitor(
    namespace="myapp",        # Metric prefix: myapp_db_*
    subsystem="database"      # Subsystem: myapp_database_*
)

manager = DatabaseManager()
manager.initialize(config, auto_start=True, monitor=monitor)

# Expose metrics endpoint (Flask example)
from flask import Flask
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Metrics available:
# - myapp_database_queries_total
# - myapp_database_query_duration_seconds
# - myapp_database_errors_total
# - myapp_database_pool_size
# - myapp_database_pool_active
# - myapp_database_sessions_active
```

**Use Case**: You use Prometheus/Grafana for monitoring

### Option 3: No Monitoring (Default)

```python
from sqlalchemy_engine_kit import DatabaseManager

# No monitor parameter = NoOpMonitor (zero overhead)
manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# Or explicitly
from sqlalchemy_engine_kit import NoOpMonitor
manager.initialize(config, monitor=NoOpMonitor())
```

**Use Case**: Development, testing, or when monitoring happens at a different layer

---

## Logging Levels and Best Practices

### Production Logging Level
```python
import logging

# Set appropriate level for production
LoggerAdapter.get_logger("engine_kit").setLevel(logging.WARNING)

# Development/Staging
LoggerAdapter.get_logger("engine_kit").setLevel(logging.INFO)

# Debugging issues
LoggerAdapter.get_logger("engine_kit").setLevel(logging.DEBUG)
```

### What Gets Logged

| Level | What | Example |
|-------|------|---------|
| **DEBUG** | SQL queries, detailed operations | `SELECT * FROM users WHERE id = 1` |
| **INFO** | Lifecycle events | `Engine started`, `Session created` |
| **WARNING** | Recoverable issues | `Pool exhausted, waiting`, `Retry attempt 2` |
| **ERROR** | Operation failures | `Connection failed`, `Query error` |
| **CRITICAL** | System failures | `Engine initialization failed` |

### Sensitive Data Protection

```python
# engine_kit NEVER logs:
# - Passwords
# - Connection strings with credentials
# - User data in queries (by default)

# To log SQL queries (development only!):
from sqlalchemy_engine_kit import EngineConfig

config = EngineConfig(
    echo=True  # Logs all SQL to SQLAlchemy logger
)
```

---

## Monitoring Metrics Reference

### Standard Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `db_queries_total` | Counter | Total queries executed | `db_type`, `query_type`, `success` |
| `db_query_duration_seconds` | Histogram | Query execution time | `db_type`, `query_type` |
| `db_errors_total` | Counter | Total errors | `db_type`, `error_type` |
| `db_pool_size` | Gauge | Connection pool size | `db_type` |
| `db_pool_active` | Gauge | Active connections | `db_type` |
| `db_pool_idle` | Gauge | Idle connections | `db_type` |
| `db_pool_overflow` | Gauge | Overflow connections | `db_type` |
| `db_sessions_active` | Gauge | Active sessions | `db_type` |

### Alerts to Set Up

```yaml
# Example alert rules (Prometheus)
groups:
  - name: database
    rules:
      # Query duration
      - alert: SlowQueries
        expr: histogram_quantile(0.95, db_query_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "95th percentile query time > 1s"
      
      # Error rate
      - alert: HighErrorRate
        expr: rate(db_errors_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Database error rate > 1%"
      
      # Pool exhaustion
      - alert: PoolExhausted
        expr: db_pool_active >= db_pool_size
        for: 1m
        annotations:
          summary: "Connection pool exhausted"
      
      # High session count
      - alert: HighSessionCount
        expr: db_sessions_active > 50
        for: 5m
        annotations:
          summary: "Unusually high active sessions"
```

---

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from sqlalchemy_engine_kit import DatabaseManager, LoggerAdapter
import logging

app = FastAPI()

# Use FastAPI's logger
LoggerAdapter.set_logger(app.logger)

@app.on_event("startup")
async def startup():
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True, monitor=your_monitor)

@app.on_event("shutdown")
async def shutdown():
    manager = DatabaseManager.get_instance()
    manager.stop()
```

### Flask Integration

```python
from flask import Flask
from sqlalchemy_engine_kit import DatabaseManager, LoggerAdapter

app = Flask(__name__)

# Use Flask's logger
LoggerAdapter.set_logger(app.logger)

@app.before_first_request
def init_db():
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)

@app.teardown_appcontext
def shutdown_db(exception=None):
    # Engine cleanup happens automatically
    pass
```

### Django Integration

```python
# settings.py
import logging
from sqlalchemy_engine_kit import LoggerAdapter

# Use Django's logger
django_logger = logging.getLogger('django.db')
LoggerAdapter.set_logger(django_logger)

# apps.py
from django.apps import AppConfig
from sqlalchemy_engine_kit import DatabaseManager

class MyAppConfig(AppConfig):
    def ready(self):
        manager = DatabaseManager()
        manager.initialize(config, auto_start=True)
```

---

## Troubleshooting

### Issue: Logs not appearing

**Solution 1**: Check logger level
```python
import logging
logger = logging.getLogger("engine_kit")
print(f"Logger level: {logger.level}")
print(f"Has handlers: {bool(logger.handlers)}")
```

**Solution 2**: Check if custom logger is configured
```python
from sqlalchemy_engine_kit import LoggerAdapter
# Reset to defaults
LoggerAdapter.reset_logger()
```

### Issue: Duplicate log messages

**Cause**: Both root logger and custom logger are configured

**Solution**: Set `propagate=False`
```python
import logging
logger = logging.getLogger("engine_kit")
logger.propagate = False
```

### Issue: Monitoring metrics not appearing

**Solution**: Check monitor instance
```python
manager = DatabaseManager.get_instance()
engine = manager.engine
print(f"Monitor: {type(engine._monitor)}")

# If NoOpMonitor, inject your monitor
manager.initialize(config, monitor=your_monitor, force_reinitialize=True)
```

---

## Performance Considerations

### Logging Performance
- **INFO/WARNING/ERROR**: Minimal overhead (~1-2 microseconds per log)
- **DEBUG**: Moderate overhead (~10-20 microseconds, includes SQL logging)
- **Recommendation**: Use INFO in production, DEBUG for troubleshooting

### Monitoring Performance
- **NoOpMonitor**: Zero overhead (no-op calls)
- **PrometheusMonitor**: ~5-10 microseconds per metric
- **Custom Monitor**: Depends on your implementation
- **Recommendation**: Use async/buffered metrics in high-throughput scenarios

---

## Summary

| Aspect | Modular? | Default Behavior | Production Recommendation |
|--------|----------|------------------|---------------------------|
| **Logging** | ✅ Yes | Auto-configured console logger | Inject your app's logger |
| **Monitoring** | ✅ Yes | NoOpMonitor (no metrics) | Inject your monitoring system |
| **SQL Logging** | ✅ Yes | Disabled | Keep disabled (use APM instead) |
| **Log Level** | ✅ Yes | INFO | WARNING for prod, INFO for staging |

**Key Principle**: Engine-kit adapts to YOUR infrastructure, not the other way around.



