# Quick Start Guide

Get up and running with engine-kit in 5 minutes!

## Installation

```bash
# Install from source (until published to PyPI)
pip install git+https://github.com/vidinsight/sqlalchemy-engine-kit.git

# Or clone and install locally
git clone https://github.com/vidinsight/sqlalchemy-engine-kit.git
cd vidinsight-sqlalchemy-engine-kit
pip install -e .

# Install with optional dependencies
pip install -e ".[postgres]"     # PostgreSQL support
pip install -e ".[mysql]"        # MySQL support
pip install -e ".[migrations]"   # Alembic migrations
pip install -e ".[monitoring]"   # Prometheus monitoring
pip install -e ".[all]"          # Everything
```

## 5-Minute Tutorial

### Step 1: Configure Database (30 seconds)

```python
from sqlalchemy_engine_kit import get_sqlite_config, get_postgresql_config

# SQLite (for development/testing)
config = get_sqlite_config("myapp.db")

# Or PostgreSQL (for production)
config = get_postgresql_config(
    db_name="myapp",
    host="localhost",
    username="myuser",
    password="mypassword"
)
```

### Step 2: Initialize Manager (30 seconds)

```python
from sqlalchemy_engine_kit import DatabaseManager

# Initialize once at application startup
manager = DatabaseManager()
manager.initialize(config, auto_start=True)
```

### Step 3: Define Models (1 minute)

```python
from sqlalchemy_engine_kit import Base, TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Integer, String

class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

# Create tables
manager.engine.create_tables(Base.metadata)
```

### Step 4: Use Database (3 minutes)

#### Option A: With Decorators (Recommended)

```python
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session

@with_session()
def create_user(session: Session, email: str, name: str) -> User:
    user = User(email=email, name=name)
    session.add(user)
    session.flush()
    return user

@with_session()
def get_user(session: Session, user_id: int) -> User:
    return session.query(User).filter_by(id=user_id).first()

# Use them
user = create_user(email="test@example.com", name="Test User")
retrieved = get_user(user_id=user.id)
print(f"User: {retrieved.name}")
```

#### Option B: Direct Session Queries

```python
from sqlalchemy_engine_kit import with_session
from sqlalchemy.orm import Session

@with_session()
def example(session: Session):
    # Create
    user = User(email="test@example.com", name="Test User")
    session.add(user)
    session.flush()
    
    # Read
    user = session.query(User).filter_by(id=user.id).first()
    
    # Update
    user.name = "Updated Name"
    session.flush()
    
    # Delete
    session.delete(user)
    session.flush()
    
    # Find by email
    user = session.query(User).filter_by(email="test@example.com").first()
    
    return user
```

#### Option C: With Context Manager

```python
def create_user_manual(email: str, name: str) -> User:
    manager = DatabaseManager.get_instance()
    
    with manager.engine.session_context() as session:
        user = User(email=email, name=name)
        session.add(user)
        session.flush()
        return user
```

## Complete Example Application

```python
# app.py
from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_postgresql_config,
    with_session,
    Base,
    TimestampMixin,
    # Direct SQLAlchemy queries
)
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Session

# 1. Define Models
class Post(Base, TimestampMixin):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=False)

# 2. Define helper functions
def find_posts_by_author(session: Session, author: str):
    return session.query(Post).filter_by(author=author).all()

# 3. Initialize Database
def init_database():
    config = get_postgresql_config(
        db_name="blog",
        host="localhost",
        username="bloguser",
        password="blogpass"
    )
    
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)
    
    print("Database initialized!")

# 4. Application Functions
@with_session()
def create_post(session: Session, title: str, content: str, author: str) -> Post:
    post = Post(title=title, content=content, author=author)
    session.add(post)
    session.flush()
    return post

@with_session()
def get_all_posts(session: Session):
    return session.query(Post).all()

@with_session()
def get_posts_by_author(session: Session, author: str):
    return find_posts_by_author(session, author)

@with_session()
def update_post(session: Session, post_id: int, **kwargs) -> Post:
    post = session.query(Post).filter_by(id=post_id).first()
    if post:
        for key, value in kwargs.items():
            setattr(post, key, value)
        session.flush()
    return post

# 5. Run Application
if __name__ == "__main__":
    # Initialize
    init_database()
    
    # Create posts
    post1 = create_post(
        title="First Post",
        content="This is my first post!",
        author="John Doe"
    )
    post2 = create_post(
        title="Second Post",
        content="Another great post!",
        author="John Doe"
    )
    
    # Query posts
    all_posts = get_all_posts()
    print(f"Total posts: {len(all_posts)}")
    
    john_posts = get_posts_by_author("John Doe")
    print(f"John's posts: {len(john_posts)}")
    
    # Update post
    updated = update_post(post1.id, title="Updated First Post")
    print(f"Updated: {updated.title}")
    
    # Cleanup
    manager = DatabaseManager.get_instance()
    manager.stop()
```

