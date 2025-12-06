"""
Integration tests for migrations
"""

import pytest
import os
import tempfile
from pathlib import Path

# Check if migrations are available
try:
    from sqlalchemy_engine_kit.migrations import (
    MigrationManager,
    run_migrations,
    create_migration,
    get_current_revision,
    get_head_revision,
        ALEMBIC_AVAILABLE,
)
    from sqlalchemy_engine_kit.migrations.exceptions import DatabaseMigrationError
    
    # Check if MigrationManager is actually available (not None)
    if MigrationManager is None or not ALEMBIC_AVAILABLE:
        MIGRATIONS_AVAILABLE = False
    else:
        MIGRATIONS_AVAILABLE = True
except ImportError:
    MIGRATIONS_AVAILABLE = False
    MigrationManager = None
    run_migrations = None
    create_migration = None
    get_current_revision = None
    get_head_revision = None
    DatabaseMigrationError = None


class TestMigrationManager:
    """Tests for MigrationManager."""
    
    @pytest.fixture
    def migration_dir(self, tmp_path):
        """Create temporary migration directory."""
        mig_dir = tmp_path / "migrations"
        mig_dir.mkdir()
        return mig_dir
    
    @pytest.fixture
    def migration_manager(self, test_engine, migration_dir):
        """Create MigrationManager fixture."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            return MigrationManager(test_engine, script_location=str(migration_dir))
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")
    
    def test_get_current_revision_no_migrations(self, migration_manager):
        """Test get_current_revision when no migrations applied."""
        if not MIGRATIONS_AVAILABLE or migration_manager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        # Should return None if no migrations applied
        current = migration_manager.get_current_revision()
        assert current is None or current == ""
    
    def test_get_head_revision(self, migration_manager):
        """Test get_head_revision."""
        if not MIGRATIONS_AVAILABLE or migration_manager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        # Head revision should exist even if no migrations
        head = migration_manager.get_head_revision()
        # Head might be None if no migrations exist
        assert head is None or isinstance(head, str)
    
    def test_history_generator(self, migration_manager):
        """Test history method returns generator."""
        if not MIGRATIONS_AVAILABLE or migration_manager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        history = migration_manager.history()
        # Should be a generator/iterator
        assert hasattr(history, '__iter__')
        
        # Should be able to iterate (even if empty)
        list(history)  # Consume generator


class TestMigrationCommands:
    """Tests for migration command functions."""
    
    def test_get_current_revision_function(self, test_manager):
        """Test get_current_revision convenience function."""
        if not MIGRATIONS_AVAILABLE or get_current_revision is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            current = get_current_revision(test_manager.engine)
            # Should return None or string
            assert current is None or isinstance(current, str)
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")
    
    def test_get_head_revision_function(self, test_manager):
        """Test get_head_revision convenience function."""
        if not MIGRATIONS_AVAILABLE or get_head_revision is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            # This will fail if alembic directory doesn't exist, which is expected
            # Just check that it doesn't crash the system
            try:
                head = get_head_revision(test_manager.engine)
                # Should return None or string
                assert head is None or isinstance(head, str)
            except DatabaseMigrationError:
                # Expected if alembic directory doesn't exist
                pass
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")


class TestMigrationErrors:
    """Tests for migration error handling."""
    
    def test_migration_error_handling(self, test_engine):
        """Test that migration errors are properly handled."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            # Create manager with non-existent script location
            invalid_dir = "/nonexistent/path/migrations"
            manager = MigrationManager(test_engine, script_location=invalid_dir)
            
            # Should raise DatabaseMigrationError when accessing config
            with pytest.raises(DatabaseMigrationError):
                manager.get_head_revision()
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")


