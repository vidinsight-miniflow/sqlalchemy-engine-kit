"""
Integration tests for repositories

NOTE: Repository pattern is not included in this version.
All tests in this file are skipped.
"""

import pytest

# Repository pattern not available in this version
pytestmark = pytest.mark.skip(reason="Repository pattern not included in this version")


class TestBaseRepository:
    """Tests for BaseRepository."""
    
    @pytest.fixture
    def repo(self, test_session):
        """Create repository fixture."""
        return BaseRepository(SimpleModel, test_session)
    
    def test_create(self, repo, test_session):
        """Test repository create method."""
        Base.metadata.create_all(test_session.bind)
        
        user = repo.create(name="Test", value=42)
        
        assert user.id is not None
        assert user.name == "Test"
        assert user.value == 42
    
    def test_get_by_id(self, repo, test_session):
        """Test repository get_by_id method."""
        Base.metadata.create_all(test_session.bind)
        
        user = repo.create(name="Test", value=42)
        test_session.commit()
        
        found = repo.get_by_id(user.id)
        assert found is not None
        assert found.id == user.id
        assert found.name == "Test"
    
    def test_get_by_id_not_found(self, repo, test_session):
        """Test get_by_id with non-existent ID."""
        Base.metadata.create_all(test_session.bind)
        
        found = repo.get_by_id(99999)
        assert found is None
    
    def test_get_all(self, repo, test_session):
        """Test repository get_all method."""
        Base.metadata.create_all(test_session.bind)
        
        # Create multiple records
        for i in range(5):
            repo.create(name=f"Item {i}", value=i)
        test_session.commit()
        
        all_items = repo.get_all()
        assert len(all_items) == 5
    
    def test_get_all_with_limit(self, repo, test_session):
        """Test get_all with limit."""
        Base.metadata.create_all(test_session.bind)
        
        # Create multiple records
        for i in range(10):
            repo.create(name=f"Item {i}", value=i)
        test_session.commit()
        
        items = repo.get_all(limit=3)
        assert len(items) == 3
    
    def test_update(self, repo, test_session):
        """Test repository update method."""
        Base.metadata.create_all(test_session.bind)
        
        user = repo.create(name="Test", value=42)
        test_session.commit()
        
        updated = repo.update(user.id, name="Updated", value=100)
        
        assert updated.name == "Updated"
        assert updated.value == 100
    
    def test_delete(self, repo, test_session):
        """Test repository delete method."""
        Base.metadata.create_all(test_session.bind)
        
        user = repo.create(name="Test", value=42)
        test_session.commit()
        
        success = repo.delete(user.id)
        assert success is True
        
        found = repo.get_by_id(user.id)
        assert found is None
    
    def test_filter(self, repo, test_session):
        """Test repository filter method."""
        Base.metadata.create_all(test_session.bind)
        
        repo.create(name="Test 1", value=10)
        repo.create(name="Test 2", value=20)
        repo.create(name="Other", value=30)
        test_session.commit()
        
        filtered = repo.filter(name="Test 1")
        assert len(filtered) == 1
        assert filtered[0].name == "Test 1"
    
    def test_count(self, repo, test_session):
        """Test repository count method."""
        Base.metadata.create_all(test_session.bind)
        
        for i in range(5):
            repo.create(name=f"Item {i}", value=i)
        test_session.commit()
        
        count = repo.count()
        assert count == 5
    
    def test_exists(self, repo, test_session):
        """Test repository exists method."""
        Base.metadata.create_all(test_session.bind)
        
        user = repo.create(name="Test", value=42)
        test_session.commit()
        
        assert repo.exists(user.id) is True
        assert repo.exists(99999) is False
    
    def test_bulk_create(self, repo, test_session):
        """Test repository bulk_create method."""
        Base.metadata.create_all(test_session.bind)
        
        items = [
            {"name": f"Item {i}", "value": i}
            for i in range(5)
        ]
        
        created = repo.bulk_create(items)
        assert len(created) == 5
        assert all(item.id is not None for item in created)


