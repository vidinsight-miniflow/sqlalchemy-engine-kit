"""
Unit tests for models module
"""

import pytest
from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy_engine_kit.models import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    model_to_dict,
    model_to_json,
    models_to_list,
)
from tests.fixtures.sample_models import User, Post, SimpleModel


class TestBase:
    """Tests for Base declarative class."""
    
    def test_base_inheritance(self):
        """Test that Base is DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)
    
    def test_base_metadata(self):
        """Test that Base has metadata."""
        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None
    
    def test_model_creation(self):
        """Test creating a model with Base."""
        class TestModel(Base):
            __tablename__ = 'test_models'
            id = Column(Integer, primary_key=True)
            name = Column(String(255))
        
        assert TestModel.__tablename__ == 'test_models'
        assert hasattr(TestModel, 'id')
        assert hasattr(TestModel, 'name')


class TestTimestampMixin:
    """Tests for TimestampMixin."""
    
    def test_timestamp_mixin_adds_fields(self):
        """Test that TimestampMixin adds created_at and updated_at."""
        class TestModel(Base, TimestampMixin):
            __tablename__ = 'test_timestamp'
            id = Column(Integer, primary_key=True)
        
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')
    
    def test_timestamp_auto_set(self, test_session):
        """Test that timestamps are automatically set."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(email="test@example.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        # Timestamps should be very close (within 1 second)
        time_diff = abs((user.updated_at - user.created_at).total_seconds())
        assert time_diff < 1.0
    
    def test_timestamp_updates_on_modify(self, test_session):
        """Test that updated_at changes on update."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(email="test@example.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        original_updated = user.updated_at
        
        # Update user
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        user.name = "Updated Name"
        test_session.flush()
        
        assert user.updated_at >= original_updated


class TestSoftDeleteMixin:
    """Tests for SoftDeleteMixin."""
    
    def test_soft_delete_mixin_adds_fields(self):
        """Test that SoftDeleteMixin adds is_deleted and deleted_at."""
        class TestModel(Base, SoftDeleteMixin):
            __tablename__ = 'test_soft_delete'
            id = Column(Integer, primary_key=True)
        
        assert hasattr(TestModel, 'is_deleted')
        assert hasattr(TestModel, 'deleted_at')
    
    def test_soft_delete_defaults(self, test_session):
        """Test that soft delete fields have correct defaults."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(email="test@example.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        assert user.is_deleted is False
        assert user.deleted_at is None
    
    def test_soft_delete_method(self, test_session):
        """Test soft_delete method."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(email="test@example.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        user.soft_delete()
        test_session.flush()
        
        assert user.is_deleted is True
        assert user.deleted_at is not None
        assert isinstance(user.deleted_at, datetime)
    
    def test_restore_method(self, test_session):
        """Test restore method."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(email="test@example.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        user.soft_delete()
        test_session.flush()
        
        assert user.is_deleted is True
        
        user.restore()
        test_session.flush()
        
        assert user.is_deleted is False
        assert user.deleted_at is None


class TestAuditMixin:
    """Tests for AuditMixin."""
    
    def test_audit_mixin_adds_fields(self):
        """Test that AuditMixin adds created_by and updated_by."""
        class TestModel(Base, AuditMixin):
            __tablename__ = 'test_audit'
            id = Column(Integer, primary_key=True)
        
        assert hasattr(TestModel, 'created_by')
        assert hasattr(TestModel, 'updated_by')
    
    def test_audit_fields_optional(self, test_session):
        """Test that audit fields are optional."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hash"
        )
        test_session.add(user)
        test_session.flush()
        
        # Fields can be None
        assert user.created_by is None or isinstance(user.created_by, str)
        assert user.updated_by is None or isinstance(user.updated_by, str)
    
    def test_audit_fields_set(self, test_session):
        """Test setting audit fields."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            created_by="admin",
            updated_by="admin"
        )
        test_session.add(user)
        test_session.flush()
        
        assert user.created_by == "admin"
        assert user.updated_by == "admin"


class TestModelSerialization:
    """Tests for model serialization functions."""
    
    def test_model_to_dict_basic(self, test_session):
        """Test basic model_to_dict conversion."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = SimpleModel(name="Test", value=42)
        test_session.add(user)
        test_session.flush()
        
        result = model_to_dict(user)
        assert isinstance(result, dict)
        assert result["id"] == user.id
        assert result["name"] == "Test"
        assert result["value"] == 42
    
    def test_model_to_dict_exclude_fields(self, test_session):
        """Test model_to_dict with exclude parameter."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="secret"
        )
        test_session.add(user)
        test_session.flush()
        
        result = model_to_dict(user, exclude=["password_hash"])
        assert "password_hash" not in result
        assert "email" in result
        assert "name" in result
    
    def test_model_to_dict_with_timestamps(self, test_session):
        """Test model_to_dict with timestamp fields."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hash"
        )
        test_session.add(user)
        test_session.flush()
        
        result = model_to_dict(user)
        assert "created_at" in result
        assert "updated_at" in result
        # datetime is serialized to ISO format string
        assert isinstance(result["created_at"], str)
        assert "T" in result["created_at"] or "-" in result["created_at"]  # ISO format
    
    def test_model_to_json_basic(self, test_session):
        """Test basic model_to_json conversion."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = SimpleModel(name="Test", value=42)
        test_session.add(user)
        test_session.flush()
        
        result = model_to_json(user)
        assert isinstance(result, str)
        assert "Test" in result
        assert "42" in result
    
    def test_model_to_json_exclude_fields(self, test_session):
        """Test model_to_json with exclude parameter."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="secret"
        )
        test_session.add(user)
        test_session.flush()
        
        result = model_to_json(user, exclude=["password_hash"])
        assert "password_hash" not in result
        assert "email" in result
    
    def test_models_to_list(self, test_session):
        """Test models_to_list conversion."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        users = [
            SimpleModel(name=f"User {i}", value=i)
            for i in range(3)
        ]
        for user in users:
            test_session.add(user)
        test_session.flush()
        
        result = models_to_list(users)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)
        assert result[0]["name"] == "User 0"
        assert result[1]["name"] == "User 1"
        assert result[2]["name"] == "User 2"
    
    def test_models_to_list_exclude_fields(self, test_session):
        """Test models_to_list with exclude parameter."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        users = [
            User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                password_hash="hash"
            )
            for i in range(2)
        ]
        for user in users:
            test_session.add(user)
        test_session.flush()
        
        result = models_to_list(users, exclude=["password_hash"])
        assert len(result) == 2
        assert all("password_hash" not in item for item in result)
        assert all("email" in item for item in result)
    
    def test_model_to_dict_with_relationships(self, test_session):
        """Test model_to_dict with relationships."""
        # Create tables
        Base.metadata.create_all(test_session.bind)
        
        user = User(
            email="test@example.com",
            name="Test User",
            password_hash="hash"
        )
        test_session.add(user)
        test_session.flush()
        
        post = Post(
            title="Test Post",
            content="Content",
            user_id=user.id
        )
        test_session.add(post)
        test_session.flush()
        
        # Test without relationships
        result = model_to_dict(user, include_relationships=False)
        assert "posts" not in result
        
        # Test with relationships
        result = model_to_dict(user, include_relationships=True, max_depth=1)
        assert "posts" in result
        assert isinstance(result["posts"], list)
        assert len(result["posts"]) == 1

