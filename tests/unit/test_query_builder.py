"""
Unit tests for QueryBuilder utilities

NOTE: Repository pattern is not included in this version.
All tests in this file are skipped.
"""

import pytest

# Repository pattern not available in this version
pytestmark = pytest.mark.skip(reason="Repository pattern not included in this version")


class TestQueryBuilderPaginate:
    """Tests for QueryBuilder.paginate method."""
    
    def test_paginate_first_page(self, test_session):
        """Test pagination for first page."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(20):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        paginated = QueryBuilder.paginate(query, page=1, page_size=10)
        results = paginated.all()
        
        assert len(results) == 10
        assert results[0].name == "Item 0"
        assert results[9].name == "Item 9"
    
    def test_paginate_second_page(self, test_session):
        """Test pagination for second page."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(20):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        paginated = QueryBuilder.paginate(query, page=2, page_size=10)
        results = paginated.all()
        
        assert len(results) == 10
        assert results[0].name == "Item 10"
        assert results[9].name == "Item 19"
    
    def test_paginate_invalid_page(self, test_session):
        """Test pagination with invalid page number."""
        query = test_session.query(SimpleModel)
        
        with pytest.raises(ValueError, match="Page must be >= 1"):
            QueryBuilder.paginate(query, page=0, page_size=10)
        
        with pytest.raises(ValueError, match="Page must be >= 1"):
            QueryBuilder.paginate(query, page=-1, page_size=10)
    
    def test_paginate_invalid_page_size(self, test_session):
        """Test pagination with invalid page size."""
        query = test_session.query(SimpleModel)
        
        with pytest.raises(ValueError, match="Page size must be >= 1"):
            QueryBuilder.paginate(query, page=1, page_size=0)
        
        with pytest.raises(ValueError, match="Page size must be >= 1"):
            QueryBuilder.paginate(query, page=1, page_size=-1)
    
    def test_paginate_empty_result(self, test_session):
        """Test pagination with empty result set."""
        Base.metadata.create_all(test_session.bind)
        
        query = test_session.query(SimpleModel)
        paginated = QueryBuilder.paginate(query, page=1, page_size=10)
        results = paginated.all()
        
        assert len(results) == 0


class TestQueryBuilderOrderBy:
    """Tests for QueryBuilder.order_by method."""
    
    def test_order_by_ascending(self, test_session):
        """Test ordering ascending."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(SimpleModel(name="C", value=3))
        test_session.add(SimpleModel(name="A", value=1))
        test_session.add(SimpleModel(name="B", value=2))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        ordered = QueryBuilder.order_by(query, field="name", descending=False)
        results = ordered.all()
        
        assert len(results) == 3
        assert results[0].name == "A"
        assert results[1].name == "B"
        assert results[2].name == "C"
    
    def test_order_by_descending(self, test_session):
        """Test ordering descending."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(SimpleModel(name="C", value=3))
        test_session.add(SimpleModel(name="A", value=1))
        test_session.add(SimpleModel(name="B", value=2))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        ordered = QueryBuilder.order_by(query, field="name", descending=True)
        results = ordered.all()
        
        assert len(results) == 3
        assert results[0].name == "C"
        assert results[1].name == "B"
        assert results[2].name == "A"
    
    def test_order_by_invalid_field(self, test_session):
        """Test ordering with invalid field."""
        Base.metadata.create_all(test_session.bind)
        
        query = test_session.query(SimpleModel)
        
        with pytest.raises(AttributeError):
            QueryBuilder.order_by(query, field="nonexistent", descending=False)


