# Deployment Guide

## Production Deployment Checklist

### 1. Environment Setup

#### Required Environment Variables
```bash
# Database Configuration (if using env loader)
DB_TYPE=postgresql                    # postgresql, mysql, sqlite
DB_NAME=myapp_production
DB_HOST=db.example.com
DB_PORT=5432
DB_USERNAME=app_user
DB_PASSWORD=secure_password_here

# Optional: Custom Logger Integration
ENGINE_KIT_LOGGER_NAME=myapp.database  # Use your app's logger

# Optional: Logging Level
ENGINE_KIT_LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
```

#### Database Connection Pooling
```python
from sqlalchemy_engine_kit import DatabaseManager, EngineConfig

# Production pool settings
engine_config = EngineConfig(
    pool_size=20,              # Number of persistent connections
    max_overflow=10,           # Additional connections allowed
    pool_timeout=30,           # Seconds to wait for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connections before use
    echo=False                 # Disable SQL logging in production
)
```

### 2. Logging Configuration

#### Option A: Use Your Existing Logger (Recommended)
```python
import logging
from sqlalchemy_engine_kit import LoggerAdapter

# Configure your application logger first
app_logger = logging.getLogger("myapp")
app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app_logger.addHandler(handler)

# Inject into engine_kit
LoggerAdapter.set_logger(app_logger)

# Now all engine_kit logs use your logger
manager = DatabaseManager()
# ... logs will appear in your application logger
```

#### Option B: Use Environment Variable
```bash
# Set environment variable before starting app
export ENGINE_KIT_LOGGER_NAME=myapp.database

# engine_kit will automatically use logging.getLogger("myapp.database")
```

#### Option C: Use Default (Auto-configured)
```python
# Do nothing - engine_kit creates its own logger
# Good for quick setup, but less control
```

### 3. Monitoring Configuration

#### Option A: Inject Custom Monitor (Recommended for Production)
```python
from sqlalchemy_engine_kit import DatabaseManager, BaseMonitor
from typing import Optional, Dict

class CustomMonitor(BaseMonitor):
    """Your monitoring system integration."""
    
    def __init__(self, your_metrics_client):
        self.metrics = your_metrics_client
    
    def increment(self, name: str, value: float = 1.0, 
                  labels: Optional[Dict[str, str]] = None) -> None:
        self.metrics.counter(name).inc(value, labels)
    
    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> None:
        self.metrics.gauge(name).set(value, labels)
    
    def observe_histogram(self, name: str, value: float,
                         labels: Optional[Dict[str, str]] = None) -> None:
        self.metrics.histogram(name).observe(value, labels)
    
    def record_query_duration(self, query: str, duration: float,
                             success: bool, db_type: Optional[str] = None) -> None:
        labels = {"success": str(success), "db_type": db_type or "unknown"}
        self.metrics.histogram("db_query_duration_seconds").observe(duration, labels)
    
    def record_error(self, error_type: str, db_type: Optional[str] = None,
                    labels: Optional[Dict[str, str]] = None) -> None:
        all_labels = {"error_type": error_type, "db_type": db_type or "unknown"}
        if labels:
            all_labels.update(labels)
        self.metrics.counter("db_errors_total").inc(1, all_labels)
    
    def record_connection_pool_stats(self, pool_size: int, active: int,
                                    idle: int, overflow: int,
                                    db_type: Optional[str] = None) -> None:
        labels = {"db_type": db_type or "unknown"}
        self.metrics.gauge("db_pool_size").set(pool_size, labels)
        self.metrics.gauge("db_pool_active").set(active, labels)
        self.metrics.gauge("db_pool_idle").set(idle, labels)
        self.metrics.gauge("db_pool_overflow").set(overflow, labels)
    
    def record_session_count(self, count: int, db_type: Optional[str] = None) -> None:
        self.metrics.gauge("db_sessions_active").set(count, {"db_type": db_type or "unknown"})

# Initialize and inject
monitor = CustomMonitor(your_metrics_client)
manager = DatabaseManager()
manager.initialize(config, monitor=monitor)
```

#### Option B: Use Prometheus (Built-in)
```python
from sqlalchemy_engine_kit import PrometheusMonitor

# Requires: pip install prometheus-client
monitor = PrometheusMonitor(
    namespace="myapp",
    subsystem="database"
)

manager.initialize(config, monitor=monitor)

# Expose metrics endpoint (in your web framework)
# Flask example:
# from prometheus_client import generate_latest
# @app.route('/metrics')
# def metrics():
#     return generate_latest()
```

#### Option C: No Monitoring (Not Recommended for Production)
```python
from sqlalchemy_engine_kit import NoOpMonitor

monitor = NoOpMonitor()  # Does nothing
manager.initialize(config, monitor=monitor)
```

### 4. Application Lifecycle

