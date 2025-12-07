# Migration Guide

Guide for migrating from vanilla SQLAlchemy to engine-kit.

## Table of Contents

- [Why Migrate?](#why-migrate)
- [Migration Steps](#migration-steps)
- [Before and After Examples](#before-and-after-examples)
- [Common Migration Patterns](#common-migration-patterns)
- [Troubleshooting](#troubleshooting)

---

## Why Migrate?

### Benefits

1. **Simplified Session Management**: No more manual session handling
2. **Singleton Pattern**: Single engine instance across application
3. **Decorators**: Clean, declarative code
4. **Production Features**: Built-in monitoring, health checks, retry logic
5. **Repository Pattern**: Consistent CRUD operations

### What Stays the Same

- SQLAlchemy ORM (models, relationships, queries)
- Database drivers (psycopg2, pymysql, etc.)
- Migration tools (Alembic)
- Your existing models (with minor adjustments)

---

## Migration Steps

### Step 1: Install engine-kit

```bash
pip install git+https://github.com/vidinsight/sqlalchemy-engine-kit.git
```

### Step 2: Update Imports

**Before:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**After:**
```python
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, Base, with_session
from sqlalchemy.orm import Session
```

### Step 3: Replace Engine Creation

**Before:**
```python
engine = create_engine(
    "postgresql://user:pass@localhost/mydb",
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(bind=engine)
```

**After:**
```python
config = get_postgresql_config(
    db_name="mydb",
    host="localhost",
    username="user",
    password="pass"
)
manager = DatabaseManager()
manager.initialize(config, auto_start=True)
```

### Step 4: Replace Session Management

**Before:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(name: str):
    db = SessionLocal()
    try:
        user = User(name=name)
        db.add(user)
        db.commit()
        return user
    except:
        db.rollback()
        raise
    finally:
        db.close()
```

**After:**
```python
@with_session(auto_commit=True)
def create_user(session: Session, name: str):
    user = User(name=name)
    session.add(user)
    return user  # Auto-commits
```

### Step 5: Update Models (Optional)

**Before:**
```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**After:**
```python
from sqlalchemy_engine_kit import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    # created_at and updated_at automatically added
```

---

## Before and After Examples

### Example 1: Simple CRUD

#### Before (Vanilla SQLAlchemy)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:pass@localhost/mydb")
SessionLocal = sessionmaker(bind=engine)

def create_user(name: str, email: str):
    session = SessionLocal()
    try:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()
        return user
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_user(user_id: int):
    session = SessionLocal()
    try:
        return session.query(User).filter_by(id=user_id).first()
    finally:
        session.close()

def update_user(user_id: int, name: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.name = name
            session.commit()
        return user
    except:
        session.rollback()
        raise
    finally:
        session.close()
```

#### After (engine-kit)

```python
from sqlalchemy_engine_kit import with_session, DatabaseManager, get_postgresql_config
from sqlalchemy.orm import Session

# Initialize once
manager = DatabaseManager()
manager.initialize(get_postgresql_config(...), auto_start=True)

@with_session(auto_commit=True)
def create_user(session: Session, name: str, email: str):
    user = User(name=name, email=email)
    session.add(user)
    return user

@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()

@with_session(auto_commit=True)
def update_user(session: Session, user_id: int, name: str):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.name = name
    return user
```

### Example 2: Flask Application

#### Before (Vanilla SQLAlchemy)

```python
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

app = Flask(__name__)
engine = create_engine("postgresql://user:pass@localhost/mydb")
db_session = scoped_session(sessionmaker(bind=engine))

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/users', methods=['POST'])
def create_user():
    user = User(name=request.json['name'])
    db_session.add(user)
    db_session.commit()
    return jsonify({'id': user.id}), 201

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user.id, 'name': user.name})
```

#### After (engine-kit)

```python
from flask import Flask, request, jsonify
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, with_session, Base
from sqlalchemy.orm import Session

app = Flask(__name__)

@app.before_first_request
def init_db():
    manager = DatabaseManager()
    manager.initialize(get_postgresql_config(...), auto_start=True)
    manager.engine.create_tables(Base.metadata)

@app.route('/users', methods=['POST'])
@with_session(auto_commit=True)
def create_user(session: Session):
    user = User(name=request.json['name'])
    session.add(user)
    return jsonify({'id': user.id}), 201

@app.route('/users/<int:user_id>')
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user.id, 'name': user.name})
```

### Example 3: FastAPI Application

#### Before (Vanilla SQLAlchemy)

```python
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI()
engine = create_engine("postgresql://user:pass@localhost/mydb")
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    user = User(name=user_data['name'])
    db.add(user)
    db.commit()
    return {"id": user.id}
```

#### After (engine-kit)

```python
from fastapi import FastAPI, Depends
from sqlalchemy_engine_kit import DatabaseManager, get_postgresql_config, with_session
from sqlalchemy.orm import Session

app = FastAPI()

@app.on_event("startup")
async def startup():
    manager = DatabaseManager()
    manager.initialize(get_postgresql_config(...), auto_start=True)

def get_session():
    manager = DatabaseManager()
    with manager.engine.session_context() as session:
        yield session

@app.post("/users")
async def create_user(user_data: dict, session: Session = Depends(get_session)):
    user = User(name=user_data['name'])
    session.add(user)
    session.commit()
    return {"id": user.id}
```

### Example 4: Repository Pattern

#### Before (Vanilla SQLAlchemy)

```python
class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, name: str, email: str):
        user = User(name=name, email=email)
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_by_id(self, user_id: int):
        return self.session.query(User).filter_by(id=user_id).first()
    
    def get_all(self):
        return self.session.query(User).all()
    
    def update(self, user_id: int, **kwargs):
        user = self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            self.session.commit()
        return user
    
    def delete(self, user_id: int):
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()

# Usage
session = SessionLocal()
repo = UserRepository(session)
user = repo.create(name="John", email="john@example.com")
session.close()
```

#### After (engine-kit)

```python
from sqlalchemy_engine_kit import with_session, with_readonly_session
from sqlalchemy.orm import Session

@with_readonly_session()
def find_user_by_email(session: Session, email: str):
    return session.query(User).filter_by(email=email).first()

# Usage
@with_session(auto_commit=True)
def example(session: Session):
    repo = UserRepository(session)
    user = repo.create(name="John", email="john@example.com")
    user = repo.get_by_id(user.id)
    users = repo.get_all()
    repo.update(user.id, name="John Updated")
    repo.delete(user.id)
```

---

## Common Migration Patterns

### Pattern 1: Context Manager to Decorator

**Before:**
```python
def create_user(name: str):
    with SessionLocal() as session:
        user = User(name=name)
        session.add(user)
        session.commit()
        return user
```

**After:**
```python
@with_session(auto_commit=True)
def create_user(session: Session, name: str):
    user = User(name=name)
    session.add(user)
    return user
```

### Pattern 2: Manual Session to Decorator

**Before:**
```python
def get_user(user_id: int):
    session = SessionLocal()
    try:
        return session.query(User).filter_by(id=user_id).first()
    finally:
        session.close()
```

**After:**
```python
@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()
```

### Pattern 3: Transaction to Decorator

**Before:**
```python
def transfer_money(from_id: int, to_id: int, amount: float):
    session = SessionLocal()
    try:
        from_account = session.query(Account).get(from_id)
        to_account = session.query(Account).get(to_id)
        from_account.balance -= amount
        to_account.balance += amount
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
```

**After:**
```python
@with_transaction()
def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    from_account = session.query(Account).get(from_id)
    to_account = session.query(Account).get(to_id)
    from_account.balance -= amount
    to_account.balance += amount
    # Auto-commit on success, auto-rollback on error
```

### Pattern 4: Scoped Session to Singleton

**Before:**
```python
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(...)
db_session = scoped_session(sessionmaker(bind=engine))

def get_user(user_id: int):
    return db_session.query(User).filter_by(id=user_id).first()
```

**After:**
```python
from sqlalchemy_engine_kit import DatabaseManager, with_session

manager = DatabaseManager()
manager.initialize(config, auto_start=True)

@with_session(readonly=True)
def get_user(session: Session, user_id: int):
    return session.query(User).filter_by(id=user_id).first()
```

---

## Troubleshooting

### Issue 1: "DatabaseManagerNotInitializedError"

**Problem:**
```python
manager = DatabaseManager()
engine = manager.engine  # Error!
```

**Solution:**
```python
manager = DatabaseManager()
manager.initialize(config, auto_start=True)
engine = manager.engine  # OK
```

### Issue 2: Session Not Injected

**Problem:**
```python
@with_session()
def my_function(name: str):  # Missing session parameter!
    user = User(name=name)
    session.add(user)  # NameError: session not defined
```

**Solution:**
```python
@with_session()
def my_function(session: Session, name: str):  # Add session parameter
    user = User(name=name)
    session.add(user)
```

### Issue 3: Multiple Initializations

**Problem:**
```python
# In different modules
manager1 = DatabaseManager()
manager1.initialize(config1)

manager2 = DatabaseManager()
manager2.initialize(config2)  # Error: Already initialized!
```

**Solution:**
```python
# Initialize once in main module
# app.py
manager = DatabaseManager()
manager.initialize(config, auto_start=True)

# In other modules, just get instance
manager = DatabaseManager()  # Same instance
```

### Issue 4: Models Not Using Base

**Problem:**
```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):  # Different Base!
    pass
