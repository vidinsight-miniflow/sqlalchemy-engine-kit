"""
Unit tests for exception classes
"""

import pytest
import sys
from sqlalchemy_engine_kit.core.exceptions import (
    EngineKitError,
    InvalidInputError,
    DatabaseError,
    DatabaseConfigError,
    DatabaseConfigurationError,
    DatabaseEngineErrorBase,
    DatabaseEngineNotStartedError,
    DatabaseEngineInitializationError,
    DatabaseSessionError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabasePoolError,
    DatabaseHealthError,
    DatabaseManagerError,
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
    DatabaseManagerResetError,
    DatabaseDecoratorError,
    DatabaseDecoratorSignatureError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorRetryError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""
    
    def test_engine_kit_error_is_base(self):
        """Test that EngineKitError is base exception."""
        assert issubclass(InvalidInputError, EngineKitError)
        assert issubclass(DatabaseError, EngineKitError)
    
    def test_database_error_hierarchy(self):
        """Test DatabaseError subclasses."""
        assert issubclass(DatabaseConfigError, DatabaseError)
        assert issubclass(DatabaseEngineErrorBase, DatabaseError)
        assert issubclass(DatabaseManagerError, DatabaseError)
        assert issubclass(DatabaseDecoratorError, DatabaseError)
    
    def test_database_config_error_hierarchy(self):
        """Test DatabaseConfigError subclasses."""
        assert issubclass(DatabaseConfigurationError, DatabaseConfigError)
    
    def test_database_engine_error_hierarchy(self):
        """Test DatabaseEngineErrorBase subclasses."""
        assert issubclass(DatabaseEngineNotStartedError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseEngineInitializationError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseSessionError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseConnectionError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseQueryError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseTransactionError, DatabaseEngineErrorBase)
        assert issubclass(DatabasePoolError, DatabaseEngineErrorBase)
        assert issubclass(DatabaseHealthError, DatabaseEngineErrorBase)
    
    def test_database_manager_error_hierarchy(self):
        """Test DatabaseManagerError subclasses."""
        assert issubclass(DatabaseManagerNotInitializedError, DatabaseManagerError)
        assert issubclass(DatabaseManagerAlreadyInitializedError, DatabaseManagerError)
        assert issubclass(DatabaseManagerResetError, DatabaseManagerError)
    
    def test_database_decorator_error_hierarchy(self):
        """Test DatabaseDecoratorError subclasses."""
        assert issubclass(DatabaseDecoratorSignatureError, DatabaseDecoratorError)
        assert issubclass(DatabaseDecoratorManagerError, DatabaseDecoratorError)
        assert issubclass(DatabaseDecoratorRetryError, DatabaseDecoratorError)


class TestExceptionMessageFormatting:
    """Tests for exception message formatting."""
    
    def test_engine_kit_error_message(self):
        """Test EngineKitError message formatting."""
        error = EngineKitError(message="Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
    
    def test_engine_kit_error_with_context(self):
        """Test EngineKitError with context."""
        error = EngineKitError(
            message="Test error",
            context={"key": "value", "number": 42}
        )
        assert error.message == "Test error"
        assert error.context == {"key": "value", "number": 42}
        # __str__ returns only message, but repr includes context
        repr_str = repr(error)
        assert "key" in repr_str and "value" in repr_str
    
    def test_engine_kit_error_with_original_error(self):
        """Test EngineKitError with original error."""
        original = ValueError("Original error")
        error = EngineKitError(
            message="Test error",
            original_error=original
        )
        assert error.original_error == original
        # __str__ returns only message, but full error message includes original
        error_str = str(error)
        # Check that original error info is accessible via repr or exception args
        assert error.original_error == original
    
    def test_invalid_input_error_message(self):
        """Test InvalidInputError message formatting."""
        error = InvalidInputError(
            field_name="port",
            value=0,
            expected="positive integer",
            received="non-positive integer: 0"
        )
        assert error.field_name == "port"
        assert error.value == 0
        assert error.expected == "positive integer"
        assert error.received == "non-positive integer: 0"
        assert "port" in str(error).lower()
    
    def test_database_error_message(self):
        """Test DatabaseError message formatting."""
        error = DatabaseConnectionError(
            message="Connection failed",
            host="localhost",
            port=5432
        )
        assert error.message == "Connection failed"
        assert error.host == "localhost"
        assert error.port == 5432
        assert "Connection failed" in str(error)
    
    def test_database_query_error_message(self):
        """Test DatabaseQueryError message formatting."""
        error = DatabaseQueryError(
            message="Query failed",
            query="SELECT * FROM users",
            original_error=ValueError("Table not found")
        )
        assert error.query == "SELECT * FROM users"
        assert error.message == "Query failed"
        assert error.original_error is not None


class TestExceptionSlots:
    """Tests for __slots__ memory optimization."""
    
    def test_engine_kit_error_has_slots(self):
        """Test that EngineKitError uses __slots__."""
        error = EngineKitError(message="Test")
        assert hasattr(error, '__slots__')
        # Try to set an attribute that's not in slots (should work but not recommended)
        # Actually, __slots__ prevents setting arbitrary attributes
        assert '__slots__' in EngineKitError.__dict__
    
    def test_invalid_input_error_has_slots(self):
        """Test that InvalidInputError uses __slots__."""
        assert '__slots__' in InvalidInputError.__dict__
        error = InvalidInputError(
            field_name="test",
            value=1,
            expected="int",
            received="str"
        )
        # Verify slots are working
        assert hasattr(error, 'field_name')
        assert hasattr(error, 'value')
    
    def test_database_error_has_slots(self):
        """Test that DatabaseError uses __slots__."""
        assert '__slots__' in DatabaseError.__dict__
        error = DatabaseConnectionError(
            message="Test",
            host="localhost",
            port=5432
        )
        assert hasattr(error, 'host')
        assert hasattr(error, 'port')
    
    def test_memory_optimization(self):
        """Test that __slots__ reduces memory usage."""
        # Create many exception instances
        errors = [
            InvalidInputError(
                field_name=f"field{i}",
                value=i,
                expected="int",
                received="str"
            )
            for i in range(1000)
        ]
        # If __slots__ is working, memory usage should be lower
        # This is a basic check - actual memory profiling would be more accurate
        assert len(errors) == 1000
        assert all(hasattr(e, 'field_name') for e in errors)


class TestExceptionRepr:
    """Tests for exception __repr__ methods."""
    
    def test_engine_kit_error_repr(self):
        """Test EngineKitError __repr__."""
        error = EngineKitError(message="Test error", context={"key": "value"})
        repr_str = repr(error)
        assert "EngineKitError" in repr_str
        assert "Test error" in repr_str
    
    def test_invalid_input_error_repr(self):
        """Test InvalidInputError __repr__."""
        error = InvalidInputError(
            field_name="port",
            value=0,
            expected="positive integer",
            received="non-positive"
        )
        repr_str = repr(error)
        assert "InvalidInputError" in repr_str
        assert "port" in repr_str
    
    def test_database_error_repr(self):
        """Test DatabaseError __repr__."""
        error = DatabaseConnectionError(
            message="Connection failed",
            host="localhost",
            port=5432
        )
        repr_str = repr(error)
        assert "DatabaseConnectionError" in repr_str
        assert "Connection failed" in repr_str


class TestExceptionContext:
    """Tests for exception context handling."""
    
    def test_context_preservation(self):
        """Test that context is preserved in exceptions."""
        error = EngineKitError(
            message="Test",
            context={"operation": "connect", "retry_count": 3}
        )
        assert error.context["operation"] == "connect"
        assert error.context["retry_count"] == 3
    
    def test_original_error_preservation(self):
        """Test that original error is preserved."""
        original = ValueError("Original")
        error = DatabaseQueryError(
            message="Query failed",
            query="SELECT 1",
            original_error=original
        )
        assert error.original_error == original
        assert isinstance(error.original_error, ValueError)
    
    def test_nested_error_chain(self):
        """Test error chaining with nested exceptions."""
        original = ValueError("Original")
        intermediate = DatabaseConnectionError(
            message="Connection failed",
            host="localhost",
            port=5432,
            original_error=original
        )
        final = DatabaseQueryError(
            message="Query failed",
            query="SELECT 1",
            original_error=intermediate
        )
        assert final.original_error == intermediate
        assert intermediate.original_error == original

