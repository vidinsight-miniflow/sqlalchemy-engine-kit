"""
Logger integration for engine-kit.

This module provides integration with the host system's logging infrastructure.
It supports:
- Using host system's logger (default)
- Custom logger injection
- Environment variable configuration
- Lazy logger initialization for performance
"""
import sys
import logging
from typing import Optional

class LoggerAdapter:
    """Adapter for integrating with host system's logger.
    
    This class provides a unified logging interface that automatically
    integrates with the host system's logging configuration. It follows
    the principle of "least surprise" - if the host system has configured
    logging, it uses that. Otherwise, it provides sensible defaults.
    
    Priority order:
    1. Custom injected logger (via set_logger())
    2. Host system's logger (from ENGINE_KIT_LOGGER_NAME env var)
    3. Root logger (if configured by host system)
    4. Default engine_kit logger (with basic console handler)
    
    Examples:
        >>> # Automatic integration (recommended)
        >>> logger = LoggerAdapter.get_logger(__name__)
        >>> logger.info("Database engine started")
        
        >>> # Custom logger injection
        >>> import logging
        >>> custom_logger = logging.getLogger("myapp.database")
        >>> LoggerAdapter.set_logger(custom_logger)
        >>> logger = LoggerAdapter.get_logger(__name__)  # Uses custom_logger
        
        >>> # Environment variable
        >>> # export ENGINE_KIT_LOGGER_NAME="myapp.database"
        >>> logger = LoggerAdapter.get_logger(__name__)  # Uses "myapp.database"
    """
    
    _custom_logger: Optional[logging.Logger] = None
    _default_loggers: dict[str, logging.Logger] = {}
    _default_configured = False
    
    @classmethod
    def get_logger(cls, name: str = "Database Engine") -> logging.Logger:
        """Get logger instance.
        
        This method follows a priority order to determine which logger to use:
        1. Custom injected logger (if set via set_logger())
        2. Host system's logger (from ENGINE_KIT_LOGGER_NAME env var)
        3. Root logger (if configured by host system)
        4. Default engine_kit logger (with basic console handler)
        
        Args:
            name: Logger name (typically __name__ or module name)
                - Examples: "engine_kit.engine", "engine_kit.config"
                - Default: "engine_kit"
            
        Returns:
            Logger instance that integrates with host system's logging
            
        Examples:
            >>> # In engine.py
            >>> logger = LoggerAdapter.get_logger(__name__)
            >>> logger.info("Engine started")
            
            >>> # In config module
            >>> logger = LoggerAdapter.get_logger("engine_kit.config")
            >>> logger.debug("Configuration loaded")
        """
        # 1. Check for custom logger (highest priority)
        if cls._custom_logger is not None:
            return cls._custom_logger
        
        # 3. Check if root logger is configured (host system might have configured it)
        root_logger = logging.getLogger()
        if root_logger.handlers:
            # Host system has configured logging, use it with our module name
            return logging.getLogger(name)
        
        # 4. Use default engine_kit logger (lazy initialization)
        if name not in cls._default_loggers:
            logger = logging.getLogger(name)
            
            # Only configure if not already configured
            if not logger.handlers and not cls._default_configured:
                cls._configure_default()
                cls._default_configured = True
            
            cls._default_loggers[name] = logger
        
        return cls._default_loggers[name]
    
    @classmethod
    def set_logger(cls, logger: logging.Logger) -> None:
        """Inject custom logger from host system.
        
        This method allows the host system to inject its own logger instance.
        Once set, all calls to get_logger() will return this logger, regardless
        of the name parameter.
        
        Args:
            logger: Logger instance from host system
                - Should be a properly configured logging.Logger instance
                - All engine-kit log messages will go through this logger
        
        Examples:
            >>> # FastAPI application
            >>> import logging
            >>> app_logger = logging.getLogger("myapp")
            >>> LoggerAdapter.set_logger(app_logger)
            >>> # Now all engine-kit logs use myapp logger
            
            >>> # Flask application
            >>> from flask import Flask
            >>> app = Flask(__name__)
            >>> LoggerAdapter.set_logger(app.logger)
            >>> # Now all engine-kit logs use Flask's logger
        """
        cls._custom_logger = logger
    
    @classmethod
    def reset_logger(cls) -> None:
        """Reset to default logger behavior.
        
        This method clears the custom logger and resets to automatic
        logger detection. Useful for testing or when switching between
        different logging configurations.
        
        Examples:
            >>> # Reset custom logger
            >>> LoggerAdapter.reset_logger()
            >>> # Now get_logger() will use automatic detection again
        """
        cls._custom_logger = None
    
    @classmethod
    def _configure_default(cls) -> None:
        """Configure default logging for engine-kit.
        
        This method sets up a basic console handler with a sensible
        default format. It only runs if:
        - No custom logger is set
        - No host system logger is found
        - Root logger is not configured
        
        The default configuration:
        - Level: INFO
        - Handler: StreamHandler (stdout)
        - Format: timestamp - name - level - message
        """
        # Get root engine_kit logger
        root_logger = logging.getLogger("engine_kit")
        root_logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if root_logger.handlers:
            return
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        root_logger.addHandler(handler)
        
        # Prevent propagation to root logger (avoid duplicate logs)
        root_logger.propagate = False