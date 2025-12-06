"""
Integration tests for complex query scenarios (joins, aggregations, subqueries)
"""

import pytest
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy_engine_kit import with_session
from sqlalchemy_engine_kit.models import Base
from tests.fixtures.sample_models import User, Post, Comment

# Repository pattern not available in this version
REPOSITORIES_AVAILABLE = False
BaseRepository = None


class TestJoinQueries:
    """Tests for JOIN query scenarios."""
    
    def test_inner_join(self, test_session):
        """Test inner join between tables."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        post1 = Post(title="Post 1", content="Content 1", user_id=user.id)
        post2 = Post(title="Post 2", content="Content 2", user_id=user.id)
        test_session.add(post1)
        test_session.add(post2)
        test_session.commit()
        
        # Inner join query
        query = test_session.query(User, Post).join(Post, User.id == Post.user_id)
        results = query.all()
        
        assert len(results) == 2
        for user_obj, post_obj in results:
            assert user_obj.id == post_obj.user_id
            assert post_obj.title.startswith("Post")
    
    def test_left_outer_join(self, test_session):
        """Test left outer join."""
        Base.metadata.create_all(test_session.bind)
        
        # Create user without posts
        user1 = User(email="user1@test.com", name="User 1", password_hash="hash")
        # Create user with posts
        user2 = User(email="user2@test.com", name="User 2", password_hash="hash")
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        post = Post(title="Post", content="Content", user_id=user2.id)
        test_session.add(post)
        test_session.commit()
        
        # Left outer join - should include users without posts
        query = test_session.query(User, Post).outerjoin(Post, User.id == Post.user_id)
        results = query.all()
        
        assert len(results) >= 2
        # User1 should have None for Post
        user1_result = [r for r in results if r[0].id == user1.id][0]
        assert user1_result[1] is None  # No post
    
    def test_multiple_joins(self, test_session):
        """Test multiple table joins."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        post = Post(title="Post", content="Content", user_id=user.id)
        test_session.add(post)
        test_session.flush()
        
        comment1 = Comment(content="Comment 1", user_id=user.id, post_id=post.id)
        comment2 = Comment(content="Comment 2", user_id=user.id, post_id=post.id)
        test_session.add(comment1)
        test_session.add(comment2)
        test_session.commit()
        
        # Join User -> Post -> Comment
        query = test_session.query(User, Post, Comment).join(
            Post, User.id == Post.user_id
        ).join(
            Comment, Post.id == Comment.post_id
        )
        results = query.all()
        
        assert len(results) == 2  # Two comments
        for user_obj, post_obj, comment_obj in results:
            assert user_obj.id == post_obj.user_id
            assert post_obj.id == comment_obj.post_id
    
    def test_join_with_filter(self, test_session):
        """Test join with WHERE clause."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user1 = User(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = User(email="user2@test.com", name="User 2", password_hash="hash")
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        post1 = Post(title="Post 1", content="Content", user_id=user1.id)
        post2 = Post(title="Post 2", content="Content", user_id=user2.id)
        test_session.add(post1)
        test_session.add(post2)
        test_session.commit()
        
        # Join with filter
        query = test_session.query(User, Post).join(
            Post, User.id == Post.user_id
        ).filter(User.email == "user1@test.com")
        results = query.all()
        
        assert len(results) == 1
        assert results[0][0].email == "user1@test.com"
        assert results[0][1].user_id == user1.id


class TestAggregationQueries:
    """Tests for aggregation queries (COUNT, SUM, AVG, etc.)."""
    
    def test_count_aggregation(self, test_session):
        """Test COUNT aggregation."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        for i in range(5):
            post = Post(title=f"Post {i}", content="Content", user_id=user.id)
            test_session.add(post)
        test_session.commit()
        
        # Count posts per user
        query = test_session.query(
            User.id,
            User.email,
            func.count(Post.id).label('post_count')
        ).outerjoin(Post, User.id == Post.user_id).group_by(User.id, User.email)
        
        results = query.all()
        assert len(results) == 1
        assert results[0].post_count == 5
    
    def test_sum_aggregation(self, test_session):
        """Test SUM aggregation."""
        Base.metadata.create_all(test_session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data with numeric values
        for i in range(10):
            item = SimpleModel(name=f"Item {i}", value=i)
            test_session.add(item)
        test_session.commit()
        
        # Sum all values
        result = test_session.query(func.sum(SimpleModel.value)).scalar()
        expected_sum = sum(range(10))  # 0+1+2+...+9 = 45
        assert result == expected_sum
    
    def test_avg_aggregation(self, test_session):
        """Test AVG aggregation."""
        Base.metadata.create_all(test_session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data
        for i in range(10):
            item = SimpleModel(name=f"Item {i}", value=i)
            test_session.add(item)
        test_session.commit()
        
        # Average value
        result = test_session.query(func.avg(SimpleModel.value)).scalar()
        expected_avg = sum(range(10)) / 10  # 4.5
        assert abs(result - expected_avg) < 0.01
    
    def test_max_min_aggregation(self, test_session):
        """Test MAX and MIN aggregations."""
        Base.metadata.create_all(test_session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data
        values = [10, 5, 20, 15, 30]
        for i, val in enumerate(values):
            item = SimpleModel(name=f"Item {i}", value=val)
            test_session.add(item)
        test_session.commit()
        
        # Max value
        max_val = test_session.query(func.max(SimpleModel.value)).scalar()
        assert max_val == 30
        
        # Min value
        min_val = test_session.query(func.min(SimpleModel.value)).scalar()
        assert min_val == 5
    
    def test_group_by_with_having(self, test_session):
        """Test GROUP BY with HAVING clause."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user1 = User(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = User(email="user2@test.com", name="User 2", password_hash="hash")
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        # User1 has 3 posts, User2 has 1 post
        for i in range(3):
            post = Post(title=f"Post {i}", content="Content", user_id=user1.id)
            test_session.add(post)
        post = Post(title="Post", content="Content", user_id=user2.id)
        test_session.add(post)
        test_session.commit()
        
        # Group by user, having count > 1
        query = test_session.query(
            User.id,
            func.count(Post.id).label('post_count')
        ).join(Post, User.id == Post.user_id).group_by(User.id).having(
            func.count(Post.id) > 1
        )
        
        results = query.all()
        assert len(results) == 1
        assert results[0].post_count == 3


class TestSubqueryScenarios:
    """Tests for subquery scenarios."""
    
    def test_scalar_subquery(self, test_session):
        """Test scalar subquery."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        for i in range(5):
            post = Post(title=f"Post {i}", content="Content", user_id=user.id)
            test_session.add(post)
        test_session.commit()
        
        # Subquery: count posts for a user
        subquery = test_session.query(func.count(Post.id)).filter(
            Post.user_id == user.id
        ).scalar_subquery()
        
        # Use in main query
        result = test_session.query(User.email, subquery.label('post_count')).filter(
            User.id == user.id
        ).first()
        
        assert result.post_count == 5
    
    def test_exists_subquery(self, test_session):
        """Test EXISTS subquery."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user1 = User(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = User(email="user2@test.com", name="User 2", password_hash="hash")
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        # User1 has posts, User2 doesn't
        post = Post(title="Post", content="Content", user_id=user1.id)
        test_session.add(post)
        test_session.commit()
        
        # Find users who have posts
        subquery = test_session.query(Post).filter(Post.user_id == User.id).exists()
        users_with_posts = test_session.query(User).filter(subquery).all()
        
        assert len(users_with_posts) == 1
        assert users_with_posts[0].id == user1.id
    
    def test_in_subquery(self, test_session):
        """Test IN subquery."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        post1 = Post(title="Post 1", content="Content", user_id=user.id)
        post2 = Post(title="Post 2", content="Content", user_id=user.id)
        test_session.add(post1)
        test_session.add(post2)
        test_session.commit()
        
        # Subquery: get post IDs for user
        subquery = test_session.query(Post.id).filter(Post.user_id == user.id)
        
        # Find comments for those posts
        comment = Comment(content="Comment", user_id=user.id, post_id=post1.id)
        test_session.add(comment)
        test_session.commit()
        
        comments = test_session.query(Comment).filter(
            Comment.post_id.in_(subquery)
        ).all()
        
        assert len(comments) == 1
        assert comments[0].post_id == post1.id
    
    def test_correlated_subquery(self, test_session):
        """Test correlated subquery."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        test_session.add(user)
        test_session.flush()
        
        for i in range(3):
            post = Post(title=f"Post {i}", content="Content", user_id=user.id)
            test_session.add(post)
        test_session.commit()
        
        # Correlated subquery: post count per user
        subquery = test_session.query(func.count(Post.id)).filter(
            Post.user_id == User.id
        ).correlate(User).scalar_subquery()
        
        result = test_session.query(
            User.email,
            subquery.label('post_count')
        ).filter(User.id == user.id).first()
        
        assert result.post_count == 3


class TestComplexQueryCombinations:
    """Tests for combining multiple query features."""
    
    def test_join_with_aggregation_and_filter(self, test_session):
        """Test join with aggregation and filter."""
        Base.metadata.create_all(test_session.bind)
        
        # Create test data
        user1 = User(email="user1@test.com", name="User 1", password_hash="hash")
        user2 = User(email="user2@test.com", name="User 2", password_hash="hash")
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        # User1 has 2 posts, User2 has 1 post
        for i in range(2):
            post = Post(title=f"Post {i}", content="Content", user_id=user1.id)
            test_session.add(post)
        post = Post(title="Post", content="Content", user_id=user2.id)
        test_session.add(post)
        test_session.commit()
        
        # Complex query: join, aggregate, filter, group by
        query = test_session.query(
            User.email,
            func.count(Post.id).label('post_count')
        ).join(Post, User.id == Post.user_id).filter(
            User.email.like('user1%')
        ).group_by(User.email)
        
        results = query.all()
        assert len(results) == 1
        assert results[0].post_count == 2
    
    def test_multiple_conditions_with_or(self, test_session):
        """Test queries with OR conditions."""
        Base.metadata.create_all(test_session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data
        item1 = SimpleModel(name="Item A", value=10)
        item2 = SimpleModel(name="Item B", value=20)
        item3 = SimpleModel(name="Item C", value=30)
        test_session.add(item1)
        test_session.add(item2)
        test_session.add(item3)
        test_session.commit()
        
        # Query with OR condition
        results = test_session.query(SimpleModel).filter(
            or_(
                SimpleModel.value == 10,
                SimpleModel.value == 30
            )
        ).all()
        
        assert len(results) == 2
        values = [r.value for r in results]
        assert 10 in values
        assert 30 in values
        assert 20 not in values
    
    def test_nested_conditions(self, test_session):
        """Test nested AND/OR conditions."""
        Base.metadata.create_all(test_session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data
        for i in range(10):
            item = SimpleModel(name=f"Item {i}", value=i)
            test_session.add(item)
        test_session.commit()
        
        # Complex nested conditions
        results = test_session.query(SimpleModel).filter(
            and_(
                SimpleModel.value >= 2,
                or_(
                    SimpleModel.value <= 4,
                    SimpleModel.value >= 8
                )
            )
        ).all()
        
        # Should get values: 2, 3, 4, 8, 9
        assert len(results) == 5
        values = [r.value for r in results]
        assert all(v in [2, 3, 4, 8, 9] for v in values)


class TestRepositoryWithComplexQueries:
    """Tests for using repositories with complex queries."""
    
    @pytest.mark.skip(reason="Repositories module not available")
    @with_session()
    def test_repository_with_join(self, session: Session):
        """Test repository pattern with join queries."""
        Base.metadata.create_all(session.bind)
        
        # Create test data
        user = User(email="user@test.com", name="Test User", password_hash="hash")
        session.add(user)
        session.flush()
        
        post = Post(title="Post", content="Content", user_id=user.id)
        session.add(post)
        session.commit()
        
        # Direct query (repository pattern not available in this version)
        base_query = session.query(User)
        
        # Add join
        query = base_query.join(Post, User.id == Post.user_id)
        results = query.all()
        
        assert len(results) == 1
        assert results[0].id == user.id
    
    @pytest.mark.skip(reason="Repositories module not available")
    @with_session()
    def test_repository_with_aggregation(self, session: Session):
        """Test repository pattern with aggregation."""
        Base.metadata.create_all(session.bind)
        
        from tests.fixtures.sample_models import SimpleModel
        
        # Create test data
        for i in range(5):
            item = SimpleModel(name=f"Item {i}", value=i * 10)
            session.add(item)
        session.commit()
        
        # Use aggregation with repository model
        result = session.query(func.avg(SimpleModel.value)).scalar()
        expected_avg = sum([0, 10, 20, 30, 40]) / 5  # 20
        assert abs(result - expected_avg) < 0.01

