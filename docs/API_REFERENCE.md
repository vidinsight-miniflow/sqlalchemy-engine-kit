# API Reference

Complete API documentation for engine-kit.

## Table of Contents

- [DatabaseManager](#databasemanager)
- [DatabaseEngine](#databaseengine)
- [Decorators](#decorators)
- [Configuration](#configuration)
- [Models](#models)
- [Repositories](#repositories)
- [Migrations](#migrations)
- [Monitoring](#monitoring)
- [Logging](#logging)
- [Exceptions](#exceptions)

---

## DatabaseManager

Singleton pattern ile uygulama genelinde tek bir database engine instance'ı yönetir.

### Class: `DatabaseManager`

```python
from sqlalchemy_engine_kit import DatabaseManager

manager = DatabaseManager()
```

#### Methods

##### `initialize(config, auto_start=True, create_tables=None, force_reinitialize=False, monitor=None)`

Database engine'i başlatır.

**Parameters:**
- `config` (DatabaseConfig): Database konfigürasyonu
- `auto_start` (bool, optional): Engine'i otomatik başlat. Default: `True`
- `create_tables` (Any, optional): Metadata objesi - tabloları oluşturur. Default: `None`
- `force_reinitialize` (bool, optional): Zaten initialize edilmişse yeniden initialize et. Default: `False`
- `monitor` (BaseMonitor, optional): Custom monitor instance. Default: `None` (NoOpMonitor kullanır)

**Raises:**
- `DatabaseManagerAlreadyInitializedError`: Zaten initialize edilmişse (force_reinitialize=False ise)

**Example:**
```python
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, PrometheusMonitor

config = get_postgresql_config(db_name="myapp", host="localhost", username="user", password="pass")
monitor = PrometheusMonitor()

manager = DatabaseManager()
manager.initialize(config, auto_start=True, monitor=monitor)
```

##### `get_instance(config=None, auto_start=True)`

Singleton instance'ı döndürür. İlk çağrıda config verilirse initialize eder.

**Parameters:**
- `config` (DatabaseConfig, optional): İlk çağrıda gerekli
- `auto_start` (bool, optional): Default: `True`

**Returns:**
- `DatabaseManager`: Singleton instance

**Example:**
```python
# İlk çağrı
manager = DatabaseManager.get_instance(config, auto_start=True)

# Sonraki çağrılar
manager = DatabaseManager.get_instance()  # Aynı instance
```

##### `start()`

Engine'i başlatır.

**Raises:**
- `DatabaseManagerNotInitializedError`: Initialize edilmemişse

##### `stop()`

Engine'i durdurur. Idempotent.

##### `reset(full_reset=False)`

Engine'i durdurur ve temizler.

**Parameters:**
- `full_reset` (bool, optional): Singleton instance'ı da temizler. Default: `False`

**Example:**
```python
# Test sonrası temizlik
manager.reset(full_reset=True)
```

##### `get_health_status()`

Manager ve engine'in sağlık durumunu döndürür.

**Returns:**
```python
{
    "manager_initialized": bool,
    "engine_started": bool,
    "engine_health": dict  # DatabaseEngine.health_check() sonucu
}
```

#### Properties

##### `engine: DatabaseEngine`

Database engine instance'ına erişim.

**Raises:**
- `DatabaseManagerNotInitializedError`: Initialize edilmemişse

##### `is_started: bool`

Engine'in başlatılmış olup olmadığını kontrol eder.

##### `is_initialized: bool`

Manager'ın initialize edilmiş olup olmadığını kontrol eder.

---

## DatabaseEngine

SQLAlchemy engine wrapper - connection pooling, session management, health checks.

### Class: `DatabaseEngine`

```python
from sqlalchemy_engine_kit import DatabaseEngine, DatabaseConfig

engine = DatabaseEngine(config)
```

#### Methods

##### `start()`

Engine'i başlatır ve connection pool oluşturur.

**Raises:**
- `DatabaseEngineError`: Başlatma hatası

##### `stop()`

Engine'i durdurur ve tüm bağlantıları kapatır. Idempotent.

##### `session_context(auto_commit=False)`

Session context manager döndürür.

**Parameters:**
- `auto_commit` (bool, optional): Otomatik commit. Default: `False`

**Returns:**
- Context manager: SQLAlchemy Session

**Example:**
```python
with engine.session_context() as session:
    user = User(name="John")
    session.add(user)
    session.commit()
```

##### `get_session()`

Yeni bir session döndürür. Manuel yönetim gerekir.

**Returns:**
- `Session`: SQLAlchemy session

**Warning:** Session'ı manuel kapatmayı unutmayın!

##### `create_tables(metadata)`

Tabloları oluşturur.

**Parameters:**
- `metadata`: SQLAlchemy MetaData objesi

**Example:**
```python
from sqlalchemy_engine_kit import Base

engine.create_tables(Base.metadata)
```

##### `health_check()`

Database bağlantısını kontrol eder.

**Returns:**
```python
{
    "status": "healthy" | "unhealthy" | "degraded" | "stopped",
    "message": str,
    "details": {
        "pool_size": int,
        "checked_out": int,
        "overflow": int,
        "checked_in": int
    }
}
```

**Example:**
```python
health = engine.health_check()
if health["status"] == "healthy":
    print("Database is ready!")
```

#### Properties

##### `_engine: Engine`

SQLAlchemy Engine instance'ına doğrudan erişim (advanced kullanım).

---

## Decorators

Otomatik session ve transaction yönetimi için decorator'lar.

### `@with_session(auto_commit=False, readonly=False)`

Fonksiyona otomatik session enjekte eder.

**Parameters:**
- `auto_commit` (bool, optional): Başarılı sonuçta otomatik commit. Default: `False`
- `readonly` (bool, optional): Read-only session (commit yapılmaz). Default: `False`

**Function Signature:**
Fonksiyon `session: Session` parametresi içermelidir.

**Example:**
```python
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session

@with_session(auto_commit=True)
def create_user(session: Session, name: str) -> User:
    user = User(name=name)
    session.add(user)
    return user  # Otomatik commit

@with_session(readonly=True)
def get_user(session: Session, user_id: int) -> User:
    return session.query(User).filter_by(id=user_id).first()
```

**Error Handling:**
- Hata durumunda otomatik rollback
- Exception'ı yeniden fırlatır

### `@with_transaction()`

Atomic transaction garantisi sağlar.

**Function Signature:**
Fonksiyon `session: Session` parametresi içermelidir.

**Example:**
```python
from sqlalchemy_engine_kit import with_transaction
from sqlalchemy.orm import Session

@with_transaction()
def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    from_account = session.query(Account).get(from_id)
    to_account = session.query(Account).get(to_id)
    
    from_account.balance -= amount
    to_account.balance += amount
    
    # Hata olursa otomatik rollback
    # Başarılı olursa otomatik commit
```

**Error Handling:**
- Hata durumunda otomatik rollback
- Exception'ı yeniden fırlatır

### `@with_readonly_session()`

Read-only session sağlar (commit yapılmaz).

**Example:**
```python
from sqlalchemy_engine_kit import with_readonly_session
from sqlalchemy.orm import Session

@with_readonly_session()
def list_users(session: Session) -> list[User]:
    return session.query(User).all()
```

### `@with_retry(max_attempts=3, retry_on=(DeadlockDetected, TimeoutError))`

Retry logic ekler.

**Parameters:**
- `max_attempts` (int, optional): Maksimum deneme sayısı. Default: `3`
- `retry_on` (tuple, optional): Retry yapılacak exception'lar. Default: `(DeadlockDetected, TimeoutError)`

**Example:**
```python
from sqlalchemy_engine_kit import with_retry, with_session
from sqlalchemy.orm import Session

@with_retry(max_attempts=5)
@with_session(auto_commit=True)
def update_user(session: Session, user_id: int, name: str):
    user = session.query(User).get(user_id)
    user.name = name
    # Deadlock olursa otomatik retry
```

---

## Configuration

Database ve engine konfigürasyonu.

### `DatabaseConfig`

Database bağlantı bilgileri.

```python
from sqlalchemy_engine_kit import DatabaseConfig, DatabaseType

config = DatabaseConfig(
    db_type=DatabaseType.POSTGRESQL,
    db_name="myapp",
    host="localhost",
    port=5432,
    username="user",
    password="password"
)
```

**Parameters:**
- `db_type` (DatabaseType): Database tipi (SQLITE, POSTGRESQL, MYSQL)
- `db_name` (str): Database adı
- `host` (str, optional): Host (network databases için)
- `port` (int, optional): Port (network databases için)
- `username` (str, optional): Kullanıcı adı (network databases için)
- `password` (str, optional): Şifre (network databases için)

**Methods:**
- `get_connection_string() -> str`: Connection string döndürür
- `to_dict(exclude_password=True) -> dict`: Dict'e çevirir

### `EngineConfig`

Engine ve connection pool ayarları.

```python
from sqlalchemy_engine_kit import EngineConfig

engine_config = EngineConfig(
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=False
)
```

**Parameters:**
- `pool_size` (int, optional): Pool boyutu. Default: `5`
- `max_overflow` (int, optional): Maksimum overflow. Default: `10`
- `pool_timeout` (int, optional): Timeout (saniye). Default: `30`
- `pool_pre_ping` (bool, optional): Connection check. Default: `True`
- `echo` (bool, optional): SQL loglama. Default: `False`

**Presets:**
```python
# Development
config = EngineConfig.for_development()

# High concurrency
config = EngineConfig.for_high_concurrency()

# Testing
config = EngineConfig.for_testing()
```

### Factory Functions

#### `get_sqlite_config(db_name=":memory:")`

SQLite config oluşturur.

```python
from sqlalchemy_engine_kit import get_sqlite_config

config = get_sqlite_config("myapp.db")
```

#### `get_postgresql_config(db_name, host="localhost", port=5432, username=None, password=None)`

PostgreSQL config oluşturur.

```python
from sqlalchemy_engine_kit import get_postgresql_config

config = get_postgresql_config(
    db_name="myapp",
    host="localhost",
    username="user",
    password="pass"
)
```

#### `get_mysql_config(db_name, host="localhost", port=3306, username=None, password=None)`

MySQL config oluşturur.

```python
from sqlalchemy_engine_kit import get_mysql_config

config = get_mysql_config(
    db_name="myapp",
    host="localhost",
    username="user",
    password="pass"
)
```

---

## Models

Base model ve mixin'ler.

### `Base`

SQLAlchemy declarative base.

```python
from sqlalchemy_engine_kit import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
```

### `TimestampMixin`

`created_at` ve `updated_at` alanları ekler.

```python
from sqlalchemy_engine_kit import Base, TimestampMixin
from sqlalchemy import Column, Integer, String

class Post(Base, TimestampMixin):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    # created_at ve updated_at otomatik eklenir
```

**Fields:**
- `created_at` (DateTime): Oluşturulma zamanı
- `updated_at` (DateTime): Güncellenme zamanı

### `SoftDeleteMixin`

Soft delete desteği ekler.

```python
from sqlalchemy_engine_kit import Base, SoftDeleteMixin

class User(Base, SoftDeleteMixin):
    __tablename__ = 'users'
    # deleted_at ve is_deleted otomatik eklenir
```

**Fields:**
- `deleted_at` (DateTime, nullable): Silinme zamanı
- `is_deleted` (bool): Silinmiş mi?

**Methods:**
- `soft_delete()`: Soft delete yapar
- `restore()`: Geri yükler

**Example:**
```python
user = User(name="John")
session.add(user)
session.commit()

user.soft_delete()  # deleted_at set edilir
session.commit()

# Query'de otomatik filtrelenir (is_deleted=False)
users = session.query(User).all()  # Silinenler gelmez
```

### `AuditMixin`

Audit alanları ekler (created_by, updated_by).

```python
from sqlalchemy_engine_kit import Base, AuditMixin

class Document(Base, AuditMixin):
    __tablename__ = 'documents'
    # created_by, updated_by otomatik eklenir
```

**Fields:**
- `created_by` (String, nullable): Oluşturan
- `updated_by` (String, nullable): Güncelleyen

### Serialization

#### `model_to_dict(model, exclude_fields=None)`

Model'i dict'e çevirir.

```python
from sqlalchemy_engine_kit import model_to_dict

user = User(name="John", email="john@example.com")
data = model_to_dict(user, exclude_fields=["password"])
# {"id": 1, "name": "John", "email": "john@example.com"}
```

#### `models_to_list(models, exclude_fields=None)`

Model listesini dict listesine çevirir.

```python
from sqlalchemy_engine_kit import models_to_list

users = session.query(User).all()
data = models_to_list(users)
# [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
```

#### `model_to_json(model, exclude_fields=None)`

Model'i JSON string'e çevirir.

```python
from sqlalchemy_engine_kit import model_to_json

user = User(name="John")
json_str = model_to_json(user)
```

---

## Direct Session Queries

Repository pattern is not included in this version. Use direct SQLAlchemy ORM queries with decorators.

### Example Usage

```python
from sqlalchemy_engine_kit import with_session, with_readonly_session
from sqlalchemy.orm import Session

@with_session()
def create_user(session: Session, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    session.flush()
    return user

@with_readonly_session()
def get_user_by_id(session: Session, user_id: int) -> User:
    return session.query(User).filter_by(id=user_id).first()

@with_readonly_session()
def get_all_users(session: Session, limit: int = None, offset: int = None):
    query = session.query(User)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return query.all()
```

##### `create(**kwargs) -> T`

Yeni kayıt oluşturur.

##### `update(id, **kwargs) -> T`

Günceller.

##### `delete(id) -> None`

Siler (soft delete varsa soft delete yapar).

##### `filter(**kwargs) -> Query`

Filtreleme query'si döndürür.

##### `exists(id) -> bool`

Var mı kontrol eder.

**Example:**
```python
@with_session()
def example(session: Session):
    # Create
    user = User(name="John", email="john@example.com")
    session.add(user)
    session.flush()
    
    # Read
    user = session.query(User).filter_by(id=user.id).first()
    users = session.query(User).limit(10).all()
    
    # Update
    user.name = "John Updated"
    session.flush()
    
    # Delete
    session.delete(user)
    session.flush()
    
    # Custom query
    user = session.query(User).filter_by(email="john@example.com").first()
```

---

## Migrations

Alembic migration yönetimi.

### `MigrationManager`

Migration yönetimi için manager.

```python
from sqlalchemy_engine_kit import MigrationManager, DatabaseEngine

manager = MigrationManager(engine, script_location="migrations")
```

**Methods:**

##### `get_current_revision() -> str | None`

Mevcut revision'ı döndürür.

##### `get_head_revision() -> str | None`

Head revision'ı döndürür.

##### `upgrade(target="head")`

Upgrade yapar.

##### `downgrade(target)`

Downgrade yapar.

##### `stamp(revision)`

Revision'ı stamp eder.

### Helper Functions

#### `run_migrations(engine, script_location, target="head")`

Migration çalıştırır.

```python
from sqlalchemy_engine_kit import run_migrations

run_migrations(engine, script_location="migrations")
```

#### `create_migration(script_location, message)`

Yeni migration oluşturur.

```python
from sqlalchemy_engine_kit import create_migration

create_migration("migrations", "add_user_table")
```

#### `get_current_revision(engine, script_location) -> str | None`

Mevcut revision'ı döndürür.

#### `get_head_revision(script_location) -> str | None`

Head revision'ı döndürür.

---

## Monitoring

Pluggable monitoring interface.

### `BaseMonitor`

Base monitor interface.

```python
from sqlalchemy_engine_kit import BaseMonitor

class CustomMonitor(BaseMonitor):
    def record_query_duration(self, duration: float, query: str):
        # Custom implementation
        pass
    
    def record_error(self, error: Exception, context: dict):
        # Custom implementation
        pass
```

**Methods:**
- `record_query_duration(duration, query)`
- `record_error(error, context)`
- `record_session_count(count)`
- `record_connection_pool_stats(stats)`

### `NoOpMonitor`

Default monitor (hiçbir şey yapmaz).

```python
from sqlalchemy_engine_kit import NoOpMonitor

monitor = NoOpMonitor()
```

### `PrometheusMonitor`

Prometheus metrics.

```python
from sqlalchemy_engine_kit import PrometheusMonitor

monitor = PrometheusMonitor()
manager.initialize(config, monitor=monitor)
```

**Metrics:**
- `engine_kit_query_duration_seconds`
- `engine_kit_errors_total`
- `engine_kit_sessions_active`
- `engine_kit_pool_size`
- `engine_kit_pool_checked_out`

---

## Logging

Modular logging.

### `LoggerAdapter`

Logger adapter.

```python
from sqlalchemy_engine_kit import LoggerAdapter
import logging

# Custom logger kullan
LoggerAdapter.set_logger(logging.getLogger("myapp"))

# Veya default logger
logger = LoggerAdapter.get_logger()
```

**Methods:**
- `set_logger(logger)`: Custom logger set et
- `get_logger() -> Logger`: Logger al

---

## Exceptions

Exception hierarchy.

### Base Exceptions

- `EngineKitError`: Base exception
- `InvalidInputError`: Geçersiz input
- `DatabaseError`: Database hataları

### Database Exceptions

- `DatabaseConfigError`: Config hatası
- `DatabaseConnectionError`: Bağlantı hatası
- `DatabaseQueryError`: Query hatası
- `DatabaseSessionError`: Session hatası
- `DatabaseTransactionError`: Transaction hatası
- `DatabasePoolError`: Pool hatası
- `DatabaseHealthError`: Health check hatası

### Manager Exceptions

- `DatabaseManagerError`: Manager hatası
- `DatabaseManagerNotInitializedError`: Initialize edilmemiş
- `DatabaseManagerAlreadyInitializedError`: Zaten initialize edilmiş

### Migration Exceptions

- `DatabaseMigrationError`: Migration hatası

**Example:**
```python
from sqlalchemy_engine_kit import DatabaseManagerNotInitializedError

try:
    manager = DatabaseManager()
    engine = manager.engine
except DatabaseManagerNotInitializedError:
    print("Manager not initialized!")
```

---

## Quick Reference

### Common Patterns

```python
# 1. Initialize
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config

config = get_postgresql_config(db_name="myapp", host="localhost", username="user", password="pass")
manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# 2. Define models
from sqlalchemy_engine_kit import Base, TimestampMixin
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

# 3. Create tables
manager.engine.create_tables(Base.metadata)

# 4. Use with decorators
from sqlalchemy_engine_kit import with_session
@with_session(auto_commit=True)
def create_user(session, name):
    user = User(name=name)
    session.add(user)
    return user

# 5. Use direct queries
@with_session()
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()

@with_session()
def find_user_by_email(session: Session, email: str):
    return session.query(User).filter_by(email=email).first()

@with_session()
def example(session: Session):
    # Create
    user = User(name="John", email="john@example.com")
    session.add(user)
    session.flush()
    
    # Find
    return session.query(User).filter_by(email="john@example.com").first()
```

---

**Last Updated:** 2024
**Version:** 0.1.0

