# Examples

Real-world usage examples and integrations.

## Table of Contents

- [Flask Integration](#flask-integration)
- [FastAPI Integration](#fastapi-integration)
- [Django Integration](#django-integration)
- [CLI Application](#cli-application)
- [Background Jobs](#background-jobs)
- [Testing](#testing)
- [Advanced Patterns](#advanced-patterns)

---

## Flask Integration

### Basic Setup

```python
# app.py
from flask import Flask
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, with_session, Base
from sqlalchemy.orm import Session

app = Flask(__name__)

# Initialize database on startup
@app.before_first_request
def init_db():
    config = get_postgresql_config(
        db_name=app.config['DB_NAME'],
        host=app.config['DB_HOST'],
        username=app.config['DB_USER'],
        password=app.config['DB_PASSWORD']
    )
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)

# Cleanup on shutdown
@app.teardown_appcontext
def close_db(error):
    # Sessions are automatically managed
    pass

# Use in routes
@app.route('/users', methods=['POST'])
@with_session(auto_commit=True)
def create_user(session: Session):
    from models import User
    user = User(name=request.json['name'])
    session.add(user)
    return jsonify({'id': user.id, 'name': user.name}), 201

@app.route('/users/<int:user_id>')
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    from models import User
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user.id, 'name': user.name})
```

### With Direct Session Queries

```python
# routes.py
from flask import Blueprint, request, jsonify
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['POST'])
@with_session()
def create_user(session: Session):
    user = User(
        name=request.json['name'],
        email=request.json['email']
    )
    session.add(user)
    session.flush()
    return jsonify({'id': user.id}), 201

@users_bp.route('/users/<int:user_id>')
@with_readonly_session()
def get_user(session: Session, user_id: int):
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user.id, 'name': user.name})
```

---

## FastAPI Integration

### Basic Setup

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, with_session, Base
from sqlalchemy.orm import Session

app = FastAPI()

# Initialize on startup
@app.on_event("startup")
async def startup():
    config = get_postgresql_config(
        db_name="myapp",
        host="localhost",
        username="user",
        password="pass"
    )
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)

# Dependency for session
def get_session():
    manager = DatabaseManager()
    with manager.engine.session_context() as session:
        yield session

# Use in endpoints
@app.post("/users")
async def create_user(user_data: dict, session: Session = Depends(get_session)):
    from models import User
    user = User(name=user_data['name'], email=user_data['email'])
    session.add(user)
    session.commit()
    return {"id": user.id, "name": user.name}

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: Session = Depends(get_session)):
    from models import User
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name}
```

### With Dependency Injection

```python
# dependencies.py
from sqlalchemy_engine_kit import DatabaseManager
from sqlalchemy.orm import Session

def get_db():
    manager = DatabaseManager()
    with manager.engine.session_context() as session:
        yield session

# queries.py
from sqlalchemy_engine_kit import with_readonly_session
from sqlalchemy.orm import Session

@with_readonly_session()
def find_user_by_email(session: Session, email: str) -> User:
    return session.query(User).filter_by(email=email).first()

# routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
router = APIRouter()

@router.post("/users")
async def create_user(user_data: dict, session: Session = Depends(get_db)):
    user = User(**user_data)
    session.add(user)
    session.flush()
    return {"id": user.id}

@router.get("/users/{user_id}")
async def get_user(user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return {"id": user.id, "name": user.name}
```

---

## Django Integration

### Custom Database Backend

```python
# myapp/db.py
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config
from django.conf import settings

def init_engine_kit():
    config = get_postgresql_config(
        db_name=settings.DATABASES['default']['NAME'],
        host=settings.DATABASES['default']['HOST'],
        username=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    return manager

# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        from .db import init_engine_kit
        self.engine_manager = init_engine_kit()

# views.py
from django.http import JsonResponse
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session

@with_session(auto_commit=True)
def create_user_view(request, session: Session):
    from models import User
    user = User(name=request.POST['name'])
    session.add(user)
    return JsonResponse({'id': user.id, 'name': user.name})
```

---

## CLI Application

### Simple CLI Tool

```python
# cli.py
import click
from sqlalchemy_engine_kit import DatabaseManager, get_sqlite_config, with_session, Base
from sqlalchemy.orm import Session

# Initialize once
manager = DatabaseManager()
manager.initialize(get_sqlite_config("cli.db"), auto_start=True)
manager.engine.create_tables(Base.metadata)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('name')
@with_session(auto_commit=True)
def create_user(session: Session, name: str):
    """Create a new user."""
    from models import User
    user = User(name=name)
    session.add(user)
    click.echo(f"Created user: {user.id}")

@cli.command()
@with_session(readonly=True)
def list_users(session: Session):
    """List all users."""
    from models import User
    users = session.query(User).all()
    for user in users:
        click.echo(f"{user.id}: {user.name}")

if __name__ == '__main__':
    cli()
```

### Advanced CLI with Repository

```python
# cli.py
import click
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, with_session
from sqlalchemy.orm import Session
from repositories import UserRepository

manager = DatabaseManager()
manager.initialize(get_postgresql_config(...), auto_start=True)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', required=True)
@click.option('--email', required=True)
@with_session(auto_commit=True)
def add_user(session: Session, name: str, email: str):
    """Add a new user."""
    repo = UserRepository(session)
    user = repo.create(name=name, email=email)
    click.echo(f"Added user: {user.id}")

@cli.command()
@click.argument('user_id', type=int)
@with_session(readonly=True)
def show_user(session: Session, user_id: int):
    """Show user details."""
    repo = UserRepository(session)
    user = repo.get_by_id(user_id)
    if not user:
        click.echo("User not found", err=True)
        return
    click.echo(f"ID: {user.id}")
    click.echo(f"Name: {user.name}")
    click.echo(f"Email: {user.email}")
```

---

## Background Jobs

### Celery Integration

```python
# tasks.py
from celery import Celery
from sqlalchemy_engine_kit import DatabaseManager, with_session
from sqlalchemy.orm import Session

celery = Celery('tasks')

@celery.task
@with_session(auto_commit=True)
def process_user(session: Session, user_id: int):
    """Process user in background."""
    from models import User
    from repositories import UserRepository
    
    repo = UserRepository(session)
    user = repo.get_by_id(user_id)
    
    if not user:
        return {"error": "User not found"}
    
    # Do some processing
    user.processed = True
    session.flush()
    
    return {"status": "processed", "user_id": user.id}
```

### Simple Background Worker

```python
# worker.py
import time
from sqlalchemy_engine_kit import DatabaseManager, with_session
from sqlalchemy.orm import Session

manager = DatabaseManager()
manager.initialize(get_postgresql_config(...), auto_start=True)

@with_session(auto_commit=True)
def process_queue(session: Session):
    """Process items from queue."""
    from models import Task
    tasks = session.query(Task).filter_by(status='pending').limit(10).all()
    
    for task in tasks:
        task.status = 'processing'
        session.flush()
        
        # Do work
        result = do_work(task)
        
        task.status = 'completed'
        task.result = result
        session.flush()

if __name__ == '__main__':
    while True:
        process_queue()
        time.sleep(5)
```

---

## Testing

### Pytest Fixtures

```python
# conftest.py
import pytest
from sqlalchemy_engine_kit import DatabaseManager, get_sqlite_config, Base

@pytest.fixture(scope="session")
def db_manager():
    """Create database manager for tests."""
    config = get_sqlite_config(":memory:")
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)
    yield manager
    manager.reset(full_reset=True)

@pytest.fixture
def session(db_manager):
    """Create a test session."""
    with db_manager.engine.session_context() as session:
        yield session
```

### Unit Tests

```python
# test_users.py
import pytest
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session
from models import User

@pytest.fixture
def sample_user(session):
    """Create a sample user."""
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    session.commit()
    return user

def test_create_user(session):
    """Test user creation."""
    user = User(name="John", email="john@example.com")
    session.add(user)
    session.commit()
    
    assert user.id is not None
    assert user.name == "John"

def test_get_user(session, sample_user):
    """Test getting user."""
    user = session.query(User).filter_by(id=sample_user.id).first()
    assert user is not None
    assert user.name == "Test User"

@with_session(auto_commit=True)
def test_with_decorator(session: Session):
    """Test with decorator."""
    user = User(name="Decorator Test")
    session.add(user)
    # Auto-commit happens here
    assert user.id is not None
```

### Integration Tests

```python
# test_integration.py
import pytest
from sqlalchemy_engine_kit import DatabaseManager, get_sqlite_config, with_session
from sqlalchemy.orm import Session

@pytest.fixture
def test_manager():
    """Test manager."""
    manager = DatabaseManager()
    manager.initialize(get_sqlite_config(":memory:"), auto_start=True)
    yield manager
    manager.reset(full_reset=True)

def test_manager_singleton():
    """Test singleton pattern."""
    manager1 = DatabaseManager()
    manager2 = DatabaseManager()
    assert manager1 is manager2

@with_session(auto_commit=True)
def test_transaction(session: Session):
    """Test transaction."""
    from models import User, Order
    
    user = User(name="Test")
    session.add(user)
    session.flush()
    
    order = Order(user_id=user.id, total=100.0)
    session.add(order)
    # Both committed together
```

---

## Advanced Patterns

### Multi-Database Support

```python
# multi_db.py
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config

# Primary database
primary_manager = DatabaseManager()
primary_manager.initialize(
    get_postgresql_config(db_name="primary", ...),
    auto_start=True
)

# Secondary database (analytics)
secondary_config = get_postgresql_config(db_name="analytics", ...)
secondary_engine = DatabaseEngine(secondary_config)
secondary_engine.start()

# Use in code
@with_session(auto_commit=True)
def write_to_primary(session: Session):
    # Uses primary_manager
    pass

def write_to_secondary():
    with secondary_engine.session_context() as session:
        # Uses secondary_engine
        pass
```

### Custom Monitor

```python
# custom_monitor.py
from sqlalchemy_engine_kit import BaseMonitor
import datadog

class DatadogMonitor(BaseMonitor):
    def record_query_duration(self, duration: float, query: str):
        datadog.statsd.histogram(
            'engine_kit.query.duration',
            duration,
            tags=[f'query:{query[:50]}']
        )
    
    def record_error(self, error: Exception, context: dict):
        datadog.statsd.increment(
            'engine_kit.errors',
            tags=[f'error_type:{type(error).__name__}']
        )
    
    def record_session_count(self, count: int):
        datadog.statsd.gauge('engine_kit.sessions.active', count)
    
    def record_connection_pool_stats(self, stats: dict):
        datadog.statsd.gauge('engine_kit.pool.size', stats['pool_size'])
        datadog.statsd.gauge('engine_kit.pool.checked_out', stats['checked_out'])

# Use it
monitor = DatadogMonitor()
manager.initialize(config, monitor=monitor)
```

### Retry Logic

```python
# retry_example.py
from sqlalchemy_engine_kit import with_retry, with_session
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

@with_retry(max_attempts=5, retry_on=(OperationalError,))
@with_session(auto_commit=True)
def critical_operation(session: Session, user_id: int):
    """Critical operation with retry."""
    from models import User
    user = session.query(User).get(user_id)
    user.balance += 100  # Important operation
    # Will retry on connection errors
```

### Bulk Operations

```python
# bulk_ops.py
from sqlalchemy_engine_kit import bulk_insert, bulk_update, with_session
from sqlalchemy.orm import Session

@with_session(auto_commit=True)
def import_users(session: Session, user_data: list):
    """Bulk import users."""
    from models import User
    
    users = [User(name=d['name'], email=d['email']) for d in user_data]
    bulk_insert(session, users)
    # Much faster than individual inserts

@with_session(auto_commit=True)
def update_users(session: Session, updates: dict):
    """Bulk update users."""
    from models import User
    
    bulk_update(
        session,
        User,
        updates,  # {id: {'name': 'New Name'}, ...}
    )
```

### Pagination

```python
# pagination.py
from sqlalchemy_engine_kit import paginate_with_meta, with_session
from sqlalchemy.orm import Session

@with_session(readonly=True)
def list_users(session: Session, page: int = 1, per_page: int = 20):
    """List users with pagination."""
    from models import User
    
    result = paginate_with_meta(
        session.query(User),
        page=page,
        per_page=per_page
    )
    
    return {
        'items': result.items,
        'total': result.total,
        'page': result.page,
        'per_page': result.per_page,
        'pages': result.pages
    }
```

### Eager Loading

```python
# eager_loading.py
from sqlalchemy_engine_kit import with_relationships, with_session
from sqlalchemy.orm import Session

@with_session(readonly=True)
def get_user_with_orders(session: Session, user_id: int):
    """Get user with orders (avoid N+1)."""
    from models import User, Order
    
    user = session.query(User).filter_by(id=user_id).first()
    
    # Eager load orders
    with_relationships(user, 'orders')
    
    # Now accessing user.orders doesn't trigger new queries
    for order in user.orders:
        print(order.total)
```

---

## Complete Example: Blog Application

```python
# blog_app.py
from flask import Flask, request, jsonify
from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_postgresql_config,
    with_session,
    Base,
    TimestampMixin,
    # Direct SQLAlchemy queries
)
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Session, relationship

app = Flask(__name__)

# Models
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    posts = relationship('Post', back_populates='author')

class Post(Base, TimestampMixin):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')

# Query helpers
@with_readonly_session()
def find_posts_by_author(session: Session, author_id: int):
    return session.query(Post).filter_by(author_id=author_id).all()

# Initialize
@app.before_first_request
def init_db():
    config = get_postgresql_config(
        db_name="blog",
        host="localhost",
        username="user",
        password="pass"
    )
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)

# Routes
@app.route('/posts', methods=['POST'])
@with_session(auto_commit=True)
def create_post(session: Session):
    repo = PostRepository(session)
    post = repo.create(
        title=request.json['title'],
        content=request.json['content'],
        author_id=request.json['author_id']
    )
    return jsonify({'id': post.id, 'title': post.title}), 201

@app.route('/posts/<int:post_id>')
@with_session(readonly=True)
def get_post(session: Session, post_id: int):
    repo = PostRepository(session)
    post = repo.get_by_id(post_id)
    if not post:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author_id': post.author_id
    })

@app.route('/users/<int:user_id>/posts')
@with_session(readonly=True)
def get_user_posts(session: Session, user_id: int):
    repo = PostRepository(session)
    posts = repo.find_by_author(user_id)
    return jsonify([{'id': p.id, 'title': p.title} for p in posts])

if __name__ == '__main__':
    app.run(debug=True)
```

---

**More examples coming soon!**

