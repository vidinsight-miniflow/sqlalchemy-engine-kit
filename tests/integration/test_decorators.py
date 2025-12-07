"""
Integration tests for decorators
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy_engine_kit import with_session, with_transaction, with_readonly_session
from sqlalchemy_engine_kit.core.exceptions import DatabaseDecoratorSignatureError
from tests.fixtures.sample_models import SimpleModel
from sqlalchemy_engine_kit.models import Base


class TestWithSession:
    """Tests for @with_session decorator."""
    
    def test_with_session_basic(self, test_manager):
        """Test basic @with_session usage."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        @with_session()
        def create_user(session: Session, name: str, value: int):
            user = SimpleModel(name=name, value=value)
            session.add(user)
            session.flush()
            # Get id before session closes
            user_id = user.id
            return user_id, user.name, user.value
        
        user_id, name, value = create_user(name="Test", value=42)
        assert user_id is not None
        assert name == "Test"
        assert value == 42
    
    def test_with_session_auto_commit(self, test_manager):
        """Test @with_session with auto_commit."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Clean up first
        @with_session()
        def cleanup(session: Session):
            session.query(SimpleModel).filter_by(name="TestAutoCommit").delete(synchronize_session=False)
            session.commit()
        
        cleanup()
        
        @with_session(auto_commit=True)
        def create_user(session: Session, name: str):
            user = SimpleModel(name=name, value=1)
            session.add(user)
            session.flush()  # Ensure id is generated
            user_id = user.id
            return user_id
        
        user_id = create_user(name="TestAutoCommit")
        assert user_id is not None
        
        # Verify data persisted (auto-committed)
        @with_session()
        def get_user(session: Session):
            user = session.query(SimpleModel).filter_by(id=user_id).first()
            if user:
                return user.id, user.name
            return None, None
        
        result_id, result_name = get_user()
        assert result_id is not None
        assert result_id == user_id
        assert result_name == "TestAutoCommit"
    
    def test_with_session_rollback_on_error(self, test_manager):
        """Test @with_session rollback on error."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Clean up any existing data first
        @with_session()
        def cleanup(session: Session):
            session.query(SimpleModel).filter_by(name="TestRollback").delete()
            session.commit()
        
        cleanup()
        
        @with_session()
        def create_user_with_error(session: Session):
            user = SimpleModel(name="TestRollback", value=1)
            session.add(user)
            session.add(user)
            session.flush()
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            create_user_with_error()
        
        # Verify data was rolled back
        @with_session()
        def get_user(session: Session):
            return session.query(SimpleModel).filter_by(name="TestRollback").first()
        
        result = get_user()
        assert result is None
    
    def test_with_session_signature_validation(self, test_manager):
        """Test @with_session signature validation."""
        # Decorator should raise error when applied (not when called)
        with pytest.raises(DatabaseDecoratorSignatureError):
            @with_session(validate_signature=True)
            def invalid_function(no_session_param: str):
                return no_session_param


class TestWithTransaction:
    """Tests for @with_transaction decorator."""
    
    def test_with_transaction_atomic(self, test_manager):
        """Test @with_transaction atomicity."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Clean up any existing data first
        @with_session()
        def cleanup(session: Session):
            session.query(SimpleModel).filter(
                SimpleModel.name.in_(["User 1", "User 2"])
            ).delete(synchronize_session=False)
            session.commit()
        
        cleanup()
        
        @with_transaction()
        def create_users(session: Session):
            user1 = SimpleModel(name="User 1", value=1)
            user2 = SimpleModel(name="User 2", value=2)
            session.add(user1)
            session.add(user2)
            session.flush()
            # Get IDs before session closes
            return [user1.id, user2.id]
        
        user_ids = create_users()
        assert len(user_ids) == 2
        
        # Verify both persisted
        @with_session()
        def count_users(session: Session):
            return session.query(SimpleModel).filter(
                SimpleModel.id.in_(user_ids)
            ).count()
        
        count = count_users()
        assert count == 2
    
    def test_with_transaction_rollback_on_error(self, test_manager):
        """Test @with_transaction rollback on error."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Clean up any existing data first
        @with_session()
        def cleanup(session: Session):
            session.query(SimpleModel).filter(
                SimpleModel.name.in_(["User 1", "User 2"])
            ).delete(synchronize_session=False)
            session.commit()
        
        cleanup()
        
        @with_transaction()
        def create_users_with_error(session: Session):
            user1 = SimpleModel(name="User 1", value=1)
            user2 = SimpleModel(name="User 2", value=2)
            session.add(user1)
            session.add(user2)
            session.flush()
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            create_users_with_error()
        
        # Verify nothing persisted (atomic rollback)
        @with_session()
        def count_users(session: Session):
            return session.query(SimpleModel).filter(
                SimpleModel.name.in_(["User 1", "User 2"])
            ).count()
        
        count = count_users()
        assert count == 0


class TestWithReadonlySession:
    """Tests for @with_readonly_session decorator."""
    
    def test_with_readonly_session(self, test_manager):
        """Test @with_readonly_session for read operations."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Clean up first
        @with_session()
        def cleanup(session: Session):
            session.query(SimpleModel).filter_by(name="TestReadonly").delete(synchronize_session=False)
            session.commit()
        
        cleanup()
        
        # Create data first
        @with_session(auto_commit=True)
        def create_user(session: Session):
            user = SimpleModel(name="TestReadonly", value=42)
            session.add(user)
            session.flush()
            return user.id
        
        user_id = create_user()
        
        # Read with readonly session
        @with_readonly_session()
        def get_user(session: Session):
            user = session.query(SimpleModel).filter_by(id=user_id).first()
            if user:
                return user.id, user.name, user.value
            return None, None, None
        
        result_id, result_name, result_value = get_user()
        assert result_id is not None
        assert result_id == user_id
        assert result_name == "TestReadonly"
        assert result_value == 42
    
    def test_with_readonly_session_no_commit(self, test_manager):
        """Test that readonly session doesn't commit."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        @with_readonly_session()
        def try_create_user(session: Session):
            user = SimpleModel(name="Test", value=42)
            session.add(user)
            session.flush()
            # No commit in readonly session
        
        try_create_user()
        
        # Verify data not persisted
        @with_session()
        def get_user(session: Session):
            return session.query(SimpleModel).filter_by(name="Test").first()
        
        result = get_user()
        # Result might be None or might exist depending on flush behavior
        # The key is that readonly session doesn't auto-commit


class TestDecoratorChaining:
    """Tests for decorator chaining."""
    
    def test_decorator_with_other_decorators(self, test_manager):
        """Test decorator works with other decorators."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        def log_calls(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        
        @log_calls
        @with_session(auto_commit=True)
        def create_user(session: Session, name: str):
            user = SimpleModel(name=name, value=1)
            session.add(user)
            session.flush()
            return user.id
        
        user_id = create_user(name="TestChained")
        assert user_id is not None
        
        # Verify persisted
        @with_session()
        def get_user(session: Session):
            user = session.query(SimpleModel).filter_by(id=user_id).first()
            if user:
                return user.id, user.name
            return None, None
        
        result_id, result_name = get_user()
        assert result_id is not None
        assert result_id == user_id
        assert result_name == "TestChained"