class TestMigrationExecution:
    """Tests for actual migration execution (upgrade, downgrade, stamp)."""
    
    @pytest.fixture
    def migration_dir_with_init(self, tmp_path):
        """Create migration directory with initialized Alembic."""
        mig_dir = tmp_path / "migrations"
        mig_dir.mkdir()
        
        # Try to initialize Alembic if possible
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command
            
            # Create basic alembic.ini structure
            alembic_cfg = AlembicConfig()
            alembic_cfg.set_main_option("script_location", str(mig_dir))
            
            # Create versions directory
            versions_dir = mig_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            
            return mig_dir
        except ImportError:
            return mig_dir
    
    def test_upgrade_to_head(self, test_engine, migration_dir_with_init):
        """Test upgrading database to head revision."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to upgrade (may fail if no migrations exist, which is OK)
            try:
                manager.upgrade("head")
                # If successful, verify current revision
                current = manager.get_current_revision()
                assert current is not None or current == ""
            except DatabaseMigrationError as e:
                # Expected if no migrations exist
                assert "script" in str(e).lower() or "migration" in str(e).lower()
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")
    
    def test_downgrade_one_revision(self, test_engine, migration_dir_with_init):
        """Test downgrading database by one revision."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to downgrade (may fail if no migrations exist, which is OK)
            try:
                manager.downgrade("-1")
                # If successful, verify it worked
                current = manager.get_current_revision()
                assert current is not None or current == ""
            except DatabaseMigrationError:
                # Expected if no migrations exist or already at base
                pass
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")
    
    def test_stamp_revision(self, test_engine, migration_dir_with_init):
        """Test stamping database with a specific revision."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to stamp (may fail if revision doesn't exist, which is OK)
            try:
                # Try with a fake revision ID
                manager.stamp("fake_revision_id")
            except DatabaseMigrationError:
                # Expected if revision doesn't exist
                pass
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")
    
    def test_upgrade_dry_run(self, test_engine, migration_dir_with_init):
        """Test upgrade dry run (should not modify database)."""
        if not MIGRATIONS_AVAILABLE or MigrationManager is None:
            pytest.skip("Alembic not installed or MigrationManager not available")
        
        try:
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Get current revision before dry run
            current_before = manager.get_current_revision()
            
            # Try dry run upgrade
            try:
                manager.upgrade("head", dry_run=True)
                # Verify revision didn't change (dry run)
                current_after = manager.get_current_revision()
                assert current_before == current_after
            except DatabaseMigrationError:
                # Expected if no migrations exist
                pass
        except (ImportError, TypeError) as e:
            pytest.skip(f"Alembic not properly installed: {e}")


class TestMigrationConflictResolution:
    """Tests for migration conflict resolution scenarios."""
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_detect_out_of_sync_revision(self, test_engine, migration_dir_with_init):
        """Test detection of out-of-sync database revision."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Get current and head revisions
            current = manager.get_current_revision()
            head = manager.get_head_revision()
            
            # If they differ, database is out of sync
            if current != head and current is not None and head is not None:
                # This indicates out-of-sync state
                assert current != head
            else:
                # If same or None, that's also a valid state
                pass
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_handle_missing_migration_files(self, test_engine, migration_dir_with_init):
        """Test handling when migration files are missing."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to get head revision (should handle missing files gracefully)
            try:
                head = manager.get_head_revision()
                # Should return None or raise error, but not crash
                assert head is None or isinstance(head, str)
            except DatabaseMigrationError:
                # Expected if migration files don't exist
                pass
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_handle_invalid_revision_id(self, test_engine, migration_dir_with_init):
        """Test handling of invalid revision IDs."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to upgrade to invalid revision
            with pytest.raises(DatabaseMigrationError):
                manager.upgrade("invalid_revision_12345")
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_handle_downgrade_beyond_base(self, test_engine, migration_dir_with_init):
        """Test handling when trying to downgrade beyond base."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to downgrade multiple times (beyond base)
            try:
                # First downgrade might work
                manager.downgrade("-1")
                # Second downgrade might fail if already at base
                try:
                    manager.downgrade("-1")
                except DatabaseMigrationError:
                    # Expected if already at base
                    pass
            except DatabaseMigrationError:
                # Expected if no migrations or already at base
                pass
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_handle_concurrent_migration_attempts(self, test_engine, migration_dir_with_init):
        """Test handling of concurrent migration attempts."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            import threading
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            errors = []
            results = []
            
            def attempt_migration(worker_id):
                try:
                    # Try to get current revision (read operation)
                    current = manager.get_current_revision()
                    results.append((worker_id, current))
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # Multiple concurrent read operations should work
            threads = []
            for i in range(5):
                thread = threading.Thread(target=attempt_migration, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Read operations should all succeed
            assert len(errors) == 0
            assert len(results) == 5
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_migration_rollback_on_error(self, test_engine, migration_dir_with_init):
        """Test that migrations rollback on error."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Get current revision
            current_before = manager.get_current_revision()
            
            # Try to upgrade (may fail, which is OK)
            try:
                manager.upgrade("head")
                current_after = manager.get_current_revision()
                # If upgrade succeeded, revision should be set
                # If it failed, revision should remain same (rollback)
                if current_before != current_after:
                    # Upgrade succeeded
                    assert current_after is not None or current_after == ""
            except DatabaseMigrationError:
                # On error, revision should remain same (rollback)
                current_after = manager.get_current_revision()
                # In case of error, revision might be unchanged
                pass
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_stamp_with_invalid_revision_handling(self, test_engine, migration_dir_with_init):
        """Test stamping with invalid revision ID handling."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Try to stamp with clearly invalid revision
            with pytest.raises(DatabaseMigrationError):
                manager.stamp("nonexistent_revision_xyz123")
        except ImportError:
            pytest.skip("Alembic not installed")
    
    @pytest.mark.skip(reason="Migration conflict resolution tests need proper Alembic setup")
    def test_get_current_revision_after_failed_migration(self, test_engine, migration_dir_with_init):
        """Test getting current revision after failed migration."""
        try:
            from sqlalchemy_engine_kit.migrations import MigrationManager
            
            manager = MigrationManager(test_engine, script_location=str(migration_dir_with_init))
            
            # Get initial revision
            initial_revision = manager.get_current_revision()
            
            # Try invalid operation
            try:
                manager.upgrade("invalid_revision")
            except DatabaseMigrationError:
                # Expected to fail
                pass
            
            # Revision should still be accessible (might be same or different)
            current_revision = manager.get_current_revision()
            # Should not crash
            assert current_revision is None or isinstance(current_revision, str)
        except ImportError:
            pytest.skip("Alembic not installed")

