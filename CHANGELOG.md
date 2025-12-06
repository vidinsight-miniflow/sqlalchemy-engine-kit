# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-06

### Added
- Initial release of sqlalchemy-engine-kit
- DatabaseManager singleton pattern for application-wide engine management
- DatabaseEngine wrapper with connection pooling and health checks
- Decorator-based session management (`@with_session`, `@with_transaction`, `@with_readonly_session`)
- Model mixins (TimestampMixin, SoftDeleteMixin, AuditMixin)
- Alembic migration integration
- Modular logging with LoggerAdapter
- Pluggable monitoring interface (NoOpMonitor, PrometheusMonitor)
- Comprehensive error handling with custom exception hierarchy
- Retry logic for transient errors
- Comprehensive test suite (158 passed, 81 skipped)
- Full documentation (API Reference, Examples, Best Practices, Architecture, Migration Guide)

### Features
- Thread-safe singleton pattern
- Automatic session lifecycle management
- Connection pool health monitoring
- Production-ready error handling
- Modular and extensible architecture

[0.1.0]: https://github.com/vidinsight/sqlalchemy-engine-kit/releases/tag/v0.1.0