## Testing Your Code

```python
# test_app.py
import pytest
from sqlalchemy_engine_kit import DatabaseManager, get_sqlite_config, Base

@pytest.fixture(scope="function")
def test_db():
    """Setup test database."""
    config = get_sqlite_config(":memory:")
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    manager.engine.create_tables(Base.metadata)
    
    yield manager
    
    manager.reset()

def test_create_user(test_db):
    user = create_user(email="test@test.com", name="Test")
    assert user.email == "test@test.com"
    assert user.name == "Test"
```

## Common Patterns

### Pattern 1: Bulk Operations

```python
from sqlalchemy_engine_kit import with_session, bulk_insert

@with_session()
def import_users(session: Session, users_data: list):
    return bulk_insert(session, User, users_data)

# Use it
users_data = [
    {"email": "user1@example.com", "name": "User 1"},
    {"email": "user2@example.com", "name": "User 2"},
    {"email": "user3@example.com", "name": "User 3"},
]
imported = import_users(users_data)
```

### Pattern 2: Pagination

```python
from sqlalchemy_engine_kit import with_session, paginate_with_meta

@with_session()
def get_users_page(session: Session, page: int = 1, page_size: int = 10):
    query = session.query(User).filter_by(is_deleted=False)
    return paginate_with_meta(query, page=page, page_size=page_size)

# Use it
result = get_users_page(page=1, page_size=10)
print(f"Total: {result.total}, Page: {result.page}/{result.total_pages}")
for user in result.items:
    print(user.name)
```

### Pattern 3: Transactions

```python
from sqlalchemy_engine_kit import with_transaction

@with_transaction()
def transfer_points(session: Session, from_user_id: int, to_user_id: int, points: int):
    """Atomic transfer - either both succeed or both fail."""
    from_user = session.query(User).get(from_user_id)
    to_user = session.query(User).get(to_user_id)
    
    from_user.points -= points
    to_user.points += points
    
    # If anything fails, automatic rollback
    # If success, automatic commit
```

### Pattern 4: Retry on Deadlock

```python
from sqlalchemy_engine_kit import with_retry_session

@with_retry_session(max_retries=3, retry_on_deadlock=True)
def update_counter(session: Session, counter_id: int):
    """Automatically retries on deadlock."""
    counter = session.query(Counter).get(counter_id)
    counter.value += 1
    session.commit()
```

## Next Steps

- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide
- 🔍 Read [LOGGING_AND_MONITORING.md](LOGGING_AND_MONITORING.md) for observability
- 🚨 Read [RUNBOOK.md](RUNBOOK.md) for troubleshooting common issues
- 🧪 Run tests: `pytest tests/`
- 📝 Check examples in `examples/` directory (if available)

## Getting Help

- Check [RUNBOOK.md](RUNBOOK.md) for common issues
- Read docstrings in code (they're comprehensive!)
- Open an issue on GitHub
- Contact the maintainers

## Common Gotchas

1. **Always initialize manager at startup**
   ```python
   # ✅ GOOD
   manager = DatabaseManager()
   manager.initialize(config, auto_start=True)
   
   # ❌ BAD - Initialize before using
   manager = DatabaseManager()
   manager.engine  # Error: Not initialized!
   ```

2. **Use decorators or context managers**
   ```python
   # ✅ GOOD
   @with_session()
   def get_user(session, user_id):
       return session.query(User).get(user_id)
   
   # ❌ BAD - Manual session management is error-prone
   session = manager.engine.get_session()
   user = session.query(User).get(user_id)
   session.close()  # Might not run if exception!
   ```

3. **Don't create multiple managers**
   ```python
   # ✅ GOOD - Singleton pattern
   manager = DatabaseManager()  # Same instance every time
   
   # ❌ BAD - Trying to create multiple
   manager1 = DatabaseManager()
   manager2 = DatabaseManager()
   # They're the same instance! Use the singleton.
   ```

## Performance Tips

1. Use eager loading to avoid N+1 queries:
   ```python
   from sqlalchemy_engine_kit import eager_load
   
   users = eager_load(
       session.query(User),
       'posts', 'posts.comments'
   ).all()
   ```

2. Use bulk operations for many inserts:
   ```python
   bulk_insert(session, User, users_data)  # Much faster!
   ```

3. Configure appropriate pool size:
   ```python
   from sqlalchemy_engine_kit import EngineConfig
   
   config = EngineConfig(
       pool_size=20,  # Adjust based on load
       max_overflow=10
   )
   ```

Happy coding! 🚀

