# Best Practices

Guidelines and recommendations for using engine-kit effectively.

## Table of Contents

- [Initialization](#initialization)
- [Session Management](#session-management)
- [Error Handling](#error-handling)
- [Performance](#performance)
- [Testing](#testing)
- [Security](#security)
- [Common Pitfalls](#common-pitfalls)
- [Anti-Patterns](#anti-patterns)

---

## Initialization

### ✅ DO: Initialize Once at Application Startup

```python
# app.py or main.py
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config

# Initialize once
config = get_postgresql_config(db_name="myapp", ...)
manager = DatabaseManager()
manager.initialize(config, auto_start=True)
```

### ❌ DON'T: Initialize Multiple Times

```python
# BAD
def create_user():
    manager = DatabaseManager()
    manager.initialize(config)  # Don't do this!
    # ...
```

### ✅ DO: Use Singleton Pattern

```python
# Anywhere in your code
manager = DatabaseManager()  # Same instance
engine = manager.engine
```

### ✅ DO: Initialize with Monitoring

```python
from sqlalchemy_engine_kit import PrometheusMonitor

monitor = PrometheusMonitor()
manager.initialize(config, monitor=monitor)
```

---

## Session Management

### ✅ DO: Use Decorators

```python
@with_session(auto_commit=True)
def create_user(session: Session, name: str):
    user = User(name=name)
    session.add(user)
    return user  # Auto-commits
```

### ❌ DON'T: Manually Manage Sessions (Unless Necessary)

```python
# BAD - Error-prone
def create_user(name: str):
    manager = DatabaseManager()
    session = manager.engine.get_session()
    try:
        user = User(name=name)
        session.add(user)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()  # Easy to forget!
```

### ✅ DO: Use Readonly Sessions for Queries

```python
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()
```

### ✅ DO: Use Transactions for Multi-Step Operations

```python
@with_transaction()
def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    from_account = session.query(Account).get(from_id)
    to_account = session.query(Account).get(to_id)
    
    from_account.balance -= amount
    to_account.balance += amount
    # Atomic - both succeed or both fail
```

### ❌ DON'T: Mix Session Management Patterns

```python
# BAD - Confusing
@with_session()
def create_user(session: Session, name: str):
    # Then manually getting another session
    another_session = manager.engine.get_session()
    # ...
```

---

## Error Handling

### ✅ DO: Handle Specific Exceptions

```python
from sqlalchemy_engine_kit import (
    DatabaseManagerNotInitializedError,
    DatabaseConnectionError,
    DatabaseQueryError
)

try:
    manager = DatabaseManager()
    engine = manager.engine
except DatabaseManagerNotInitializedError:
    logger.error("Database not initialized")
    # Initialize or exit
except DatabaseConnectionError:
    logger.error("Cannot connect to database")
    # Retry or use fallback
```

### ✅ DO: Use Retry for Transient Errors

```python
from sqlalchemy_engine_kit import with_retry, with_session
from sqlalchemy.exc import OperationalError

@with_retry(max_attempts=3, retry_on=(OperationalError,))
@with_session(auto_commit=True)
def critical_operation(session: Session):
    # Will retry on connection errors
    pass
```

### ❌ DON'T: Swallow All Exceptions

```python
# BAD
@with_session()
def create_user(session: Session, name: str):
    try:
        user = User(name=name)
        session.add(user)
        session.commit()
    except Exception:
        pass  # Silent failure - BAD!
```

### ✅ DO: Log Errors with Context

```python
from sqlalchemy_engine_kit import LoggerAdapter
import logging

logger = LoggerAdapter.get_logger()

@with_session()
def create_user(session: Session, name: str):
    try:
        user = User(name=name)
        session.add(user)
        session.commit()
    except Exception as e:
        logger.error(f"Failed to create user: {e}", extra={
            'user_name': name,
            'operation': 'create_user'
        })
        raise
```

---

## Performance

### ✅ DO: Use Bulk Operations

```python
from sqlalchemy_engine_kit import bulk_insert

@with_session(auto_commit=True)
def import_users(session: Session, user_data: list):
    users = [User(name=d['name']) for d in user_data]
    bulk_insert(session, users)  # Much faster
```

### ❌ DON'T: Insert One by One

```python
# BAD - Slow
@with_session(auto_commit=True)
def import_users(session: Session, user_data: list):
    for d in user_data:
        user = User(name=d['name'])
        session.add(user)  # Slow!
```

### ✅ DO: Use Eager Loading

```python
from sqlalchemy_engine_kit import with_relationships

@with_session(readonly=True)
def get_user_with_orders(session: Session, user_id: int):
    user = session.query(User).filter_by(id=user_id).first()
    with_relationships(user, 'orders')  # Load all at once
    
    for order in user.orders:  # No N+1 queries
        print(order.total)
```

### ❌ DON'T: Cause N+1 Queries

```python
# BAD - N+1 problem
@with_session(readonly=True)
def get_users_with_orders(session: Session):
    users = session.query(User).all()
    for user in users:
        for order in user.orders:  # New query for each user!
            print(order.total)
```

### ✅ DO: Use Pagination

```python
from sqlalchemy_engine_kit import paginate_with_meta

@with_session(readonly=True)
def list_users(session: Session, page: int = 1):
    result = paginate_with_meta(
        session.query(User),
        page=page,
        per_page=20
    )
    return result.items
```

### ❌ DON'T: Load All Records

```python
# BAD - Memory issues
@with_session(readonly=True)
def list_users(session: Session):
    return session.query(User).all()  # Could be millions!
```

### ✅ DO: Configure Connection Pool

```python
from sqlalchemy_engine_kit import EngineConfig

engine_config = EngineConfig(
    pool_size=20,  # Adjust based on your needs
    max_overflow=10,
    pool_pre_ping=True  # Check connections
)

config = get_postgresql_config(..., engine_config=engine_config)
```

---

## Testing

### ✅ DO: Use In-Memory Database for Tests

```python
import pytest
from sqlalchemy_engine_kit import DatabaseManager, get_sqlite_config

@pytest.fixture
def test_manager():
    manager = DatabaseManager()
    manager.initialize(get_sqlite_config(":memory:"), auto_start=True)
    yield manager
    manager.reset(full_reset=True)
```

### ✅ DO: Reset Between Tests

```python
@pytest.fixture(autouse=True)
def reset_db(test_manager):
    yield
    test_manager.reset()  # Clean state for each test
```

### ✅ DO: Use Fixtures for Common Data

```python
@pytest.fixture
def sample_user(session):
    user = User(name="Test User")
    session.add(user)
    session.commit()
    return user
```

### ❌ DON'T: Use Production Database for Tests

```python
# BAD - Never do this!
@pytest.fixture
def test_manager():
    manager = DatabaseManager()
    manager.initialize(get_postgresql_config(
        db_name="production_db",  # NO!
        ...
    ))
```

---

## Security

### ✅ DO: Use Environment Variables

```python
import os
from sqlalchemy_engine_kit import get_postgresql_config

config = get_postgresql_config(
    db_name=os.getenv('DB_NAME'),
    host=os.getenv('DB_HOST'),
    username=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')  # Never hardcode!
)
```

### ❌ DON'T: Hardcode Credentials

```python
# BAD - Security risk!
config = get_postgresql_config(
    db_name="myapp",
    username="admin",
    password="password123"  # Never!
)
```

### ✅ DO: Use SSL for Production

```python
config = get_postgresql_config(
    db_name="myapp",
    host="prod-db.example.com",
    username="user",
    password="pass",
    # Add SSL configuration
    sslmode="require"
)
```

### ✅ DO: Sanitize Logs

```python
# engine-kit automatically excludes passwords from logs
config.to_dict(exclude_password=True)  # Safe to log
```

### ❌ DON'T: Log Connection Strings

```python
# BAD
logger.info(f"Connecting to: {config.get_connection_string()}")  # Contains password!
```

---

## Common Pitfalls

### 1. Forgetting to Initialize

```python
# BAD
manager = DatabaseManager()
engine = manager.engine  # Error: Not initialized!

# GOOD
manager = DatabaseManager()
manager.initialize(config, auto_start=True)
engine = manager.engine  # OK
```

### 2. Using Wrong Session

```python
# BAD
@with_session()
def create_user(session: Session, name: str):
    # Getting another session inside
    another_session = manager.engine.get_session()
    # Confusing and error-prone

# GOOD
@with_session()
def create_user(session: Session, name: str):
    user = User(name=name)
    session.add(user)
    # Use the injected session
```

### 3. Not Handling Errors in Transactions

```python
# BAD
@with_transaction()
def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    from_account = session.query(Account).get(from_id)
    to_account = session.query(Account).get(to_id)
    
    from_account.balance -= amount
    to_account.balance += amount
    # What if to_account doesn't exist? No error handling!

# GOOD
@with_transaction()
def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    from_account = session.query(Account).get(from_id)
    if not from_account:
        raise ValueError("From account not found")
    
    to_account = session.query(Account).get(to_id)
    if not to_account:
        raise ValueError("To account not found")
    
    if from_account.balance < amount:
        raise ValueError("Insufficient balance")
    
    from_account.balance -= amount
    to_account.balance += amount
```

### 4. Not Using Readonly for Queries

```python
# BAD - Unnecessary write transaction
@with_session(auto_commit=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()

# GOOD - Readonly
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()
```

---

## Anti-Patterns

### ❌ Anti-Pattern 1: Global Session

```python
# BAD - Don't do this
global_session = None

def init():
    global global_session
    global_session = manager.engine.get_session()

def create_user(name: str):
    global global_session
    user = User(name=name)
    global_session.add(user)  # Thread-unsafe!
```

### ❌ Anti-Pattern 2: Session Leaks

```python
# BAD - Session not closed
def process_data():
    session = manager.engine.get_session()
    # ... use session
    # Forgot to close! Memory leak!
```

### ❌ Anti-Pattern 3: Nested Transactions

```python
# BAD - Confusing transaction boundaries
@with_transaction()
def outer_function(session: Session):
    @with_transaction()
    def inner_function(session: Session):
        # Nested transactions - confusing!
        pass
    inner_function(session)
```

### ❌ Anti-Pattern 4: Mixing ORM and Raw SQL

```python
# BAD - Inconsistent
@with_session()
def get_user(session: Session, user_id: int):
    # Using ORM
    user = session.query(User).filter_by(id=user_id).first()
    
    # Then raw SQL
    result = session.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
    # Inconsistent and harder to maintain
```

### ❌ Anti-Pattern 5: Ignoring Connection Pool Settings

```python
# BAD - Default settings might not be optimal
manager.initialize(config)  # Using defaults

# GOOD - Configure for your needs
engine_config = EngineConfig(
    pool_size=20,  # Based on your concurrency
    max_overflow=10,
    pool_pre_ping=True
)
config = get_postgresql_config(..., engine_config=engine_config)
manager.initialize(config)
```

---

## Code Organization

### ✅ DO: Organize by Feature

```
myapp/
├── models/
│   ├── user.py
│   └── post.py
├── queries/
│   ├── user_queries.py
│   └── post_queries.py
├── services/
│   ├── user_service.py
│   └── post_service.py
└── db.py  # Database initialization
```

### ✅ DO: Organize Queries in Helper Functions

```python
# queries/user_queries.py
from sqlalchemy_engine_kit import with_session, with_readonly_session
from sqlalchemy.orm import Session

@with_readonly_session()
def find_user_by_email(session: Session, email: str) -> User:
    return session.query(User).filter_by(email=email).first()

@with_readonly_session()
def find_active_users(session: Session):
    return session.query(User).filter_by(is_active=True).all()
```

### ✅ DO: Separate Business Logic

```python
# services/user_service.py
from sqlalchemy_engine_kit import with_session
from queries.user_queries import find_user_by_email

class UserService:
    @staticmethod
    @with_session(auto_commit=True)
    def create_user(session: Session, email: str, name: str):
        # Check if email exists
        existing_user = find_user_by_email(session, email)
        if existing_user:
            raise ValueError("Email already exists")
        
        # Create new user
        user = User(email=email, name=name)
        session.add(user)
        session.flush()
        return user
```

---

## Monitoring and Observability

### ✅ DO: Use Health Checks

```python
from sqlalchemy_engine_kit import DatabaseManager

manager = DatabaseManager()
health = manager.engine.health_check()

if health['status'] != 'healthy':
    # Alert or take action
    logger.warning(f"Database unhealthy: {health}")
```

### ✅ DO: Monitor Connection Pool

```python
health = manager.engine.health_check()
pool_stats = health['details']

if pool_stats['checked_out'] > pool_stats['pool_size'] * 0.8:
    logger.warning("Connection pool nearly exhausted")
```

### ✅ DO: Track Query Performance

```python
from sqlalchemy_engine_kit import PrometheusMonitor

monitor = PrometheusMonitor()
manager.initialize(config, monitor=monitor)

# Queries are automatically tracked
# Check Prometheus metrics: engine_kit_query_duration_seconds
```

---

## Summary

### ✅ DO:
- Initialize once at startup
- Use decorators for session management
- Handle errors properly
- Use bulk operations
- Configure connection pool
- Use environment variables for credentials
- Use readonly sessions for queries
- Use transactions for multi-step operations

### ❌ DON'T:
- Initialize multiple times
- Manually manage sessions (unless necessary)
- Swallow exceptions
- Insert one by one
- Load all records
- Hardcode credentials
- Use production DB for tests
- Mix session management patterns

---

**Remember:** engine-kit is designed to make database operations easier and safer. Follow these practices to get the most out of it!

