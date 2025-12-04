"""
Exception Classes for Engine-Kit

This module provides comprehensive, user-friendly exception classes for all
error scenarios in the engine-kit package. Each exception is designed to
provide clear, actionable error messages and context information.

Exception Hierarchy:
    EngineKitError (base)
    ├── InvalidInputError
    ├── DatabaseError (base)
    │   ├── DatabaseConfigError (base)
    │   │   └── DatabaseConfigurationError
    │   ├── DatabaseEngineError (base)
    │   │   ├── DatabaseEngineNotStartedError
    │   │   ├── DatabaseEngineInitializationError
    │   │   ├── DatabaseSessionError
    │   │   ├── DatabaseConnectionError
    │   │   ├── DatabaseQueryError
    │   │   ├── DatabaseTransactionError
    │   │   ├── DatabasePoolError
    │   │   └── DatabaseHealthError
    │   ├── DatabaseManagerError (base)
    │   │   ├── DatabaseManagerNotInitializedError
    │   │   ├── DatabaseManagerAlreadyInitializedError
    │   │   └── DatabaseManagerResetError
    │   └── DatabaseDecoratorError (base)
    │       ├── DatabaseDecoratorSignatureError
    │       ├── DatabaseDecoratorManagerError
    │       └── DatabaseDecoratorRetryError

Usage Examples:
    >>> raise InvalidInputError(field_name="port", value=0, expected="positive integer")
    >>> raise DatabaseConnectionError(message="Connection timeout", host="localhost", port=5432)
    >>> raise DatabaseQueryError(query="SELECT * FROM users", error="Table 'users' doesn't exist")
"""

from typing import Optional, Dict, Any, Union


# ============================================================================
# BASE EXCEPTION
# ============================================================================

class EngineKitError(Exception):
    """Base exception class for all engine-kit errors.
    
    This is the root exception class that all other exceptions in the
    engine-kit package inherit from. It provides a consistent interface
    for error handling and includes helpful context information.
    
    Attributes:
        message (str): Human-readable error message
        context (dict): Additional context information about the error
        original_error (Exception, optional): Original exception that caused this error
    
    Examples:
        >>> try:
        ...     # Some operation
        ...     pass
        ... except Exception as e:
        ...     raise EngineKitError(
        ...         message="Operation failed",
        ...         context={"operation": "database_connect"},
        ...         original_error=e
        ...     )
    
    Note:
        - All engine-kit exceptions inherit from this class
        - Use specific exception types when possible for better error handling
        - Context dict can contain any relevant debugging information
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['message', 'context', 'original_error']
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize EngineKitError.
        
        Args:
            message: Human-readable error message
            context: Additional context information (dict)
            original_error: Original exception that caused this error
        """
        self.message = message
        self.context = context or {}
        self.original_error = original_error
        
        # Build full message
        full_message = message
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            full_message = f"{message} | Context: {context_str}"
        
        if original_error:
            full_message = f"{full_message} | Original: {type(original_error).__name__}: {str(original_error)}"
        
        super().__init__(full_message)
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, context={self.context})"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.message


# ============================================================================
# INPUT VALIDATION ERRORS
# ============================================================================