class TestSoftDeleteHelpers:
    """Tests for soft delete query helpers."""
    
    @pytest.fixture
    def user_repo(self, test_session):
        """Create user repository fixture."""
        return BaseRepository(User, test_session)
    
    def test_get_active(self, user_repo, test_session):
        """Test get_active method."""
        Base.metadata.create_all(test_session.bind)
        
        # Create active and deleted users
        user1 = user_repo.create(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = user_repo.create(email="user2@test.com", name="User 2", password_hash="hash")
        user2.soft_delete()
        test_session.commit()
        
        active = user_repo.get_active()
        assert len(active) == 1
        assert active[0].id == user1.id
    
    def test_get_deleted(self, user_repo, test_session):
        """Test get_deleted method."""
        Base.metadata.create_all(test_session.bind)
        
        # Create active and deleted users
        user1 = user_repo.create(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = user_repo.create(email="user2@test.com", name="User 2", password_hash="hash")
        user2.soft_delete()
        test_session.commit()
        
        deleted = user_repo.get_deleted()
        assert len(deleted) == 1
        assert deleted[0].id == user2.id
    
    def test_filter_active(self, user_repo, test_session):
        """Test filter_active method."""
        Base.metadata.create_all(test_session.bind)
        
        # Create active and deleted users
        user1 = user_repo.create(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = user_repo.create(email="user2@test.com", name="User 2", password_hash="hash")
        user2.soft_delete()
        test_session.commit()
        
        query = test_session.query(User)
        query = user_repo.filter_active(query)
        active = query.all()
        
        assert len(active) == 1
        assert active[0].id == user1.id


class TestBulkOperations:
    """Tests for bulk operations."""
    
    def test_bulk_insert(self, test_session):
        """Test bulk_insert function."""
        Base.metadata.create_all(test_session.bind)
        
        items = [
            {"name": f"Item {i}", "value": i}
            for i in range(5)
        ]
        
        created = bulk_insert(test_session, SimpleModel, items)
        test_session.commit()
        
        assert len(created) == 5
        assert all(item.id is not None for item in created)
    
    def test_bulk_update(self, test_session):
        """Test bulk_update function."""
        Base.metadata.create_all(test_session.bind)
        
        # Create items first
        items = [
            SimpleModel(name=f"Item {i}", value=i)
            for i in range(5)
        ]
        for item in items:
            test_session.add(item)
        test_session.commit()
        
        # Store original values before update
        original_values = {item.id: item.value for item in items}
        
        # Update all
        updates = [
            {"id": item.id, "value": item.value * 2}
            for item in items
        ]
        
        bulk_update(test_session, SimpleModel, updates)
        test_session.commit()
        
        # Verify updates (refresh to get updated values)
        test_session.expire_all()
        for item in items:
            test_session.refresh(item)
            expected_value = original_values[item.id] * 2
            assert item.value == expected_value
    
    def test_bulk_delete(self, test_session):
        """Test bulk_delete function."""
        Base.metadata.create_all(test_session.bind)
        
        # Create items first
        items = [
            SimpleModel(name=f"Item {i}", value=i)
            for i in range(5)
        ]
        for item in items:
            test_session.add(item)
        test_session.commit()
        
        # Delete all
        ids_to_delete = [item.id for item in items]
        bulk_delete(test_session, SimpleModel, ids_to_delete)
        test_session.commit()
        
        # Verify deleted
        count = test_session.query(SimpleModel).count()
        assert count == 0


class TestPagination:
    """Tests for pagination utilities."""
    
    def test_paginate_with_meta(self, test_session):
        """Test paginate_with_meta function."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(25):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        result = paginate_with_meta(query, page=1, page_size=10)
        
        assert isinstance(result, PaginationResult)
        assert len(result.items) == 10
        assert result.total == 25
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 3
        assert result.has_next is True
        assert result.has_prev is False
    
    def test_paginate_with_meta_last_page(self, test_session):
        """Test paginate_with_meta on last page."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(25):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        result = paginate_with_meta(query, page=3, page_size=10)
        
        assert len(result.items) == 5
        assert result.has_next is False
        assert result.has_prev is True
    
    def test_pagination_result_to_dict(self, test_session):
        """Test PaginationResult.to_dict method."""
        Base.metadata.create_all(test_session.bind)
        
        query = test_session.query(SimpleModel)
        result = paginate_with_meta(query, page=1, page_size=10)
        
        result_dict = result.to_dict()
        assert "items" in result_dict
        assert "pagination" in result_dict
        assert result_dict["pagination"]["page"] == 1
        assert result_dict["pagination"]["total"] == 0


class TestEagerLoading:
    """Tests for eager loading utilities."""
    
    def test_with_relationships(self, test_session):
        """Test with_relationships function."""
        Base.metadata.create_all(test_session.bind)
        
        # Create user with posts
        user = User(email="test@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        post1 = Post(title="Post 1", content="Content 1", user_id=user.id)
        post2 = Post(title="Post 2", content="Content 2", user_id=user.id)
        test_session.add(post1)
        test_session.add(post2)
        test_session.commit()
        
        # Query with eager loading (use string for relationship name)
        query = test_session.query(User)
        query = with_relationships(query, 'posts', strategy='joined')
        users = query.all()
        
        assert len(users) == 1
        # Accessing posts should not trigger additional query (N+1 prevention)
        assert len(users[0].posts) == 2

