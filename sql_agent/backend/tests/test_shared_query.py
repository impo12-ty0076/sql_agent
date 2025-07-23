"""
Unit tests for shared query functionality
"""
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..models.query import SharedQuery
from ..db.crud.shared_query import (
    create_shared_query,
    get_shared_query_by_id,
    get_shared_query_by_token,
    get_shared_queries_by_query_id,
    get_shared_queries_by_user,
    update_shared_query,
    refresh_shared_query_token,
    delete_shared_query
)
from ..services.shared_query_service import SharedQueryService
from ..db.crud.query_history import create_query_history

# Test data
TEST_USER_ID = "test-user-123"
TEST_QUERY_ID = "test-query-456"

@pytest.fixture
async def test_query_history():
    """Create a test query history for testing"""
    history = await create_query_history(
        user_id=TEST_USER_ID,
        query_id=TEST_QUERY_ID,
        favorite=False,
        tags=["test", "example"],
        notes="Test query history item"
    )
    yield history
    # Clean up is handled by test_shared_query fixture

@pytest.fixture
async def test_shared_query(test_query_history):
    """Create a test shared query for testing"""
    shared_query = await create_shared_query(
        query_id=TEST_QUERY_ID,
        shared_by=TEST_USER_ID,
        allowed_users=["test-user-789"],
        expires_in_days=7
    )
    yield shared_query
    # Clean up
    try:
        await delete_shared_query(shared_query.id)
    except:
        pass

class TestSharedQueryCRUD:
    """Test CRUD operations for shared queries"""
    
    async def test_create_shared_query(self, test_query_history):
        """Test creating a shared query"""
        shared_query = await create_shared_query(
            query_id=TEST_QUERY_ID,
            shared_by=TEST_USER_ID,
            allowed_users=["test-user-789"],
            expires_in_days=7
        )
        
        assert shared_query is not None
        assert shared_query.query_id == TEST_QUERY_ID
        assert shared_query.shared_by == TEST_USER_ID
        assert "test-user-789" in shared_query.allowed_users
        assert shared_query.access_token is not None
        assert shared_query.expires_at is not None
        
        # Clean up
        await delete_shared_query(shared_query.id)
    
    async def test_get_shared_query_by_id(self, test_shared_query):
        """Test getting a shared query by ID"""
        shared_query = await get_shared_query_by_id(test_shared_query.id)
        
        assert shared_query is not None
        assert shared_query.id == test_shared_query.id
        assert shared_query.query_id == TEST_QUERY_ID
        assert shared_query.shared_by == TEST_USER_ID
    
    async def test_get_shared_query_by_token(self, test_shared_query):
        """Test getting a shared query by token"""
        shared_query = await get_shared_query_by_token(test_shared_query.access_token)
        
        assert shared_query is not None
        assert shared_query.id == test_shared_query.id
        assert shared_query.query_id == TEST_QUERY_ID
        assert shared_query.access_token == test_shared_query.access_token
    
    async def test_get_shared_queries_by_query_id(self, test_shared_query):
        """Test getting shared queries by query ID"""
        # Create another shared query for the same query
        another_shared_query = await create_shared_query(
            query_id=TEST_QUERY_ID,
            shared_by=TEST_USER_ID,
            allowed_users=[],
            expires_in_days=14
        )
        
        # Get shared queries for the query
        shared_queries = await get_shared_queries_by_query_id(TEST_QUERY_ID)
        
        assert len(shared_queries) >= 2
        assert any(query.id == test_shared_query.id for query in shared_queries)
        assert any(query.id == another_shared_query.id for query in shared_queries)
        
        # Clean up
        await delete_shared_query(another_shared_query.id)
    
    async def test_get_shared_queries_by_user(self, test_shared_query):
        """Test getting shared queries by user ID"""
        # Get shared queries for the user
        shared_queries = await get_shared_queries_by_user(TEST_USER_ID)
        
        assert len(shared_queries) >= 1
        assert any(query.id == test_shared_query.id for query in shared_queries)
    
    async def test_update_shared_query(self, test_shared_query):
        """Test updating a shared query"""
        new_allowed_users = ["test-user-789", "test-user-101"]
        
        updated_query = await update_shared_query(
            shared_id=test_shared_query.id,
            allowed_users=new_allowed_users,
            expires_in_days=30
        )
        
        assert updated_query is not None
        assert updated_query.id == test_shared_query.id
        assert set(updated_query.allowed_users) == set(new_allowed_users)
        assert updated_query.expires_at > test_shared_query.expires_at
    
    async def test_refresh_shared_query_token(self, test_shared_query):
        """Test refreshing a shared query token"""
        old_token = test_shared_query.access_token
        
        updated_query = await refresh_shared_query_token(test_shared_query.id)
        
        assert updated_query is not None
        assert updated_query.id == test_shared_query.id
        assert updated_query.access_token != old_token
    
    async def test_delete_shared_query(self, test_query_history):
        """Test deleting a shared query"""
        # Create a shared query to delete
        shared_query = await create_shared_query(
            query_id=TEST_QUERY_ID,
            shared_by=TEST_USER_ID,
            allowed_users=[],
            expires_in_days=7
        )
        
        # Delete the shared query
        result = await delete_shared_query(shared_query.id)
        assert result is True
        
        # Verify it's deleted
        deleted_query = await get_shared_query_by_id(shared_query.id)
        assert deleted_query is None

