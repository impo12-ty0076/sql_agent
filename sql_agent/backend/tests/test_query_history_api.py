"""
Integration tests for query history API
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import uuid

from ..main import app
from ..db.crud.query_history import create_query_history, delete_query_history
from ..core.auth import create_access_token

# Test client
client = TestClient(app)

# Test data
TEST_USER_ID = "test-user-api-123"
TEST_QUERY_ID = "test-query-api-456"

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    access_token = create_access_token(
        data={"sub": TEST_USER_ID, "role": "user"}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def test_history_item():
    """Create a test history item for testing"""
    history = await create_query_history(
        user_id=TEST_USER_ID,
        query_id=TEST_QUERY_ID,
        favorite=False,
        tags=["test", "api"],
        notes="Test API history item"
    )
    yield history
    # Clean up
    try:
        await delete_query_history(history.id)
    except:
        pass

class TestQueryHistoryAPI:
    """Test query history API endpoints"""
    
    def test_save_query_to_history(self, auth_headers):
        """Test saving a query to history"""
        query_id = f"{TEST_QUERY_ID}-{uuid.uuid4()}"
        
        response = client.post(
            "/api/query-history/save",
            json={
                "query_id": query_id,
                "favorite": True,
                "tags": ["api-test", "save"],
                "notes": "API save test"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == query_id
        assert data["favorite"] is True
        assert set(data["tags"]) == {"api-test", "save"}
        assert data["notes"] == "API save test"
    
    def test_get_query_history(self, auth_headers, test_history_item):
        """Test getting query history"""
        response = client.get(
            "/api/query-history/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["limit"] == 100
        assert data["offset"] == 0
    
    def test_get_query_history_with_filters(self, auth_headers):
        """Test getting query history with filters"""
        # Create a favorite history item
        favorite_query_id = f"{TEST_QUERY_ID}-favorite-{uuid.uuid4()}"
        favorite_response = client.post(
            "/api/query-history/save",
            json={
                "query_id": favorite_query_id,
                "favorite": True,
                "tags": ["favorite", "filter-test"],
                "notes": "Favorite item for filter test"
            },
            headers=auth_headers
        )
        assert favorite_response.status_code == 200
        
        # Test filtering by favorite
        response = client.get(
            "/api/query-history/?favorite_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert all(item["favorite"] for item in data["items"])
        
        # Test filtering by tags
        response = client.get(
            "/api/query-history/?tags=filter-test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert any("filter-test" in item["tags"] for item in data["items"])
    
    def test_update_history_item(self, auth_headers, test_history_item):
        """Test updating a history item"""
        response = client.put(
            f"/api/query-history/{test_history_item.id}",
            json={
                "favorite": True,
                "tags": ["updated", "api-test"],
                "notes": "Updated via API"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_history_item.id
        assert data["favorite"] is True
        assert set(data["tags"]) == {"updated", "api-test"}
        assert data["notes"] == "Updated via API"
    
    def test_delete_history_item(self, auth_headers):
        """Test deleting a history item"""
        # Create a history item to delete
        query_id = f"{TEST_QUERY_ID}-delete-{uuid.uuid4()}"
        create_response = client.post(
            "/api/query-history/save",
            json={
                "query_id": query_id,
                "favorite": False,
                "tags": ["delete-test"],
                "notes": "Item to delete via API"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        history_id = create_response.json()["id"]
        
        # Delete the item
        delete_response = client.delete(
            f"/api/query-history/{history_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "History item deleted successfully"
        
        # Verify it's deleted
        get_response = client.get(
            "/api/query-history/",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert not any(item["id"] == history_id for item in data["items"])
    
    def test_toggle_favorite(self, auth_headers, test_history_item):
        """Test toggling favorite status"""
        response = client.post(
            f"/api/query-history/favorite/{test_history_item.id}?favorite=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_history_item.id
        assert data["favorite"] is True
        
        # Toggle back to false
        response = client.post(
            f"/api/query-history/favorite/{test_history_item.id}?favorite=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_history_item.id
        assert data["favorite"] is False
    
    def test_update_tags(self, auth_headers, test_history_item):
        """Test updating tags"""
        new_tags = ["new-tag-1", "new-tag-2"]
        
        response = client.post(
            f"/api/query-history/tags/{test_history_item.id}",
            json=new_tags,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_history_item.id
        assert set(data["tags"]) == set(new_tags)