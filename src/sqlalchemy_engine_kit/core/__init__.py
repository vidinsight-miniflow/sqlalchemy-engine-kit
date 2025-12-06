"""
Core module for engine-kit
"""

from .exceptions import (
    EngineKitError,
    InvalidInputError,
    # Database Config Errors
    DatabaseConfigError,
    DatabaseConfigurationError,
    # Database Engine Errors
    DatabaseEngineErrorBase,
    DatabaseEngineError,
    DatabaseEngineNotStartedError,
    DatabaseEngineInitializationError,
    DatabaseSessionError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabasePoolError,
    DatabaseHealthError,
    # Database Manager Errors
    DatabaseManagerError,
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
    DatabaseManagerResetError,
    # Database Decorator Errors
    DatabaseDecoratorError,
    DatabaseDecoratorSignatureError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorRetryError,
    # Base
    DatabaseError,
)
from .logging import LoggerAdapter

__all__ = [
    'EngineKitError',
    'InvalidInputError',
    'DatabaseConfigError',
    'DatabaseConfigurationError',
    'DatabaseEngineErrorBase',
    'DatabaseEngineError',
    'DatabaseEngineNotStartedError',
    'DatabaseEngineInitializationError',
    'DatabaseSessionError',
    'DatabaseConnectionError',
    'DatabaseQueryError',
    'DatabaseTransactionError',
    'DatabasePoolError',
    'DatabaseHealthError',
    'DatabaseManagerError',
    'DatabaseManagerNotInitializedError',
    'DatabaseManagerAlreadyInitializedError',
    'DatabaseManagerResetError',
    'DatabaseDecoratorError',
    'DatabaseDecoratorSignatureError',
    'DatabaseDecoratorManagerError',
    'DatabaseDecoratorRetryError',
    'DatabaseError',
    'LoggerAdapter',
]