class TestQueryBuilderSearch:
    """Tests for QueryBuilder.search method."""
    
    def test_search_single_field(self, test_session):
        """Test search in single field."""
        Base.metadata.create_all(test_session.bind)
        
        # Clean up first
        test_session.query(User).delete()
        test_session.commit()
        
        # Create test data
        test_session.add(User(email="john@example.com", name="John Doe", password_hash="hash"))
        test_session.add(User(email="jane@example.com", name="Jane Smith", password_hash="hash"))
        test_session.add(User(email="bob@example.com", name="Bob Smith", password_hash="hash"))
        test_session.commit()
        
        query = test_session.query(User)
        searched = QueryBuilder.search(query, search_term="john", fields=["name"])
        results = searched.all()
        
        assert len(results) == 1
        assert "john" in results[0].name.lower()
    
    def test_search_multiple_fields(self, test_session):
        """Test search in multiple fields."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(User(email="john@example.com", name="John Doe", password_hash="hash"))
        test_session.add(User(email="jane@example.com", name="Jane Smith", password_hash="hash"))
        test_session.add(User(email="bob@example.com", name="Bob Johnson", password_hash="hash"))
        test_session.commit()
        
        query = test_session.query(User)
        searched = QueryBuilder.search(query, search_term="example", fields=["email", "name"])
        results = searched.all()
        
        assert len(results) == 3  # All have "example" in email
    
    def test_search_case_insensitive(self, test_session):
        """Test case-insensitive search."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(User(email="John@Example.com", name="John Doe", password_hash="hash"))
        test_session.commit()
        
        query = test_session.query(User)
        searched = QueryBuilder.search(query, search_term="john", fields=["name"], case_sensitive=False)
        results = searched.all()
        
        assert len(results) == 1
    
    def test_search_no_results(self, test_session):
        """Test search with no matching results."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(User(email="john@example.com", name="John Doe", password_hash="hash"))
        test_session.commit()
        
        query = test_session.query(User)
        searched = QueryBuilder.search(query, search_term="nonexistent", fields=["name"])
        results = searched.all()
        
        assert len(results) == 0


class TestQueryBuilderFilterByRange:
    """Tests for QueryBuilder.filter_by_range method."""
    
    def test_filter_by_range_min_only(self, test_session):
        """Test range filter with minimum value only."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(10):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_range(query, field="value", min_value=5)
        results = filtered.all()
        
        assert len(results) == 5
        assert all(r.value >= 5 for r in results)
    
    def test_filter_by_range_max_only(self, test_session):
        """Test range filter with maximum value only."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(10):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_range(query, field="value", max_value=4)
        results = filtered.all()
        
        assert len(results) == 5
        assert all(r.value <= 4 for r in results)
    
    def test_filter_by_range_both(self, test_session):
        """Test range filter with both min and max."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(10):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_range(query, field="value", min_value=3, max_value=6)
        results = filtered.all()
        
        assert len(results) == 4
        assert all(3 <= r.value <= 6 for r in results)


class TestQueryBuilderFilterByList:
    """Tests for QueryBuilder.filter_by_list method."""
    
    def test_filter_by_list(self, test_session):
        """Test filter by list of values."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(10):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_list(query, field="value", values=[1, 3, 5, 7])
        results = filtered.all()
        
        assert len(results) == 4
        assert {r.value for r in results} == {1, 3, 5, 7}
    
    def test_filter_by_list_empty(self, test_session):
        """Test filter by empty list."""
        Base.metadata.create_all(test_session.bind)
        
        query = test_session.query(SimpleModel)
        
        with pytest.raises(ValueError, match="Values list cannot be empty"):
            QueryBuilder.filter_by_list(query, field="value", values=[])


class TestQueryBuilderCount:
    """Tests for QueryBuilder.count method."""
    
    def test_count(self, test_session):
        """Test count method."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(5):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        count = QueryBuilder.count(query)
        
        assert count == 5
    
    def test_count_with_filter(self, test_session):
        """Test count with filter applied."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(10):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_range(query, field="value", min_value=5)
        count = QueryBuilder.count(filtered)
        
        assert count == 5


class TestQueryBuilderExists:
    """Tests for QueryBuilder.exists method."""
    
    def test_exists_true(self, test_session):
        """Test exists returns True when records exist."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        test_session.add(SimpleModel(name="Test", value=1))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        exists_result = QueryBuilder.exists(query)
        # QueryBuilder.exists should return boolean
        assert exists_result is True
    
    def test_exists_false(self, test_session):
        """Test exists returns False when no records exist."""
        Base.metadata.create_all(test_session.bind)
        
        query = test_session.query(SimpleModel)
        exists = QueryBuilder.exists(query)
        
        assert exists is False
    
    def test_exists_with_filter(self, test_session):
        """Test exists with filter applied."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        for i in range(5):
            test_session.add(SimpleModel(name=f"Item {i}", value=i))
        test_session.commit()
        
        query = test_session.query(SimpleModel)
        filtered = QueryBuilder.filter_by_range(query, field="value", min_value=10)
        exists = QueryBuilder.exists(filtered)
        
        assert exists is False

