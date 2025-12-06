#!/usr/bin/env python3
"""
Basic Usage Example - sqlalchemy-engine-kit

Bu örnek, sqlalchemy-engine-kit'in temel kullanımını gösterir.
"""

from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_sqlite_config,
    with_session,
    with_readonly_session,
    Base,
    TimestampMixin,
)
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session


# 1. Model Tanımlama
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)


# 2. Database Başlatma
def init_database():
    """Database'i başlat."""
    import os
    db_file = "example.db"
    # Önceki database dosyasını sil (temiz başlangıç için)
    if os.path.exists(db_file):
        os.remove(db_file)
    
    config = get_sqlite_config(db_file)
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    
    # Tabloları oluştur
    Base.metadata.create_all(manager.engine._engine)
    print("✅ Database initialized and tables created")
    
    return manager


# 3. Decorator ile Session Kullanımı
@with_session()
def create_user(session: Session, name: str, email: str) -> int:
    """Kullanıcı oluştur ve ID döndür."""
    user = User(name=name, email=email)
    session.add(user)
    session.flush()
    user_id = user.id  # ID'yi session içinde al
    print(f"✅ Created user: {user.name} (ID: {user_id})")
    return user_id


@with_readonly_session()
def get_user(session: Session, user_id: int) -> User:
    """Kullanıcı getir."""
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        print(f"✅ Found user: {user.name} ({user.email})")
    else:
        print(f"❌ User with ID {user_id} not found")
    return user


@with_session()
def list_users(session: Session):
    """Tüm kullanıcıları listele."""
    users = session.query(User).all()
    print(f"✅ Total users: {len(users)}")
    for user in users:
        print(f"   - {user.name} ({user.email})")
    return users


# 4. Ana Program
def main():
    """Ana program."""
    print("=" * 60)
    print("sqlalchemy-engine-kit Basic Usage Example")
    print("=" * 60)
    
    # Database başlat
    manager = init_database()
    
    # Kullanıcı oluştur
    print("\n1. Creating users...")
    user1_id = create_user(name="John Doe", email="john@example.com")
    user2_id = create_user(name="Jane Smith", email="jane@example.com")
    user3_id = create_user(name="Bob Wilson", email="bob@example.com")
    
    # Kullanıcı getir
    print("\n2. Getting user...")
    retrieved = get_user(user_id=user1_id)
    
    # Tüm kullanıcıları listele
    print("\n3. Listing all users...")
    all_users = list_users()
    
    # Cleanup
    print("\n4. Cleaning up...")
    manager.stop()
    print("✅ Database stopped")
    
    print("\n" + "=" * 60)
    print("Example completed successfully! ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()