#### Startup Sequence
```python
# app_startup.py
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config
import logging

# 1. Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myapp")

# 2. Initialize database manager
manager = DatabaseManager()
config = get_postgresql_config(
    db_name="myapp",
    host="db.example.com",
    username="app_user",
    password="secure_password"
)

# 3. Start engine with monitoring
try:
    manager.initialize(config, auto_start=True)
    logger.info("Database engine started successfully")
    
    # 4. Create tables if needed
    from myapp.models import Base
    manager.engine.create_tables(Base.metadata)
    
    # 5. Health check
    health = manager.get_health_status()
    if not health['is_healthy']:
        raise Exception("Database not healthy")
        
except Exception as e:
    logger.error(f"Failed to start database: {e}")
    raise
```

#### Graceful Shutdown
```python
# app_shutdown.py
import signal
import sys

def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutting down...")
    
    # Stop database engine
    try:
        manager = DatabaseManager.get_instance()
        manager.stop()
        logger.info("Database engine stopped")
    except Exception as e:
        logger.error(f"Error stopping database: {e}")
    
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

### 5. Health Checks

```python
# health_check.py
def database_health_check():
    """Health check endpoint for load balancer."""
    try:
        manager = DatabaseManager.get_instance()
        health = manager.get_health_status()
        
        return {
            "status": "healthy" if health['is_healthy'] else "unhealthy",
            "details": health
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### 6. Infrastructure Requirements

#### Minimum Requirements
- **Python**: 3.9+
- **Memory**: 512MB minimum, 1GB+ recommended
- **CPU**: 1 core minimum, 2+ cores recommended
- **Database**: PostgreSQL 12+, MySQL 8+, or SQLite 3.35+

#### Network Configuration
- Ensure firewall allows outbound connections to database
- Keep database on private network, not public internet
- Use SSL/TLS for database connections in production

#### Connection Pool Sizing
```python
# Rule of thumb: pool_size = (2 * num_cores) + effective_spindle_count
# For web applications with 4 cores: pool_size = 10-20

# High concurrency (100+ concurrent requests)
pool_size=50
max_overflow=20

# Medium concurrency (10-100 requests)
pool_size=20
max_overflow=10

# Low concurrency (<10 requests)
pool_size=5
max_overflow=5
```

### 7. Security Checklist

- [ ] **Never** log passwords or sensitive data
- [ ] Use environment variables or secrets manager for credentials
- [ ] Enable SSL/TLS for database connections
- [ ] Use strong, unique passwords (20+ characters)
- [ ] Rotate database credentials regularly
- [ ] Use read-only database users where possible
- [ ] Enable database audit logging
- [ ] Restrict database network access
- [ ] Keep SQLAlchemy and drivers updated
- [ ] Review and sanitize all user inputs

### 8. Performance Tuning

#### Connection Pool Tuning
```python
# Monitor these metrics:
# - connection_checkout_time: Should be <100ms
# - overflow_connections: Should rarely be >0
# - connection_timeouts: Should be 0

# If you see high checkout times:
# - Increase pool_size
# - Investigate slow queries
# - Check database server load

# If you see overflow connections:
# - Increase pool_size
# - Check for connection leaks
# - Review max_overflow setting
```

#### Query Performance
```python
# Enable query logging in staging/dev
engine_config = EngineConfig(echo=True)  # Log all SQL

# Use eager loading to avoid N+1 queries
from sqlalchemy_engine_kit import with_relationships, eager_load

# Bad: N+1 queries
users = session.query(User).all()
for user in users:
    print(user.posts)  # Separate query for each user

# Good: Single query with join
users = eager_load(
    session.query(User),
    'posts'
).all()
```

### 9. Monitoring Metrics (What to Track)

#### Key Metrics
1. **Query Duration** (`db_query_duration_seconds`)
   - Alert if p95 > 1s
   - Alert if p99 > 5s

2. **Error Rate** (`db_errors_total`)
   - Alert if error rate > 1%

3. **Connection Pool** (`db_pool_active`, `db_pool_idle`)
   - Alert if pool is exhausted (active = pool_size)

4. **Active Sessions** (`db_sessions_active`)
   - Alert if abnormally high

5. **Database Health** (`db_health_check`)
   - Alert if unhealthy

### 10. Backup and Recovery

```bash
# Backup strategy (example for PostgreSQL)
# Daily automated backups
0 2 * * * pg_dump -h db.example.com -U app_user myapp > /backups/myapp_$(date +\%Y\%m\%d).sql

# Point-in-time recovery setup
# Enable WAL archiving in PostgreSQL config
```

### 11. Deployment Checklist

- [ ] Tested on staging environment
- [ ] Database migrations run successfully
- [ ] Connection pool tested under load
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Team trained on runbooks
- [ ] Credentials rotated
- [ ] Security scan passed

## Common Issues

See [RUNBOOK.md](RUNBOOK.md) for troubleshooting common issues.