class TestSharedQueryService:
    """Test shared query service"""
    
    def setup_method(self):
        """Set up the test environment"""
        self.service = SharedQueryService()
    
    async def test_create_shared_link(self, test_query_history):
        """Test creating a shared link"""
        result = await self.service.create_shared_link(
            user_id=TEST_USER_ID,
            query_id=TEST_QUERY_ID,
            allowed_users=["test-user-789"],
            expires_in_days=7
        )
        
        assert result is not None
        assert result["query_id"] == TEST_QUERY_ID
        assert result["shared_by"] == TEST_USER_ID
        assert "test-user-789" in result["allowed_users"]
        assert result["access_token"] is not None
        assert result["expires_at"] is not None
        
        # Clean up
        await delete_shared_query(result["id"])
    
    async def test_get_shared_link(self, test_shared_query):
        """Test getting a shared link"""
        result = await self.service.get_shared_link(test_shared_query.id)
        
        assert result is not None
        assert result["id"] == test_shared_query.id
        assert result["query_id"] == TEST_QUERY_ID
        assert result["shared_by"] == TEST_USER_ID
    
    async def test_get_shared_query_by_token(self, test_shared_query):
        """Test getting a shared query by token"""
        result = await self.service.get_shared_query_by_token(test_shared_query.access_token)
        
        assert result is not None
        assert result["id"] == test_shared_query.id
        assert result["query_id"] == TEST_QUERY_ID
        assert result["access_token"] == test_shared_query.access_token
    
    async def test_get_user_shared_queries(self, test_shared_query):
        """Test getting user shared queries"""
        results = await self.service.get_user_shared_queries(TEST_USER_ID)
        
        assert len(results) >= 1
        assert any(query["id"] == test_shared_query.id for query in results)
    
    async def test_update_shared_link(self, test_shared_query):
        """Test updating a shared link"""
        new_allowed_users = ["test-user-789", "test-user-101"]
        
        result = await self.service.update_shared_link(
            user_id=TEST_USER_ID,
            shared_id=test_shared_query.id,
            allowed_users=new_allowed_users,
            expires_in_days=30
        )
        
        assert result is not None
        assert result["id"] == test_shared_query.id
        assert set(result["allowed_users"]) == set(new_allowed_users)
    
    async def test_refresh_access_token(self, test_shared_query):
        """Test refreshing an access token"""
        old_token = test_shared_query.access_token
        
        result = await self.service.refresh_access_token(
            user_id=TEST_USER_ID,
            shared_id=test_shared_query.id
        )
        
        assert result is not None
        assert result["id"] == test_shared_query.id
        assert result["access_token"] != old_token
    
    async def test_delete_shared_link(self, test_query_history):
        """Test deleting a shared link"""
        # Create a shared query to delete
        shared_query = await create_shared_query(
            query_id=TEST_QUERY_ID,
            shared_by=TEST_USER_ID,
            allowed_users=[],
            expires_in_days=7
        )
        
        # Delete the shared query
        result = await self.service.delete_shared_link(
            user_id=TEST_USER_ID,
            shared_id=shared_query.id
        )
        
        assert result is True
        
        # Verify it's deleted
        with pytest.raises(ValueError):
            await self.service.get_shared_link(shared_query.id)
    
    async def test_check_access_permission(self, test_shared_query):
        """Test checking access permission"""
        # Convert to dict for testing
        shared_query_dict = test_shared_query.to_dict()
        
        # Owner should have access
        assert await self.service.check_access_permission(TEST_USER_ID, shared_query_dict) is True
        
        # User in allowed_users should have access
        assert await self.service.check_access_permission("test-user-789", shared_query_dict) is True
        
        # User not in allowed_users should not have access
        assert await self.service.check_access_permission("test-user-999", shared_query_dict) is False
        
        # Test with empty allowed_users (public access)
        shared_query_dict["allowed_users"] = []
        assert await self.service.check_access_permission("test-user-999", shared_query_dict) is True
        
        # Test with expired link
        expired_dict = shared_query_dict.copy()
        expired_dict["expires_at"] = (datetime.utcnow() - timedelta(days=1)).isoformat()
        assert await self.service.check_access_permission(TEST_USER_ID, expired_dict) is False