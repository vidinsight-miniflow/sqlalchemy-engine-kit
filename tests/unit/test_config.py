"""
Unit tests for config module
"""

import pytest
import os
from sqlalchemy_engine_kit.config import (
    DatabaseConfig,
    DatabaseType,
    EngineConfig,
    get_config_from_env,
    load_config_from_file,
)
from sqlalchemy_engine_kit.core.exceptions import InvalidInputError, DatabaseConfigurationError


class TestDatabaseConfig:
    """Tests for DatabaseConfig class."""
    
    def test_sqlite_config_creation(self):
        """Test SQLite configuration creation."""
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_name="test.db",
            sqlite_path="test.db"
        )
        assert config.db_type == DatabaseType.SQLITE
        assert config.db_name == "test.db"
        assert config.sqlite_path == "test.db"
    
    def test_postgresql_config_creation(self):
        """Test PostgreSQL configuration creation."""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            db_name="testdb",
            host="localhost",
            port=5432,
            username="user",
            password="pass"
        )
        assert config.db_type == DatabaseType.POSTGRESQL
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_port_auto_assignment(self):
        """Test automatic port assignment."""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            db_name="testdb",
            host="localhost",
            username="user",
            password="pass"
        )
        assert config.port == DatabaseType.POSTGRESQL.default_port()
    
    def test_for_development(self):
        """Test for_development factory method."""
        config = DatabaseConfig.for_development()
        assert config.db_type == DatabaseType.SQLITE
        assert config.sqlite_path == ":memory:"
        assert config.db_name == ":memory:"
    
    def test_for_testing(self):
        """Test for_testing factory method."""
        config = DatabaseConfig.for_testing("test.db")
        assert config.db_type == DatabaseType.SQLITE
        assert config.sqlite_path == "test.db"
    
    def test_get_connection_string_sqlite(self):
        """Test connection string generation for SQLite."""
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            sqlite_path="test.db"
        )
        conn_str = config.get_connection_string()
        assert "sqlite" in conn_str.lower()
        assert "test.db" in conn_str
    
    def test_get_connection_string_postgresql(self):
        """Test connection string generation for PostgreSQL."""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            db_name="testdb",
            host="localhost",
            port=5432,
            username="user",
            password="pass"
        )
        conn_str = config.get_connection_string()
        assert "postgresql" in conn_str.lower()
        assert "testdb" in conn_str
        assert "user" in conn_str
        # Password may be masked in connection string
        assert "pass" in conn_str or "***" in conn_str
    
    def test_invalid_port_raises_error(self):
        """Test that invalid port raises InvalidInputError."""
        with pytest.raises(InvalidInputError):
            DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                db_name="testdb",
                host="localhost",
                port=-1,
                username="user",
                password="pass"
            )
    
    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raise error."""
        with pytest.raises(InvalidInputError):
            DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                db_name="testdb",
                host="localhost",
                port=5432
                # Missing username/password
            )
    
    def test_to_dict_excludes_password(self):
        """Test that to_dict excludes password."""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            db_name="testdb",
            host="localhost",
            port=5432,
            username="user",
            password="secret"
        )
        config_dict = config.to_dict()
        assert "password" not in config_dict
        assert config_dict["username"] == "user"


class TestEngineConfig:
    """Tests for EngineConfig class."""
    
    def test_default_config(self):
        """Test default engine configuration."""
        config = EngineConfig()
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True
    
    def test_custom_config(self):
        """Test custom engine configuration."""
        config = EngineConfig(
            pool_size=5,
            max_overflow=10,
            pool_timeout=60,
            echo=True
        )
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 60
        assert config.echo is True
    
    def test_for_development(self):
        """Test for_development factory method."""
        config = EngineConfig.for_development()
        assert config.pool_size == 5
        assert config.echo is True
    
    def test_for_high_concurrency(self):
        """Test for_high_concurrency factory method."""
        config = EngineConfig.for_high_concurrency()
        assert config.pool_size >= 20
        assert config.max_overflow >= 20
    
    def test_merge_configs(self):
        """Test merging two configs."""
        config1 = EngineConfig(pool_size=10, echo=True)
        config2 = EngineConfig(pool_size=20, echo=False)
        
        merged = config1.merge(config2)
        assert merged.pool_size == 20  # config2 overrides
        assert merged.echo is False  # config2 overrides
        assert merged.pool_timeout == 30  # default from config1
    
    def test_invalid_pool_size_raises_error(self):
        """Test that invalid pool_size raises error."""
        with pytest.raises(InvalidInputError):
            EngineConfig(pool_size=-1)
    
    def test_to_dict(self):
        """Test to_dict method."""
        config = EngineConfig(pool_size=5, echo=True)
        config_dict = config.to_dict()
        assert config_dict["pool_size"] == 5
        assert config_dict["echo"] is True
        assert "pool_pre_ping" in config_dict
    
    def test_to_engine_kwargs(self):
        """Test to_engine_kwargs method."""
        config = EngineConfig(pool_size=5, echo=True)
        kwargs = config.to_engine_kwargs()
        assert kwargs["pool_size"] == 5
        assert kwargs["echo"] is True
        assert "autocommit" not in kwargs  # Session setting, not engine setting


class TestDatabaseType:
    """Tests for DatabaseType enum."""
    
    def test_all_types(self):
        """Test all_types class method."""
        types = DatabaseType.all_types()
        assert DatabaseType.SQLITE in types
        assert DatabaseType.POSTGRESQL in types
        assert DatabaseType.MYSQL in types
    
    def test_network_based(self):
        """Test network_based class method."""
        network_types = DatabaseType.network_based()
        assert DatabaseType.SQLITE not in network_types
        assert DatabaseType.POSTGRESQL in network_types
        assert DatabaseType.MYSQL in network_types
    
    def test_default_port(self):
        """Test default_port method."""
        assert DatabaseType.POSTGRESQL.default_port() == 5432
        assert DatabaseType.MYSQL.default_port() == 3306
        assert DatabaseType.SQLITE.default_port() == 0
    
    def test_requires_credentials(self):
        """Test requires_credentials method."""
        assert DatabaseType.SQLITE.requires_credentials() is False
        assert DatabaseType.POSTGRESQL.requires_credentials() is True
        assert DatabaseType.MYSQL.requires_credentials() is True


class TestEnvLoader:
    """Tests for environment loader functions."""
    
    def test_get_config_from_env_sqlite(self, monkeypatch):
        """Test loading SQLite config from environment."""
        try:
            from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
            if not ENV_LOADER_AVAILABLE:
                pytest.skip("python-dotenv not installed")
        except ImportError:
            pytest.skip("python-dotenv not installed")
        
        monkeypatch.setenv("DB_TYPE", "sqlite")
        monkeypatch.setenv("DB_SQLITE_PATH", "test.db")
        
        try:
        config = get_config_from_env()
        except ImportError as e:
            if "python-dotenv" in str(e):
                pytest.skip("python-dotenv not installed")
            raise
        assert config.db_type == DatabaseType.SQLITE
        assert config.sqlite_path == "test.db"
    
    def test_get_config_from_env_postgresql(self, monkeypatch):
        """Test loading PostgreSQL config from environment."""
        try:
            from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
            if not ENV_LOADER_AVAILABLE:
                pytest.skip("python-dotenv not installed")
        except ImportError:
            pytest.skip("python-dotenv not installed")
        
        monkeypatch.setenv("DB_TYPE", "postgresql")
        monkeypatch.setenv("DB_NAME", "testdb")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "pass")
        
        try:
        config = get_config_from_env()
        except ImportError as e:
            if "python-dotenv" in str(e):
                pytest.skip("python-dotenv not installed")
            raise
        assert config.db_type == DatabaseType.POSTGRESQL
        assert config.db_name == "testdb"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_get_config_from_env_custom_prefix(self, monkeypatch):
        """Test loading config with custom prefix."""
        try:
            from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
            if not ENV_LOADER_AVAILABLE:
                pytest.skip("python-dotenv not installed")
        except ImportError:
            pytest.skip("python-dotenv not installed")
        
        monkeypatch.setenv("MYAPP_DB_TYPE", "sqlite")
        monkeypatch.setenv("MYAPP_DB_SQLITE_PATH", "custom.db")
        
        try:
        config = get_config_from_env(prefix="MYAPP_DB_")
        except ImportError as e:
            if "python-dotenv" in str(e):
                pytest.skip("python-dotenv not installed")
            raise
        assert config.db_type == DatabaseType.SQLITE
        assert config.sqlite_path == "custom.db"
    
    def test_load_config_from_file(self, tmp_path):
        """Test loading config from .env file."""
        try:
            from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
            if not ENV_LOADER_AVAILABLE:
                pytest.skip("python-dotenv not installed")
        except ImportError:
            pytest.skip("python-dotenv not installed")
        
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DB_TYPE=sqlite\n"
            "DB_SQLITE_PATH=file.db\n"
        )
        
        try:
        config = load_config_from_file(str(env_file))
        except ImportError as e:
            if "python-dotenv" in str(e):
                pytest.skip("python-dotenv not installed")
            raise
        assert config.db_type == DatabaseType.SQLITE
        assert config.sqlite_path == "file.db"
    
    def test_missing_required_env_vars_raises_error(self, monkeypatch):
        """Test that missing required env vars raise error."""
        try:
            from sqlalchemy_engine_kit.config import ENV_LOADER_AVAILABLE
            if not ENV_LOADER_AVAILABLE:
                pytest.skip("python-dotenv not installed")
        except ImportError:
            pytest.skip("python-dotenv not installed")
        
        monkeypatch.setenv("DB_TYPE", "postgresql")
        # Missing DB_NAME, DB_HOST, etc.
        
        try:
        with pytest.raises(DatabaseConfigurationError):
            get_config_from_env()
        except ImportError as e:
            if "python-dotenv" in str(e):
                pytest.skip("python-dotenv not installed")
            raise

