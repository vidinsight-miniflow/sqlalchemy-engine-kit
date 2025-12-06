"""
Sample SQLAlchemy models for testing
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from sqlalchemy_engine_kit.models import Base, TimestampMixin, SoftDeleteMixin, AuditMixin


class User(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Sample User model with all mixins."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Relationships
    posts = relationship('Post', back_populates='user', cascade='all, delete-orphan')
    comments = relationship('Comment', back_populates='user', cascade='all, delete-orphan')


class Post(Base, TimestampMixin, SoftDeleteMixin):
    """Sample Post model with relationships."""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')


class Comment(Base, TimestampMixin):
    """Sample Comment model."""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='comments')
    post = relationship('Post', back_populates='comments')


class SimpleModel(Base):
    """Simple model without mixins for basic tests."""
    __tablename__ = 'simple_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    value = Column(Integer, default=0)

