# Architecture Guide

Technical architecture and design decisions for engine-kit.

## Table of Contents

- [Overview](#overview)
- [Core Components](#core-components)
- [Design Patterns](#design-patterns)
- [Thread Safety](#thread-safety)
- [Connection Pooling](#connection-pooling)
- [Session Management](#session-management)
- [Error Handling](#error-handling)
- [Extension Points](#extension-points)

---

## Overview

engine-kit is a **convenience layer** on top of SQLAlchemy that provides:

1. **Simplified Session Management**: Decorators and context managers
2. **Singleton Pattern**: Application-wide database engine instance
3. **Direct Session Queries**: SQLAlchemy ORM queries with decorators
4. **Production Features**: Monitoring, logging, health checks

### Architecture Layers

```
┌─────────────────────────────────────────┐
│      Application Layer                   │
│  (Your code using decorators/repos)     │
├─────────────────────────────────────────┤
│      engine-kit Layer                    │
│  • Decorators (@with_session)           │
│  • DatabaseManager (Singleton)          │
│  • DatabaseEngine (Pool Management)     │
│  • Repositories (CRUD)                  │
├─────────────────────────────────────────┤
│      SQLAlchemy Layer                   │
│  • ORM (Models, Sessions)               │
│  • Engine (Connection Pool)             │
├─────────────────────────────────────────┤
│      Database Driver Layer              │
│  • psycopg2 (PostgreSQL)                │
│  • pymysql (MySQL)                       │
│  • sqlite3 (SQLite)                      │
├─────────────────────────────────────────┤
│      Database                            │
│  • PostgreSQL / MySQL / SQLite          │
└─────────────────────────────────────────┘
```

---

## Core Components

### 1. DatabaseManager

**Purpose**: Singleton pattern ile uygulama genelinde tek engine instance'ı yönetir.

**Key Features**:
- Thread-safe singleton
- Double-checked locking pattern
- Lifecycle management (initialize, start, stop)

**Implementation**:
```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Why Singleton?**
- Connection pooling efficiency
- Single source of truth
- Easier configuration management

### 2. DatabaseEngine

**Purpose**: SQLAlchemy Engine wrapper - connection pooling ve session yönetimi.

**Key Features**:
- Connection pool management
- Session factory
- Health checks
- Graceful shutdown

**Lifecycle**:
```
1. __init__(config)     → Create engine (not started)
2. start()              → Create connection pool
3. session_context()    → Create sessions
4. stop()               → Close all connections
```

### 3. Decorators

**Purpose**: Otomatik session ve transaction yönetimi.

**Implementation Flow**:
```
@with_session()
def my_function(session: Session, ...):
    # 1. Get DatabaseManager instance
    # 2. Get DatabaseEngine
    # 3. Create session context
    # 4. Inject session parameter
    # 5. Execute function
    # 6. Commit/rollback based on decorator
    # 7. Close session
```

**Decorator Stack**:
```python
@with_retry(max_attempts=3)
@with_transaction()
def critical_operation(session: Session):
    # Retry wrapper
    #   Transaction wrapper
    #     Session creation
    #       Your function
```

### 4. Repositories

**Purpose**: Generic CRUD operations ve query building.

**Design**:
- Direct SQLAlchemy ORM queries
- Decorator-based session management
- Type-safe with SQLAlchemy's type system

**Example**:
```python
@with_session()
def get_user_by_id(session: Session, user_id: int) -> User:
    return session.query(User).filter_by(id=user_id).first()
```

---

## Design Patterns

### 1. Singleton Pattern

**Used in**: `DatabaseManager`

**Why?**
- Single connection pool per application
- Consistent configuration
- Resource efficiency

**Implementation**:
- Double-checked locking
- Thread-safe
- Lazy initialization

### 2. Decorator Pattern for Session Management

**Used in**: `@with_session`, `@with_transaction`, `@with_readonly_session`

**Why?**
- Separation of concerns (session lifecycle)
- Testability (easy to mock)
- Reusability (consistent session handling)

**Benefits**:
- Business logic separated from session management
- Easy to test (inject mock sessions)
- Consistent session handling across application

### 3. Decorator Pattern

**Used in**: `@with_session`, `@with_transaction`

**Why?**
- Cross-cutting concerns (session management)
- Clean code (no boilerplate)
- Composable (stack decorators)

### 4. Strategy Pattern

**Used in**: Monitoring (`BaseMonitor`)

**Why?**
- Pluggable monitoring backends
- Easy to extend
- No coupling to specific monitoring system

**Example**:
```python
# Strategy interface
class BaseMonitor:
    def record_query_duration(self, duration: float, query: str):
        pass

# Concrete strategies
class NoOpMonitor(BaseMonitor): ...
class PrometheusMonitor(BaseMonitor): ...
class CustomMonitor(BaseMonitor): ...
```

---

## Thread Safety

### Singleton Thread Safety

**Problem**: Multiple threads creating singleton simultaneously.

**Solution**: Double-checked locking pattern.

```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:  # First check (no lock)
            with cls._lock:        # Acquire lock
                if cls._instance is None:  # Second check (with lock)
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### Session Thread Safety

**Problem**: SQLAlchemy sessions are not thread-safe.

**Solution**: Each thread gets its own session.

```python
@with_session()
def my_function(session: Session):
    # Each call creates a new session
    # Sessions are not shared between threads
    pass
```

### Connection Pool Thread Safety

**Problem**: Connection pool must be thread-safe.

**Solution**: SQLAlchemy's connection pool is thread-safe by design.

```python
# SQLAlchemy handles thread safety internally
engine = create_engine(...)  # Thread-safe pool
```

---

## Connection Pooling

### Pool Architecture

```
┌─────────────────────────────────────┐
│      Connection Pool                 │
│  ┌─────────┐  ┌─────────┐          │
│  │ Conn 1  │  │ Conn 2  │  ...     │
│  └─────────┘  └─────────┘          │
│       │            │                 │
│  ┌──────────────────────────┐       │
│  │   Overflow Pool           │       │
│  │  (Temporary connections) │       │
│  └──────────────────────────┘       │
└─────────────────────────────────────┘
```

### Pool Lifecycle

1. **Initialization**: Pool created with `pool_size` connections
2. **Checkout**: Session requests connection from pool
3. **Usage**: Connection used for queries
4. **Checkin**: Connection returned to pool
5. **Overflow**: If pool exhausted, create temporary connection
6. **Cleanup**: Idle connections closed after timeout

### Configuration

```python
EngineConfig(
    pool_size=10,        # Base pool size
    max_overflow=20,      # Max temporary connections
    pool_timeout=30,     # Wait time for connection
    pool_pre_ping=True   # Validate connections
)
```

### Health Monitoring

```python
health = engine.health_check()
# Returns:
# {
#   "status": "healthy",
#   "details": {
#     "pool_size": 10,
#     "checked_out": 3,
#     "overflow": 0,
#     "checked_in": 7
#   }
# }
```

---

## Session Management

### Session Lifecycle

```
1. Create Session
   ↓
2. Add/Query Objects
   ↓
3. Flush (optional)
   ↓
4. Commit or Rollback
   ↓
5. Close Session
```

### Decorator Flow

```python
@with_session(auto_commit=True)
def create_user(session: Session, name: str):
    # 1. Decorator creates session context
    # 2. Session injected as parameter
    # 3. Function executes
    # 4. If auto_commit=True and no exception:
    #    - session.commit()
    # 5. If exception:
    #    - session.rollback()
    # 6. Session closed (context manager)
```

### Context Manager Flow

```python
with engine.session_context() as session:
    # 1. Session created
    # 2. Enter context
    # 3. Use session
    # 4. Exit context
    # 5. Session closed (if not committed)
```

---

## Error Handling

### Exception Hierarchy

```
EngineKitError (base)
├── InvalidInputError
└── DatabaseError
    ├── DatabaseConfigError
    ├── DatabaseConnectionError
    ├── DatabaseQueryError
    ├── DatabaseSessionError
    ├── DatabaseTransactionError
    ├── DatabasePoolError
    ├── DatabaseHealthError
    ├── DatabaseManagerError
    │   ├── DatabaseManagerNotInitializedError
    │   └── DatabaseManagerAlreadyInitializedError
    └── DatabaseMigrationError
```

### Error Propagation

```python
try:
    @with_session()
    def create_user(session: Session, name: str):
        user = User(name=name)
        session.add(user)
        session.commit()
except DatabaseSessionError as e:
    # Handled by decorator (rollback)
    # Re-raised to caller
    logger.error(f"Session error: {e}")
    raise
```

### Retry Logic

```python
@with_retry(max_attempts=3, retry_on=(OperationalError,))
@with_session()
def critical_operation(session: Session):
    # On OperationalError:
    # 1. Rollback current transaction
    # 2. Wait (exponential backoff)
    # 3. Retry (up to max_attempts)
    pass
```

---

## Extension Points

### 1. Custom Monitor

```python
class CustomMonitor(BaseMonitor):
    def record_query_duration(self, duration: float, query: str):
        # Your implementation
        pass
    
    def record_error(self, error: Exception, context: dict):
        # Your implementation
        pass

# Use it
monitor = CustomMonitor()
manager.initialize(config, monitor=monitor)
```

### 2. Custom Logger

```python
from sqlalchemy_engine_kit import LoggerAdapter
import logging

# Use your logger
LoggerAdapter.set_logger(logging.getLogger("myapp"))
```

### 3. Custom Repository

```python
@with_session()
def find_user_by_email(session: Session, email: str) -> User:
    return session.query(User).filter_by(email=email).first()

@with_session()
def find_active_users(session: Session):
    return session.query(User).filter_by(is_active=True).all()
```

### 4. Custom Decorators

```python
from functools import wraps
from sqlalchemy_engine_kit import DatabaseManager

def with_custom_session(**kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            manager = DatabaseManager()
            with manager.engine.session_context(**kwargs) as session:
                return func(*args, session=session, **kw)
        return wrapper
    return decorator
```

---

## Performance Considerations

### 1. Connection Pool Sizing

**Rule of thumb**: `pool_size = (threads * 2) + 1`

```python
# For 10 concurrent threads
pool_size = (10 * 2) + 1 = 21
```

### 2. Session Management

**Best**: Use decorators (automatic cleanup)
**Good**: Use context managers
**Avoid**: Manual session management

### 3. Query Optimization

- Use eager loading to avoid N+1
- Use pagination for large result sets
- Use bulk operations for inserts/updates

### 4. Monitoring

- Track query duration
- Monitor connection pool usage
- Alert on pool exhaustion

---

## Security Considerations

### 1. Credential Management

- Never hardcode credentials
- Use environment variables
- Use secrets manager in production

### 2. Connection Security

- Use SSL/TLS for database connections
- Validate certificates
- Use connection string sanitization

### 3. SQL Injection Prevention

- Always use SQLAlchemy ORM (parameterized queries)
- Never use raw SQL with user input
- Validate input before queries

---

## Testing Architecture

### Test Isolation

```python
@pytest.fixture
def test_manager():
    # Each test gets fresh manager
    manager = DatabaseManager()
    manager.initialize(get_sqlite_config(":memory:"))
    yield manager
    manager.reset(full_reset=True)  # Clean singleton
```

### Mocking

```python
# Mock DatabaseManager
@patch('sqlalchemy_engine_kit.DatabaseManager')
def test_with_mock(mock_manager):
    mock_manager.return_value.engine.session_context.return_value.__enter__.return_value = mock_session
    # Test your code
```

---

## Future Considerations

### Async Support

**Planned**: Async/await support with `asyncpg` and `aiomysql`

```python
# Future API
@with_async_session()
async def create_user(session: AsyncSession, name: str):
    user = User(name=name)
    session.add(user)
    await session.commit()
```

### Query Caching

**Planned**: Optional query result caching layer

```python
# Future API
@with_cache(ttl=300)
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).get(user_id)
```

---

## Summary

engine-kit's architecture is designed for:

1. **Simplicity**: Easy to use, hard to misuse
2. **Performance**: Efficient connection pooling and session management
3. **Extensibility**: Pluggable monitoring and logging
4. **Reliability**: Thread-safe, error handling, retry logic
5. **Production-Ready**: Health checks, monitoring, graceful shutdown

The architecture follows SOLID principles and common design patterns to provide a robust, maintainable, and extensible foundation for database operations.

---

**Last Updated**: 2024
**Version**: 0.1.0