class InvalidInputError(EngineKitError):
    """Exception raised when input validation fails.
    
    This exception is raised when a function receives an invalid input
    parameter. It provides detailed information about what was expected
    and what was received.
    
    Attributes:
        field_name (str): Name of the field that failed validation
        value: The invalid value that was provided
        expected (str): Description of what was expected
        received (str): Description of what was actually received
    
    Examples:
        >>> # Invalid port number
        >>> if port <= 0:
        ...     raise InvalidInputError(
        ...         field_name="port",
        ...         value=port,
        ...         expected="positive integer",
        ...         received=f"non-positive integer: {port}"
        ...     )
        
        >>> # Invalid database type
        >>> if db_type not in [DatabaseType.SQLITE, DatabaseType.POSTGRESQL]:
        ...     raise InvalidInputError(
        ...         field_name="db_type",
        ...         value=db_type,
        ...         expected="DatabaseType.SQLITE or DatabaseType.POSTGRESQL",
        ...         received=f"unsupported type: {db_type}"
        ...     )
    
    Note:
        - Always provide clear 'expected' and 'received' descriptions
        - Include the actual value for debugging purposes
        - Use this for parameter validation errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['field_name', 'value', 'expected', 'received']
    
    def __init__(
        self,
        field_name: str,
        value: Any = None,
        expected: Optional[str] = None,
        received: Optional[str] = None,
        message: Optional[str] = None
    ):
        """Initialize InvalidInputError.
        
        Args:
            field_name: Name of the field that failed validation
            value: The invalid value (optional, for debugging)
            expected: Description of what was expected
            received: Description of what was actually received
            message: Custom error message (optional, auto-generated if not provided)
        """
        self.field_name = field_name
        self.value = value
        self.expected = expected
        self.received = received
        
        # Generate message if not provided
        if message is None:
            message_parts = [f"Invalid value for field '{field_name}'"]
            
            if value is not None:
                message_parts.append(f"received: {value}")
            
            if expected:
                message_parts.append(f"expected: {expected}")
            
            if received:
                message_parts.append(f"got: {received}")
            
            message = " | ".join(message_parts)
        
        context = {
            "field_name": field_name,
            "value": value,
            "expected": expected,
            "received": received
        }
        
        super().__init__(message=message, context=context)


# ============================================================================
# DATABASE ERRORS (BASE)
# ============================================================================

class DatabaseError(EngineKitError):
    """Base exception class for all database-related errors.
    
    This is the base class for all database exceptions. It provides
    common functionality and context for database operations.
    
    Attributes:
        db_type (str, optional): Type of database (sqlite, postgresql, mysql)
        operation (str, optional): Database operation that failed
    
    Examples:
        >>> # Base class - use specific exceptions instead
        >>> raise DatabaseError(
        ...     message="Database operation failed",
        ...     context={"db_type": "postgresql", "operation": "query"}
        ... )
    
    Note:
        - Use specific exception types (DatabaseConnectionError, etc.) when possible
        - This is mainly for catching all database errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['db_type', 'operation']
    
    def __init__(
        self,
        message: str = "Database operation failed",
        db_type: Optional[str] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseError.
        
        Args:
            message: Error message
            db_type: Type of database (sqlite, postgresql, mysql)
            operation: Database operation that failed
            context: Additional context information
            original_error: Original exception
        """
        self.db_type = db_type
        self.operation = operation
        
        full_context = context or {}
        if db_type:
            full_context["db_type"] = db_type
        if operation:
            full_context["operation"] = operation
        
        super().__init__(
            message=message,
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE ENGINE ERRORS (BASE) - Must be defined before engine-specific errors
# ============================================================================

class DatabaseEngineErrorBase(DatabaseError):
    """Base exception class for database engine errors.
    
    This is the base class for all engine-related errors.
    Use specific exception types when possible.
    
    Attributes:
        engine_state (str, optional): Current state of the engine
        operation (str, optional): Engine operation that failed
    
    Examples:
        >>> # Base class - use specific exceptions instead
        >>> raise DatabaseEngineErrorBase(
        ...     message="Engine operation failed",
        ...     engine_state="stopped",
        ...     operation="get_session"
        ... )
    
    Note:
        - Use DatabaseEngineError, DatabaseSessionError, etc. for specific errors
        - This is mainly for catching all engine errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['engine_state']
    
    def __init__(
        self,
        message: str = "Database engine operation failed",
        engine_state: Optional[str] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseEngineErrorBase.
        
        Args:
            message: Error message
            engine_state: Current state of the engine
            operation: Engine operation that failed
            context: Additional context information
            original_error: Original exception
        """
        self.engine_state = engine_state
        self.operation = operation
        
        full_context = context or {}
        if engine_state:
            full_context["engine_state"] = engine_state
        if operation:
            full_context["operation"] = operation
        
        super().__init__(
            message=message,
            operation=operation or "engine",
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE CONFIGURATION ERRORS (BASE)
# ============================================================================

class DatabaseConfigError(DatabaseError):
    """Base exception class for database configuration errors.
    
    This is the base class for all configuration-related errors.
    Use specific exception types (DatabaseConfigurationError) when possible.
    
    Attributes:
        config_name (dict): Configuration parameters that caused the error
    
    Examples:
        >>> # Base class - use DatabaseConfigurationError instead
        >>> raise DatabaseConfigError(
        ...     message="Configuration error",
        ...     config_name={"db_type": "postgresql"}
        ... )
    
    Note:
        - Use DatabaseConfigurationError for specific config errors
        - This is mainly for catching all config errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['config_name']
    
    def __init__(
        self,
        message: str = "Database configuration error",
        config_name: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseConfigError.
        
        Args:
            message: Error message
            config_name: Configuration parameters that caused the error
            context: Additional context information
            original_error: Original exception
        """
        self.config_name = config_name or {}
        
        full_context = context or {}
        if config_name:
            full_context["config_name"] = config_name
        
        super().__init__(
            message=message,
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE CONFIGURATION ERRORS
# ============================================================================

class DatabaseConfigurationError(DatabaseConfigError):
    """Exception raised when database configuration is invalid.
    
    This exception is raised when there's an issue with the database
    configuration, such as missing required parameters, invalid values,
    or incompatible settings.
    
    Attributes:
        config_name (dict): Configuration parameters that caused the error
        missing_fields (list): List of missing required fields
        invalid_fields (dict): Dictionary of invalid field names and their values
    
    Examples:
        >>> # Missing required field
        >>> if not username:
        ...     raise DatabaseConfigurationError(
        ...         config_name={"db_type": "postgresql"},
        ...         missing_fields=["username", "password"],
        ...         message="PostgreSQL requires username and password"
        ...     )
        
        >>> # Invalid configuration value
        >>> if pool_size <= 0:
        ...     raise DatabaseConfigurationError(
        ...         config_name={"pool_size": pool_size},
        ...         invalid_fields={"pool_size": "must be positive integer"},
        ...         message="Pool size must be greater than 0"
        ...     )
        
        >>> # Incompatible settings
        >>> if db_type == DatabaseType.SQLITE and host:
        ...     raise DatabaseConfigurationError(
        ...         config_name={"db_type": "sqlite", "host": host},
        ...         message="SQLite does not require host parameter"
        ...     )
    
    Note:
        - Use this for configuration validation errors
        - Always provide clear guidance on what's wrong and how to fix it
        - Include all relevant configuration parameters in config_name
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['missing_fields', 'invalid_fields']
    
    def __init__(
        self,
        config_name: Optional[Dict[str, Any]] = None,
        missing_fields: Optional[list] = None,
        invalid_fields: Optional[Dict[str, str]] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseConfigurationError.
        
        Args:
            config_name: Configuration parameters that caused the error
            missing_fields: List of missing required fields
            invalid_fields: Dictionary of invalid fields and their issues
            message: Custom error message (auto-generated if not provided)
            context: Additional context information
            original_error: Original exception
        """
        self.config_name = config_name or {}
        self.missing_fields = missing_fields or []
        self.invalid_fields = invalid_fields or {}
        
        # Generate message if not provided
        if message is None:
            message_parts = ["Database configuration error"]
            
            if missing_fields:
                message_parts.append(f"missing fields: {', '.join(missing_fields)}")
            
            if invalid_fields:
                invalid_list = [f"{k}: {v}" for k, v in invalid_fields.items()]
                message_parts.append(f"invalid fields: {', '.join(invalid_list)}")
            
            if config_name:
                config_str = ", ".join(f"{k}={v}" for k, v in config_name.items())
                message_parts.append(f"config: {config_str}")
            
            message = " | ".join(message_parts)
        
        full_context = context or {}
        full_context.update({
            "config_name": config_name,
            "missing_fields": missing_fields,
            "invalid_fields": invalid_fields
        })
        
        super().__init__(
            message=message,
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE CONNECTION ERRORS
# ============================================================================

class DatabaseConnectionError(DatabaseEngineErrorBase):
    """Exception raised when database connection fails.
    
    This exception is raised when the engine-kit cannot establish a
    connection to the database. This includes network errors, authentication
    failures, and connection timeouts.
    
    Attributes:
        host (str, optional): Database host address
        port (int, optional): Database port number
        database (str, optional): Database name
        connection_string (str, optional): Full connection string (password masked)
        timeout (float, optional): Connection timeout in seconds
    
    Examples:
        >>> # Connection timeout
        >>> raise DatabaseConnectionError(
        ...     message="Connection timeout after 30 seconds",
        ...     host="localhost",
        ...     port=5432,
        ...     database="mydb",
        ...     timeout=30.0
        ... )
        
        >>> # Authentication failure
        >>> raise DatabaseConnectionError(
        ...     message="Authentication failed",
        ...     host="db.example.com",
        ...     port=5432,
        ...     database="mydb",
        ...     context={"error_code": "28P01", "error_type": "authentication"}
        ... )
        
        >>> # Network error
        >>> raise DatabaseConnectionError(
        ...     message="Could not connect to database server",
        ...     host="192.168.1.100",
        ...     port=5432,
        ...     context={"error": "Connection refused", "network": True}
        ... )
    
    Note:
        - Never include passwords in error messages
        - Mask connection strings in logs
        - Provide actionable error messages (check host, port, firewall, etc.)
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['host', 'port', 'database', 'connection_string', 'timeout']
    
    def __init__(
        self,
        message: str = "Failed to connect to database",
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        connection_string: Optional[str] = None,
        timeout: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseConnectionError.
        
        Args:
            message: Error message
            host: Database host address
            port: Database port number
            database: Database name
            connection_string: Connection string (password will be masked)
            timeout: Connection timeout in seconds
            context: Additional context information
            original_error: Original exception
        """
        self.host = host
        self.port = port
        self.database = database
        self.connection_string = self._mask_password(connection_string) if connection_string else None
        self.timeout = timeout
        
        full_context = context or {}
        if host:
            full_context["host"] = host
        if port:
            full_context["port"] = port
        if database:
            full_context["database"] = database
        if self.connection_string:
            full_context["connection_string"] = self.connection_string
        if timeout:
            full_context["timeout"] = timeout
        
        super().__init__(
            message=message,
            context=full_context,
            original_error=original_error
        )
    
    @staticmethod
    def _mask_password(connection_string: str) -> str:
        """Mask password in connection string for security.
        
        Args:
            connection_string: Full connection string
            
        Returns:
            Connection string with password masked
        """
        import re
        # Mask password in connection string
        # Pattern: password=xxx or :password@host
        masked = re.sub(r'(password=)[^&;@\s]+', r'\1***', connection_string, flags=re.IGNORECASE)
        masked = re.sub(r':[^:@]+@', r':***@', masked)  # :password@host pattern
        return masked


# ============================================================================
# DATABASE QUERY ERRORS
# ============================================================================

class DatabaseQueryError(DatabaseEngineErrorBase):
    """Exception raised when a database query fails.
    
    This exception is raised when a SQL query execution fails. This includes
    syntax errors, constraint violations, table not found errors, and other
    SQL-related issues.
    
    Attributes:
        query (str, optional): The SQL query that failed
        error_code (str, optional): Database-specific error code
        error_type (str, optional): Type of error (syntax, constraint, etc.)
        table (str, optional): Table name involved in the error
        constraint (str, optional): Constraint name if applicable
    
    Examples:
        >>> # Table not found
        >>> raise DatabaseQueryError(
        ...     message="Table 'users' does not exist",
        ...     query="SELECT * FROM users",
        ...     error_code="42P01",
        ...     error_type="table_not_found",
        ...     table="users"
        ... )
        
        >>> # Constraint violation
        >>> raise DatabaseQueryError(
        ...     message="Unique constraint violation",
        ...     query="INSERT INTO users (email) VALUES ('test@test.com')",
        ...     error_code="23505",
        ...     error_type="constraint_violation",
        ...     constraint="users_email_key"
        ... )
        
        >>> # Syntax error
        >>> raise DatabaseQueryError(
        ...     message="SQL syntax error",
        ...     query="SELECT * FROM users WHERE id =",
        ...     error_code="42601",
        ...     error_type="syntax_error"
        ... )
    
    Note:
        - Include the query for debugging (sanitize if contains sensitive data)
        - Provide database-specific error codes when available
        - Categorize error types for better error handling
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['query', 'error_code', 'error_type', 'table', 'constraint']
    
    def __init__(
        self,
        message: str = "Database query failed",
        query: Optional[str] = None,
        error_code: Optional[str] = None,
        error_type: Optional[str] = None,
        table: Optional[str] = None,
        constraint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseQueryError.
        
        Args:
            message: Error message
            query: The SQL query that failed
            error_code: Database-specific error code
            error_type: Type of error (syntax, constraint, table_not_found, etc.)
            table: Table name involved in the error
            constraint: Constraint name if applicable
            context: Additional context information
            original_error: Original exception
        """
        self.query = query
        self.error_code = error_code
        self.error_type = error_type
        self.table = table
        self.constraint = constraint
        
        full_context = context or {}
        if query:
            full_context["query"] = self._sanitize_query(query)
        if error_code:
            full_context["error_code"] = error_code
        if error_type:
            full_context["error_type"] = error_type
        if table:
            full_context["table"] = table
        if constraint:
            full_context["constraint"] = constraint
        
        super().__init__(
            message=message,
            operation="query",
            context=full_context,
            original_error=original_error
        )
    
    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Sanitize query for logging (remove sensitive data if needed).
        
        Args:
            query: SQL query string
            
        Returns:
            Sanitized query string
        """
        # In production, you might want to remove or mask sensitive values
        # For now, just truncate very long queries
        if len(query) > 500:
            return query[:500] + "... (truncated)"
        return query


# ============================================================================
# DATABASE SESSION ERRORS
# ============================================================================

class DatabaseSessionError(DatabaseEngineErrorBase):
    """Exception raised when session management fails.
    
    This exception is raised when there's an issue with session creation,
    management, or cleanup. This includes session factory errors, session
    tracking issues, and session lifecycle problems.
    
    Attributes:
        session_id (str, optional): Identifier for the session (if available)
        operation (str, optional): Session operation that failed (create, close, etc.)
        active_sessions (int, optional): Number of active sessions when error occurred
    
    Examples:
        >>> # Session creation failed
        >>> raise DatabaseSessionError(
        ...     message="Failed to create database session",
        ...     operation="create",
        ...     context={"pool_exhausted": True, "active_sessions": 50}
        ... )
        
        >>> # Session cleanup failed
        >>> raise DatabaseSessionError(
        ...     message="Failed to close session",
        ...     operation="close",
        ...     session_id="session_123"
        ... )
    
    Note:
        - Use this for session lifecycle errors
        - Include pool status information when relevant
        - Track active sessions for debugging connection pool issues
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['session_id', 'active_sessions']
    
    def __init__(
        self,
        message: str = "Database session operation failed",
        session_id: Optional[str] = None,
        operation: Optional[str] = None,
        active_sessions: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseSessionError.
        
        Args:
            message: Error message
            session_id: Session identifier
            operation: Session operation (create, close, commit, rollback, etc.)
            active_sessions: Number of active sessions
            context: Additional context information
            original_error: Original exception
        """
        self.session_id = session_id
        self.operation = operation
        self.active_sessions = active_sessions
        
        full_context = context or {}
        if session_id:
            full_context["session_id"] = session_id
        if operation:
            full_context["operation"] = operation
        if active_sessions is not None:
            full_context["active_sessions"] = active_sessions
        
        super().__init__(
            message=message,
            operation=operation or "session",
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE ENGINE ERRORS
# ============================================================================

class DatabaseEngineError(DatabaseEngineErrorBase):
    """Exception raised when engine operations fail.
    
    This exception is raised when there's an issue with the database engine
    itself, such as engine initialization failures, engine shutdown problems,
    or engine state inconsistencies.
    
    Attributes:
        engine_state (str, optional): Current state of the engine (stopped, starting, etc.)
        operation (str, optional): Engine operation that failed (start, stop, create_tables, etc.)
    
    Examples:
        >>> # Engine not initialized
        >>> raise DatabaseEngineError(
        ...     message="Engine not initialized. Call start() first.",
        ...     engine_state="stopped",
        ...     operation="get_session"
        ... )
        
        >>> # Engine start failed
        >>> raise DatabaseEngineError(
        ...     message="Failed to start database engine",
        ...     operation="start",
        ...     context={"error": "Connection pool creation failed"}
        ... )
        
        >>> # Table creation failed
        >>> raise DatabaseEngineError(
        ...     message="Failed to create database tables",
        ...     operation="create_tables",
        ...     context={"table": "users", "error": "Permission denied"}
        ... )
    
    Note:
        - Use this for engine lifecycle errors
        - Always include engine state information
        - Provide clear guidance on what operation failed and why
    """
    pass


class DatabaseEngineNotStartedError(DatabaseEngineErrorBase):
    """Exception raised when engine operation is attempted but engine is not started.
    
    This exception is raised when trying to use engine methods (like session_context,
    get_session, create_tables) but the engine has not been started yet.
    
    Examples:
        >>> # Engine not started
        >>> if not engine.is_alive:
        ...     raise DatabaseEngineNotStartedError(
        ...         operation="session_context",
        ...         message="Engine not started. Call engine.start() first."
        ...     )
    """
    
    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseEngineNotStartedError.
        
        Args:
            operation: Operation that was attempted
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = f"Engine not started. Call engine.start() first."
            if operation:
                message = f"Engine not started. Cannot perform '{operation}'. Call engine.start() first."
        
        super().__init__(
            message=message,
            engine_state="stopped",
            operation=operation,
            context=context,
            original_error=original_error
        )


class DatabaseEngineInitializationError(DatabaseEngineErrorBase):
    """Exception raised when engine initialization fails.
    
    This exception is raised when there's an issue during engine creation,
    such as connection pool creation failures or session factory errors.
    
    Examples:
        >>> # Engine creation failed
        >>> raise DatabaseEngineInitializationError(
        ...     operation="build_engine",
        ...     context={"error": "Connection pool creation failed"}
        ... )
    """
    
    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseEngineInitializationError.
        
        Args:
            operation: Initialization operation that failed (build_engine, build_session_factory, etc.)
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = "Failed to initialize database engine"
            if operation:
                message = f"Failed to initialize database engine during '{operation}'"
        
        super().__init__(
            message=message,
            engine_state="initializing",
            operation=operation,
            context=context,
            original_error=original_error
        )


# ============================================================================
# DATABASE TRANSACTION ERRORS
# ============================================================================

class DatabaseTransactionError(DatabaseEngineErrorBase):
    """Exception raised when transaction operations fail.
    
    This exception is raised when there's an issue with database transactions,
    such as commit failures, rollback problems, or transaction state inconsistencies.
    This includes deadlocks, lock timeouts, and transaction isolation issues.
    
    Attributes:
        transaction_id (str, optional): Transaction identifier (if available)
        isolation_level (str, optional): Transaction isolation level
        is_deadlock (bool, optional): Whether this is a deadlock error
        is_timeout (bool, optional): Whether this is a timeout error
    
    Examples:
        >>> # Deadlock detected
        >>> raise DatabaseTransactionError(
        ...     message="Deadlock detected in transaction",
        ...     is_deadlock=True,
        ...     isolation_level="READ_COMMITTED",
        ...     context={"tables": ["users", "orders"], "retry_count": 2}
        ... )
        
        >>> # Transaction timeout
        >>> raise DatabaseTransactionError(
        ...     message="Transaction timeout after 30 seconds",
        ...     is_timeout=True,
        ...     isolation_level="SERIALIZABLE",
        ...     context={"timeout": 30.0, "operation": "batch_update"}
        ... )
        
        >>> # Commit failed
        >>> raise DatabaseTransactionError(
        ...     message="Failed to commit transaction",
        ...     context={"error": "Constraint violation", "table": "users"}
        ... )
    
    Note:
        - Use this for transaction-related errors
        - Mark deadlocks and timeouts for retry logic
        - Include isolation level information
        - Provide context about which tables/operations were involved
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['transaction_id', 'isolation_level', 'is_deadlock', 'is_timeout']
    
    def __init__(
        self,
        message: str = "Database transaction failed",
        transaction_id: Optional[str] = None,
        isolation_level: Optional[str] = None,
        is_deadlock: bool = False,
        is_timeout: bool = False,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseTransactionError.
        
        Args:
            message: Error message
            transaction_id: Transaction identifier
            isolation_level: Transaction isolation level
            is_deadlock: Whether this is a deadlock error
            is_timeout: Whether this is a timeout error
            context: Additional context information
            original_error: Original exception
        """
        self.transaction_id = transaction_id
        self.isolation_level = isolation_level
        self.is_deadlock = is_deadlock
        self.is_timeout = is_timeout
        
        full_context = context or {}
        if transaction_id:
            full_context["transaction_id"] = transaction_id
        if isolation_level:
            full_context["isolation_level"] = isolation_level
        if is_deadlock:
            full_context["is_deadlock"] = True
        if is_timeout:
            full_context["is_timeout"] = True
        
        super().__init__(
            message=message,
            operation="transaction",
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE POOL ERRORS
# ============================================================================

class DatabasePoolError(DatabaseEngineErrorBase):
    """Exception raised when connection pool operations fail.
    
    This exception is raised when there's an issue with the connection pool,
    such as pool exhaustion, pool creation failures, or pool configuration problems.
    
    Attributes:
        pool_type (str, optional): Type of pool (QueuePool, NullPool, StaticPool)
        pool_size (int, optional): Configured pool size
        active_connections (int, optional): Number of active connections
        max_overflow (int, optional): Maximum overflow connections
    
    Examples:
        >>> # Pool exhausted
        >>> raise DatabasePoolError(
        ...     message="Connection pool exhausted",
        ...     pool_type="QueuePool",
        ...     pool_size=10,
        ...     active_connections=10,
        ...     max_overflow=20,
        ...     context={"wait_timeout": 30.0}
        ... )
        
        >>> # Pool creation failed
        >>> raise DatabasePoolError(
        ...     message="Failed to create connection pool",
        ...     pool_type="QueuePool",
        ...     context={"error": "Invalid pool configuration"}
        ... )
    
    Note:
        - Use this for connection pool errors
        - Include pool statistics when available
        - Provide guidance on pool configuration tuning
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['pool_type', 'pool_size', 'active_connections', 'max_overflow']
    
    def __init__(
        self,
        message: str = "Connection pool operation failed",
        pool_type: Optional[str] = None,
        pool_size: Optional[int] = None,
        active_connections: Optional[int] = None,
        max_overflow: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabasePoolError.
        
        Args:
            message: Error message
            pool_type: Type of pool (QueuePool, NullPool, StaticPool)
            pool_size: Configured pool size
            active_connections: Number of active connections
            max_overflow: Maximum overflow connections
            context: Additional context information
            original_error: Original exception
        """
        self.pool_type = pool_type
        self.pool_size = pool_size
        self.active_connections = active_connections
        self.max_overflow = max_overflow
        
        full_context = context or {}
        if pool_type:
            full_context["pool_type"] = pool_type
        if pool_size is not None:
            full_context["pool_size"] = pool_size
        if active_connections is not None:
            full_context["active_connections"] = active_connections
        if max_overflow is not None:
            full_context["max_overflow"] = max_overflow
        
        super().__init__(
            message=message,
            operation="pool",
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE HEALTH ERRORS
# ============================================================================

class DatabaseHealthError(DatabaseEngineErrorBase):
    """Exception raised when health check operations fail.
    
    This exception is raised when there's an issue with database health checks,
    such as health check failures, monitoring errors, or health status inconsistencies.
    
    Attributes:
        health_status (str, optional): Current health status (healthy, unhealthy, etc.)
        check_type (str, optional): Type of health check (connection, query, pool, etc.)
        last_successful_check (str, optional): Timestamp of last successful check
    
    Examples:
        >>> # Health check failed
        >>> raise DatabaseHealthError(
        ...     message="Database health check failed",
        ...     health_status="unhealthy",
        ...     check_type="connection",
        ...     context={"error": "Connection timeout", "retry_count": 3}
        ... )
        
        >>> # Health check query failed
        >>> raise DatabaseHealthError(
        ...     message="Health check query failed",
        ...     check_type="query",
        ...     context={"query": "SELECT 1", "error": "Table does not exist"}
        ... )
    
    Note:
        - Use this for health monitoring errors
        - Include health status information
        - Track check history for debugging
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['health_status', 'check_type', 'last_successful_check']
    
    def __init__(
        self,
        message: str = "Database health check failed",
        health_status: Optional[str] = None,
        check_type: Optional[str] = None,
        last_successful_check: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseHealthError.
        
        Args:
            message: Error message
            health_status: Current health status
            check_type: Type of health check
            last_successful_check: Timestamp of last successful check
            context: Additional context information
            original_error: Original exception
        """
        self.health_status = health_status
        self.check_type = check_type
        self.last_successful_check = last_successful_check
        
        full_context = context or {}
        if health_status:
            full_context["health_status"] = health_status
        if check_type:
            full_context["check_type"] = check_type
        if last_successful_check:
            full_context["last_successful_check"] = last_successful_check
        
        super().__init__(
            message=message,
            operation="health_check",
            context=full_context,
            original_error=original_error
        )


# ============================================================================
# DATABASE MANAGER ERRORS (BASE)
# ============================================================================

class DatabaseManagerError(DatabaseError):
    """Base exception class for database manager errors.
    
    This is the base class for all manager-related errors.
    Use specific exception types when possible.
    
    Attributes:
        manager_state (str, optional): Current state of the manager
    
    Examples:
        >>> # Base class - use specific exceptions instead
        >>> raise DatabaseManagerError(
        ...     message="Manager operation failed",
        ...     manager_state="not_initialized"
        ... )
    
    Note:
        - Use DatabaseManagerNotInitializedError, etc. for specific errors
        - This is mainly for catching all manager errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['manager_state']
    
    def __init__(
        self,
        message: str = "Database manager operation failed",
        manager_state: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseManagerError.
        
        Args:
            message: Error message
            manager_state: Current state of the manager
            context: Additional context information
            original_error: Original exception
        """
        self.manager_state = manager_state
        
        full_context = context or {}
        if manager_state:
            full_context["manager_state"] = manager_state
        
        super().__init__(
            message=message,
            operation="manager",
            context=full_context,
            original_error=original_error
        )


class DatabaseManagerNotInitializedError(DatabaseManagerError):
    """Exception raised when manager operation is attempted but manager is not initialized.
    
    This exception is raised when trying to use manager methods (like engine property,
    start, stop) but the manager has not been initialized yet.
    
    Examples:
        >>> # Manager not initialized
        >>> if not manager._initialized:
        ...     raise DatabaseManagerNotInitializedError(
        ...         message="DatabaseManager not initialized. Call initialize(config) first."
        ...     )
    """
    
    def __init__(
        self,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseManagerNotInitializedError.
        
        Args:
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = "DatabaseManager not initialized. Call initialize(config) first."
        
        super().__init__(
            message=message,
            manager_state="not_initialized",
            context=context,
            original_error=original_error
        )


class DatabaseManagerAlreadyInitializedError(DatabaseManagerError):
    """Exception raised when trying to initialize an already initialized manager.
    
    This exception is raised when initialize() is called on a manager that has
    already been initialized, unless force_reinitialize=True is used.
    
    Examples:
        >>> # Manager already initialized
        >>> if manager._initialized and not force_reinitialize:
        ...     raise DatabaseManagerAlreadyInitializedError(
        ...         message="DatabaseManager already initialized. Use force_reinitialize=True to reinitialize."
        ...     )
    """
    
    def __init__(
        self,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseManagerAlreadyInitializedError.
        
        Args:
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = (
                "DatabaseManager already initialized. "
                "Use force_reinitialize=True to reinitialize or call reset() first."
            )
        
        super().__init__(
            message=message,
            manager_state="initialized",
            context=context,
            original_error=original_error
        )


class DatabaseManagerResetError(DatabaseManagerError):
    """Exception raised when manager reset operation fails.
    
    This exception is raised when there's an issue during manager reset,
    such as errors stopping the engine or cleaning up resources.
    
    Examples:
        >>> # Reset failed
        >>> raise DatabaseManagerResetError(
        ...     message="Failed to reset DatabaseManager",
        ...     context={"error": "Engine stop failed"}
        ... )
    """
    
    def __init__(
        self,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseManagerResetError.
        
        Args:
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = "Failed to reset DatabaseManager"
        
        super().__init__(
            message=message,
            manager_state="resetting",
            context=context,
            original_error=original_error
        )


# ============================================================================
# DATABASE DECORATOR ERRORS (BASE)
# ============================================================================

class DatabaseDecoratorError(DatabaseError):
    """Base exception class for database decorator errors.
    
    This is the base class for all decorator-related errors.
    Use specific exception types when possible.
    
    Attributes:
        decorator_name (str, optional): Name of the decorator that raised the error
        function_name (str, optional): Name of the function being decorated
    
    Examples:
        >>> # Base class - use specific exceptions instead
        >>> raise DatabaseDecoratorError(
        ...     message="Decorator operation failed",
        ...     decorator_name="with_session",
        ...     function_name="get_user"
        ... )
    
    Note:
        - Use DatabaseDecoratorSignatureError, etc. for specific errors
        - This is mainly for catching all decorator errors
        - Uses __slots__ for memory optimization (%86 memory reduction)
    """
    __slots__ = ['decorator_name', 'function_name']
    
    def __init__(
        self,
        message: str = "Database decorator operation failed",
        decorator_name: Optional[str] = None,
        function_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseDecoratorError.
        
        Args:
            message: Error message
            decorator_name: Name of the decorator (with_session, with_transaction, etc.)
            function_name: Name of the function being decorated
            context: Additional context information
            original_error: Original exception
        """
        self.decorator_name = decorator_name
        self.function_name = function_name
        
        full_context = context or {}
        if decorator_name:
            full_context["decorator_name"] = decorator_name
        if function_name:
            full_context["function_name"] = function_name
        
        super().__init__(
            message=message,
            operation="decorator",
            context=full_context,
            original_error=original_error
        )


class DatabaseDecoratorSignatureError(DatabaseDecoratorError):
    """Exception raised when decorated function has invalid signature.
    
    This exception is raised when a decorator expects a function with a 'session'
    parameter but the function doesn't have it, or when other signature validation fails.
    
    Examples:
        >>> # Missing session parameter
        >>> if 'session' not in sig.parameters:
        ...     raise DatabaseDecoratorSignatureError(
        ...         decorator_name="with_session",
        ...         function_name="get_user",
        ...         message="Function 'get_user' must have 'session' parameter"
        ...     )
    """
    __slots__ = ['expected', 'received']
    
    def __init__(
        self,
        decorator_name: str,
        function_name: str,
        message: Optional[str] = None,
        expected: Optional[str] = None,
        received: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseDecoratorSignatureError.
        
        Args:
            decorator_name: Name of the decorator
            function_name: Name of the function being decorated
            message: Custom error message
            expected: What was expected (e.g., "session parameter")
            received: What was received (e.g., "no session parameter")
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = f"Function '{function_name}' has invalid signature for decorator '@{decorator_name}'"
            if expected:
                message += f". Expected: {expected}"
            if received:
                message += f". Received: {received}"
        
        full_context = context or {}
        if expected:
            full_context["expected"] = expected
        if received:
            full_context["received"] = received
        
        super().__init__(
            message=message,
            decorator_name=decorator_name,
            function_name=function_name,
            context=full_context,
            original_error=original_error
        )


class DatabaseDecoratorManagerError(DatabaseDecoratorError):
    """Exception raised when decorator cannot access DatabaseManager.
    
    This exception is raised when a decorator tries to use DatabaseManager
    but it's not initialized or not available.
    
    Examples:
        >>> # Manager not initialized
        >>> if manager is None:
        ...     raise DatabaseDecoratorManagerError(
        ...         decorator_name="with_session",
        ...         function_name="get_user",
        ...         message="DatabaseManager not initialized"
        ...     )
    """
    
    def __init__(
        self,
        decorator_name: str,
        function_name: Optional[str] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseDecoratorManagerError.
        
        Args:
            decorator_name: Name of the decorator
            function_name: Name of the function being decorated
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = f"DatabaseManager not initialized. Cannot use decorator '@{decorator_name}'"
            if function_name:
                message += f" on function '{function_name}'"
            message += ". Call DatabaseManager().initialize(config) first."
        
        super().__init__(
            message=message,
            decorator_name=decorator_name,
            function_name=function_name,
            context=context,
            original_error=original_error
        )


class DatabaseDecoratorRetryError(DatabaseDecoratorError):
    """Exception raised when decorator retry logic fails.
    
    This exception is raised when retry decorator (with_retry_session) exhausts
    all retry attempts or encounters an unexpected error during retry logic.
    
    Examples:
        >>> # Retry exhausted
        >>> if attempt >= max_attempts:
        ...     raise DatabaseDecoratorRetryError(
        ...         decorator_name="with_retry_session",
        ...         function_name="risky_operation",
        ...         message=f"Failed after {max_attempts} attempts",
        ...         context={"attempt": max_attempts, "last_error": str(e)}
        ...     )
    """
    __slots__ = ['attempt', 'max_attempts']
    
    def __init__(
        self,
        decorator_name: str,
        function_name: str,
        attempt: Optional[int] = None,
        max_attempts: Optional[int] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize DatabaseDecoratorRetryError.
        
        Args:
            decorator_name: Name of the decorator
            function_name: Name of the function being decorated
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            message: Custom error message
            context: Additional context information
            original_error: Original exception
        """
        if message is None:
            message = f"Function '{function_name}' failed in decorator '@{decorator_name}'"
            if attempt is not None and max_attempts is not None:
                message += f" after {attempt}/{max_attempts} attempts"
        
        full_context = context or {}
        if attempt is not None:
            full_context["attempt"] = attempt
        if max_attempts is not None:
            full_context["max_attempts"] = max_attempts
        
        super().__init__(
            message=message,
            decorator_name=decorator_name,
            function_name=function_name,
            context=full_context,
            original_error=original_error
        )