```

**Solution:**
```python
from sqlalchemy_engine_kit import Base

class User(Base):  # Use engine-kit Base
    pass
```

### Issue 5: Connection String Format

**Problem:**
```python
# Old way
engine = create_engine("postgresql://user:pass@localhost/db")
```

**Solution:**
```python
# New way
config = get_postgresql_config(
    db_name="db",
    host="localhost",
    username="user",
    password="pass"
)
```

---

## Migration Checklist

- [ ] Install engine-kit
- [ ] Update imports (Base, DatabaseManager, decorators)
- [ ] Replace engine creation with DatabaseManager
- [ ] Replace session management with decorators
- [ ] Update models to use engine-kit Base
- [ ] Replace manual transactions with @with_transaction
- [ ] Update repository classes (if using)
- [ ] Update tests to use test fixtures
- [ ] Update configuration (environment variables)
- [ ] Test all database operations
- [ ] Update deployment configuration
- [ ] Monitor for issues

---

## Gradual Migration

You don't have to migrate everything at once! You can migrate gradually:

### Phase 1: Setup
- Install engine-kit
- Initialize DatabaseManager
- Keep existing code working

### Phase 2: New Code
- Use engine-kit for new features
- Keep old code as-is

### Phase 3: Migrate Gradually
- Migrate one module at a time
- Test thoroughly after each migration

### Phase 4: Cleanup
- Remove old session management code
- Update all models to use engine-kit Base
- Remove unused imports

---

## Getting Help

If you encounter issues during migration:

1. Check [API_REFERENCE.md](API_REFERENCE.md) for correct usage
2. Check [BEST_PRACTICES.md](BEST_PRACTICES.md) for common patterns
3. Check [EXAMPLES.md](EXAMPLES.md) for similar use cases
4. Open an issue on GitHub

---

**Happy Migrating!** 🚀

