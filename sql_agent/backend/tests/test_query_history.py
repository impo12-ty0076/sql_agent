"""
Unit tests for query history functionality
"""
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..models.query import QueryHistory
from ..db.crud.query_history import (
    create_query_history,
    get_query_history_by_id,
    get_query_history_by_user,
    update_query_history,
    delete_query_history
)
from ..services.query_history_service import QueryHistoryService

# Test data
TEST_USER_ID = "test-user-123"
TEST_QUERY_ID = "test-query-456"

@pytest.fixture
async def test_history_item():
    """Create a test history item for testing"""
    history = await create_query_history(
        user_id=TEST_USER_ID,
        query_id=TEST_QUERY_ID,
        favorite=False,
        tags=["test", "example"],
        notes="Test query history item"
    )
    yield history
    # Clean up
    try:
        await delete_query_history(history.id)
    except:
        pass

class TestQueryHistoryCRUD:
    """Test CRUD operations for query history"""
    
    async def test_create_query_history(self):
        """Test creating a query history item"""
        history_id = str(uuid.uuid4())
        tags = ["test", "create"]
        
        history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=TEST_QUERY_ID,
            favorite=True,
            tags=tags,
            notes="Test creation"
        )
        
        assert history is not None
        assert history.user_id == TEST_USER_ID
        assert history.query_id == TEST_QUERY_ID
        assert history.favorite is True
        assert set(history.tags) == set(tags)
        assert history.notes == "Test creation"
        
        # Clean up
        await delete_query_history(history.id)
    
    async def test_get_query_history_by_id(self, test_history_item):
        """Test getting a query history item by ID"""
        history = await get_query_history_by_id(test_history_item.id)
        
        assert history is not None
        assert history.id == test_history_item.id
        assert history.user_id == TEST_USER_ID
        assert history.query_id == TEST_QUERY_ID
    
    async def test_get_query_history_by_user(self, test_history_item):
        """Test getting query history items by user ID"""
        # Create another history item for the same user
        another_history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-2",
            favorite=True,
            tags=["another"],
            notes="Another test item"
        )
        
        # Get history items for the user
        history_items = await get_query_history_by_user(TEST_USER_ID)
        
        assert len(history_items) >= 2
        assert any(item.id == test_history_item.id for item in history_items)
        assert any(item.id == another_history.id for item in history_items)
        
        # Clean up
        await delete_query_history(another_history.id)
    
    async def test_update_query_history(self, test_history_item):
        """Test updating a query history item"""
        new_tags = ["updated", "test"]
        new_notes = "Updated notes"
        
        updated_history = await update_query_history(
            history_id=test_history_item.id,
            favorite=True,
            tags=new_tags,
            notes=new_notes
        )
        
        assert updated_history is not None
        assert updated_history.id == test_history_item.id
        assert updated_history.favorite is True
        assert set(updated_history.tags) == set(new_tags)
        assert updated_history.notes == new_notes
    
    async def test_delete_query_history(self):
        """Test deleting a query history item"""
        # Create a history item to delete
        history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-delete",
            favorite=False,
            tags=["delete"],
            notes="Item to delete"
        )
        
        # Delete the item
        result = await delete_query_history(history.id)
        assert result is True
        
        # Verify it's deleted
        deleted_history = await get_query_history_by_id(history.id)
        assert deleted_history is None

class TestQueryHistoryService:
    """Test query history service"""
    
    def setup_method(self):
        """Set up the test environment"""
        self.service = QueryHistoryService()
    
    async def test_save_query_to_history(self):
        """Test saving a query to history"""
        result = await self.service.save_query_to_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-service",
            favorite=True,
            tags=["service", "test"],
            notes="Service test"
        )
        
        assert result is not None
        assert result["user_id"] == TEST_USER_ID
        assert result["query_id"] == f"{TEST_QUERY_ID}-service"
        assert result["favorite"] is True
        assert set(result["tags"]) == {"service", "test"}
        assert result["notes"] == "Service test"
        
        # Clean up
        await delete_query_history(result["id"])
    
    async def test_get_query_history(self, test_history_item):
        """Test getting query history"""
        # Create additional history items with different attributes
        favorite_history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-favorite",
            favorite=True,
            tags=["favorite", "test"],
            notes="Favorite item"
        )
        
        tagged_history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-tagged",
            favorite=False,
            tags=["special", "test"],
            notes="Tagged item"
        )
        
        # Test getting all history items
        all_history = await self.service.get_query_history(
            user_id=TEST_USER_ID
        )
        assert len(all_history) >= 3
        
        # Test getting favorite items only
        favorite_items = await self.service.get_query_history(
            user_id=TEST_USER_ID,
            favorite_only=True
        )
        assert len(favorite_items) >= 1
        assert all(item["favorite"] for item in favorite_items)
        
        # Test filtering by tags
        tagged_items = await self.service.get_query_history(
            user_id=TEST_USER_ID,
            tags=["special"]
        )
        assert len(tagged_items) >= 1
        assert any("special" in item["tags"] for item in tagged_items)
        
        # Clean up
        await delete_query_history(favorite_history.id)
        await delete_query_history(tagged_history.id)
    
    async def test_update_history_item(self, test_history_item):
        """Test updating a history item"""
        result = await self.service.update_history_item(
            user_id=TEST_USER_ID,
            history_id=test_history_item.id,
            favorite=True,
            tags=["updated", "service"],
            notes="Updated by service"
        )
        
        assert result is not None
        assert result["id"] == test_history_item.id
        assert result["favorite"] is True
        assert set(result["tags"]) == {"updated", "service"}
        assert result["notes"] == "Updated by service"
    
    async def test_delete_history_item(self):
        """Test deleting a history item"""
        # Create a history item to delete
        history = await create_query_history(
            user_id=TEST_USER_ID,
            query_id=f"{TEST_QUERY_ID}-service-delete",
            favorite=False,
            tags=["delete", "service"],
            notes="Service delete test"
        )
        
        # Delete the item
        result = await self.service.delete_history_item(
            user_id=TEST_USER_ID,
            history_id=history.id
        )
        
        assert result is True
        
        # Verify it's deleted
        deleted_history = await get_query_history_by_id(history.id)
        assert deleted_history is None