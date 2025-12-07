"""
Performance and stress tests for engine-kit
"""

import pytest
import time
from sqlalchemy.orm import Session
from sqlalchemy_engine_kit import with_session
from sqlalchemy_engine_kit.models import Base
from tests.fixtures.sample_models import SimpleModel

# Repository pattern not available in this version
REPOSITORIES_AVAILABLE = False
BaseRepository = None
bulk_insert = None


class TestBulkOperationsPerformance:
    """Tests for bulk operation performance."""
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_bulk_insert_performance(self, test_manager):
        """Test bulk insert performance with large dataset."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Prepare large dataset
        large_dataset = [
            {"name": f"Item {i}", "value": i}
            for i in range(1000)
        ]
        
        @with_session()
        def perform_bulk_insert(session: Session):
            start_time = time.time()
            result = bulk_insert(session, SimpleModel, large_dataset)
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time (< 5 seconds for 1000 items)
            assert elapsed < 5.0
            assert len(result) == 1000
            return elapsed
        
        elapsed = perform_bulk_insert()
        
        # Verify data was inserted
        @with_session()
        def verify_count(session: Session):
            return session.query(SimpleModel).count()
        
        count = verify_count()
        assert count == 1000
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_bulk_update_performance(self, test_manager):
        """Test bulk update performance."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create test data
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(100):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        # Prepare updates
        updates = [
            {"id": i + 1, "name": f"Updated Item {i}", "value": i * 2}
            for i in range(100)
        ]
        
        @with_session()
        def perform_bulk_update(session: Session):
            from sqlalchemy_engine_kit.repositories import bulk_update
            start_time = time.time()
            result = bulk_update(session, SimpleModel, updates, key="id")
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time
            assert elapsed < 2.0
            return elapsed
        
        elapsed = perform_bulk_update()
        
        # Verify updates
        @with_session()
        def verify_updates(session: Session):
            item = session.query(SimpleModel).filter_by(id=1).first()
            return item.name if item else None
        
        name = verify_updates()
        assert "Updated" in name
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_bulk_delete_performance(self, test_manager):
        """Test bulk delete performance."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create test data
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(500):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        @with_session()
        def perform_bulk_delete(session: Session):
            from sqlalchemy_engine_kit.repositories import bulk_delete
            ids_to_delete = list(range(1, 501))
            
            start_time = time.time()
            result = bulk_delete(session, SimpleModel, ids_to_delete)
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time
            assert elapsed < 2.0
            return elapsed
        
        elapsed = perform_bulk_delete()
        
        # Verify deletion
        @with_session()
        def verify_deletion(session: Session):
            return session.query(SimpleModel).count()
        
        count = verify_deletion()
        assert count == 0


class TestQueryPerformance:
    """Tests for query performance."""
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_large_result_set_handling(self, test_manager):
        """Test handling of large result sets."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create large dataset
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(5000):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        @with_session()
        def query_all(session: Session):
            start_time = time.time()
            results = session.query(SimpleModel).all()
            elapsed = time.time() - start_time
            
            assert len(results) == 5000
            # Should complete in reasonable time
            assert elapsed < 10.0
            return elapsed
        
        elapsed = query_all()
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_pagination_performance(self, test_manager):
        """Test pagination performance with large datasets."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create large dataset
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(10000):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        @with_session()
        def paginate(session: Session):
            from sqlalchemy_engine_kit.repositories import paginate_with_meta
            
            start_time = time.time()
            result = paginate_with_meta(
                session.query(SimpleModel),
                page=1,
                page_size=100
            )
            elapsed = time.time() - start_time
            
            assert result.total == 10000
            assert len(result.items) == 100
            # Pagination should be fast even with large datasets
            assert elapsed < 1.0
            return elapsed
        
        elapsed = paginate()
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_filter_performance(self, test_manager):
        """Test filter query performance."""
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create test data
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(1000):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        @with_session()
        def filter_query(session: Session):
            start_time = time.time()
            results = session.query(SimpleModel).filter(
                SimpleModel.value > 500
            ).all()
            elapsed = time.time() - start_time
            
            assert len(results) == 499  # 501 to 999
            # Should be fast
            assert elapsed < 1.0
            return elapsed
        
        elapsed = filter_query()


class TestConcurrentPerformance:
    """Tests for concurrent operation performance."""
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_concurrent_inserts(self, test_manager):
        """Test performance of concurrent inserts."""
        import threading
        
        Base.metadata.create_all(test_manager.engine._engine)
        
        results = []
        errors = []
        
        def insert_worker(worker_id, count):
            @with_session()
            def insert_items(session: Session):
                repo = BaseRepository(SimpleModel, session)
                for i in range(count):
                    try:
                        repo.create(name=f"Worker {worker_id} Item {i}", value=worker_id * 1000 + i)
                    except Exception as e:
                        errors.append(e)
                        raise
        
            try:
                insert_items()
                results.append(worker_id)
            except Exception as e:
                errors.append(e)
        
        # Create 5 workers, each inserting 100 items
        threads = []
        start_time = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=insert_worker, args=(i, 100))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        
        # Should complete successfully
        assert len(errors) == 0
        assert len(results) == 5
        
        # Should complete in reasonable time
        assert elapsed < 10.0
        
        # Verify all data was inserted
        @with_session()
        def verify_count(session: Session):
            return session.query(SimpleModel).count()
        
        count = verify_count()
        assert count == 500  # 5 workers * 100 items
    
    @pytest.mark.skipif(not REPOSITORIES_AVAILABLE, reason="Repositories module not available")
    def test_concurrent_reads(self, test_manager):
        """Test performance of concurrent reads."""
        import threading
        
        Base.metadata.create_all(test_manager.engine._engine)
        
        # Create test data
        @with_session()
        def create_data(session: Session):
            repo = BaseRepository(SimpleModel, session)
            for i in range(100):
                repo.create(name=f"Item {i}", value=i)
        
        create_data()
        
        results = []
        errors = []
        
        def read_worker(worker_id):
            @with_session()
            def read_items(session: Session):
                try:
                    items = session.query(SimpleModel).limit(10).all()
                    results.append(len(items))
                except Exception as e:
                    errors.append(e)
                    raise
        
            try:
                read_items()
            except Exception as e:
                errors.append(e)
        
        # Create 10 concurrent readers
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=read_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed = time.time() - start_time
        
        # Should complete successfully
        assert len(errors) == 0
        assert len(results) == 10
        
        # Concurrent reads should be fast
        assert elapsed < 2.0

