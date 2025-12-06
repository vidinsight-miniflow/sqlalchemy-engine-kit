# Optional Dependencies

How optional dependencies are handled in engine-kit to prevent import errors.

## Overview

engine-kit uses **graceful degradation** for optional dependencies. This means:
- ✅ Package imports successfully even if optional dependencies are missing
- ✅ Features are disabled if dependencies aren't installed
- ✅ Clear error messages when trying to use features without dependencies
- ✅ No import-time errors

## How It Works

### 1. Alembic (Migrations)

```python
# src/sqlalchemy_engine_kit/migrations/__init__.py
try:
    from alembic import config as alembic_config
    from alembic import command
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    # Placeholder functions that raise helpful errors
```

**Usage:**
```python
from sqlalchemy_engine_kit.migrations import MigrationManager

# If Alembic not installed:
# - ALEMBIC_AVAILABLE = False
# - MigrationManager() raises: "Alembic is not installed. Install with: pip install alembic"
```

### 2. Prometheus (Monitoring)

```python
# src/sqlalchemy_engine_kit/monitoring/prometheus.py
try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
```

**Usage:**
```python
from sqlalchemy_engine_kit import PrometheusMonitor

# If prometheus-client not installed:
# - PrometheusMonitor() raises: "prometheus-client is required..."
```

### 3. python-dotenv (Environment Config)

```python
# src/sqlalchemy_engine_kit/config/__init__.py
try:
    from .env_loader import get_config_from_env, load_config_from_file
    ENV_LOADER_AVAILABLE = True
except ImportError:
    ENV_LOADER_AVAILABLE = False
    # Placeholder functions with helpful errors
```

**Usage:**
```python
from sqlalchemy_engine_kit import get_config_from_env

# If python-dotenv not installed:
# - ENV_LOADER_AVAILABLE = False
# - get_config_from_env() raises: "python-dotenv not installed..."
```

### 4. Database Drivers (psycopg2, pymysql)

**Important**: Database drivers are handled by SQLAlchemy, not directly by engine-kit.

SQLAlchemy uses **lazy loading** for database drivers:
- ✅ No import-time errors
- ✅ Driver is loaded only when connection is established
- ✅ Error occurs at connection time, not import time

**Example:**
```python
from sqlalchemy_engine_kit import get_postgresql_config, DatabaseManager

# This works fine - no import error
config = get_postgresql_config(
    db_name="mydb",
    host="localhost",
    username="user",
    password="pass"
)

manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# Error occurs HERE (connection time), not at import
# Error: "No module named 'psycopg2'"
```

## Checking Availability

You can check if optional features are available:

```python
from sqlalchemy_engine_kit.migrations import ALEMBIC_AVAILABLE
from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
from sqlalchemy_engine_kit import MONITORING_AVAILABLE

if ALEMBIC_AVAILABLE:
    from sqlalchemy_engine_kit.migrations import MigrationManager
    # Use migrations
else:
    print("Alembic not installed")

if ENV_LOADER_AVAILABLE:
    from sqlalchemy_engine_kit import get_config_from_env
    config = get_config_from_env()
else:
    print("python-dotenv not installed")
```

## Installation Scenarios

### Scenario 1: Minimal Installation
```bash
pip install sqlalchemy-engine-kit
```
- ✅ Core features work (SQLite, basic operations)
- ❌ Migrations disabled (Alembic not installed)
- ❌ Prometheus monitoring disabled
- ❌ Environment config disabled
- ❌ PostgreSQL/MySQL disabled (drivers not installed)

### Scenario 2: With PostgreSQL
```bash
pip install "sqlalchemy-engine-kit[postgres]"
```
- ✅ Core features work
- ✅ PostgreSQL works (psycopg2 installed)
- ❌ Migrations still disabled
- ❌ Prometheus still disabled

### Scenario 3: Full Installation
```bash
pip install "sqlalchemy-engine-kit[all]"
```
- ✅ All features enabled
- ✅ All database drivers installed
- ✅ Migrations enabled
- ✅ Monitoring enabled
- ✅ Environment config enabled

## Error Messages

When trying to use features without dependencies, you get helpful errors:

```python
# Without Alembic
from sqlalchemy_engine_kit.migrations import MigrationManager
manager = MigrationManager(...)
# ImportError: Alembic is not installed. Install with: pip install alembic

# Without prometheus-client
from sqlalchemy_engine_kit import PrometheusMonitor
monitor = PrometheusMonitor()
# ImportError: prometheus-client is required for Prometheus monitoring. 
# Install it with: pip install prometheus-client

# Without python-dotenv
from sqlalchemy_engine_kit import get_config_from_env
config = get_config_from_env()
# ImportError: python-dotenv not installed. Install with: pip install python-dotenv
```

## Best Practices

### 1. Check Availability Before Use
```python
from sqlalchemy_engine_kit.migrations import ALEMBIC_AVAILABLE

if ALEMBIC_AVAILABLE:
    from sqlalchemy_engine_kit.migrations import MigrationManager
    # Use migrations
else:
    # Fallback behavior
    print("Migrations not available")
```

### 2. Install What You Need
```bash
# For production with PostgreSQL and migrations
pip install "sqlalchemy-engine-kit[postgres,migrations]"

# For development with all features
pip install "sqlalchemy-engine-kit[all]"
```

### 3. Handle Errors Gracefully
```python
try:
    from sqlalchemy_engine_kit import PrometheusMonitor
    monitor = PrometheusMonitor()
except ImportError as e:
    from sqlalchemy_engine_kit import NoOpMonitor
    monitor = NoOpMonitor()  # Fallback
```

## Summary

✅ **Import errors are prevented** - Package imports successfully
✅ **Feature detection** - Check `*_AVAILABLE` flags
✅ **Helpful errors** - Clear messages when features are used without dependencies
✅ **Lazy loading** - Database drivers loaded only when needed
✅ **Graceful degradation** - Core features work without optional dependencies

---

**No import errors!** The package is designed to work with or without optional dependencies.

