"""
Integration tests for shared query API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from ..main import app
from ..services.shared_query_service import SharedQueryService
from ..core.auth import get_current_user_id

# Test client
client = TestClient(app)

# Mock data
TEST_USER_ID = "test-user-123"
TEST_QUERY_ID = "test-query-456"
TEST_SHARED_ID = "test-shared-789"
TEST_ACCESS_TOKEN = "test-access-token-123"

# Mock authentication
@pytest.fixture
def mock_auth():
    """Mock authentication for API tests"""
    with patch("fastapi.security.oauth2.OAuth2PasswordBearer.__call__") as mock_oauth:
        mock_oauth.return_value = "test-token"
        with patch("sql_agent.backend.core.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = TEST_USER_ID
            yield

# Mock shared query service
@pytest.fixture
def mock_shared_query_service():
    """Mock shared query service for API tests"""
    with patch.object(SharedQueryService, "create_shared_link") as mock_create, \
         patch.object(SharedQueryService, "get_shared_link") as mock_get, \
         patch.object(SharedQueryService, "get_shared_query_by_token") as mock_get_by_token, \
         patch.object(SharedQueryService, "get_user_shared_queries") as mock_list, \
         patch.object(SharedQueryService, "update_shared_link") as mock_update, \
         patch.object(SharedQueryService, "refresh_access_token") as mock_refresh, \
         patch.object(SharedQueryService, "delete_shared_link") as mock_delete, \
         patch.object(SharedQueryService, "check_access_permission") as mock_check_access:
        
        # Setup mock return values
        expires_at = datetime.utcnow() + timedelta(days=7)
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        shared_query = {
            "id": TEST_SHARED_ID,
            "query_id": TEST_QUERY_ID,
            "shared_by": TEST_USER_ID,
            "access_token": TEST_ACCESS_TOKEN,
            "expires_at": expires_at.isoformat(),
            "allowed_users": ["test-user-789"],
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat()
        }
        
        mock_create.return_value = shared_query
        mock_get.return_value = shared_query
        mock_get_by_token.return_value = shared_query
        mock_list.return_value = [shared_query]
        mock_update.return_value = shared_query
        mock_refresh.return_value = {**shared_query, "access_token": "new-token-123"}
        mock_delete.return_value = True
        mock_check_access.return_value = True
        
        yield {
            "create": mock_create,
            "get": mock_get,
            "get_by_token": mock_get_by_token,
            "list": mock_list,
            "update": mock_update,
            "refresh": mock_refresh,
            "delete": mock_delete,
            "check_access": mock_check_access,
            "shared_query": shared_query
        }

class TestSharedQueryAPI:
    """Test shared query API endpoints"""
    
    def test_create_shared_link(self, mock_auth, mock_shared_query_service):
        """Test creating a shared link"""
        response = client.post(
            "/api/shared-query/create",
            json={
                "query_id": TEST_QUERY_ID,
                "allowed_users": ["test-user-789"],
                "expires_in_days": 7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_SHARED_ID
        assert data["query_id"] == TEST_QUERY_ID
        assert data["shared_by"] == TEST_USER_ID
        assert data["access_token"] == TEST_ACCESS_TOKEN
        
        # Verify service call
        mock_shared_query_service["create"].assert_called_once_with(
            user_id=TEST_USER_ID,
            query_id=TEST_QUERY_ID,
            allowed_users=["test-user-789"],
            expires_in_days=7
        )
    
    def test_get_user_shared_queries(self, mock_auth, mock_shared_query_service):
        """Test getting user shared queries"""
        response = client.get("/api/shared-query/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == TEST_SHARED_ID
        
        # Verify service call
        mock_shared_query_service["list"].assert_called_once_with(
            user_id=TEST_USER_ID,
            include_expired=False
        )
    
    def test_get_shared_link(self, mock_auth, mock_shared_query_service):
        """Test getting a shared link"""
        response = client.get(f"/api/shared-query/{TEST_SHARED_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_SHARED_ID
        assert data["query_id"] == TEST_QUERY_ID
        
        # Verify service calls
        mock_shared_query_service["get"].assert_called_once_with(TEST_SHARED_ID)
        mock_shared_query_service["check_access"].assert_called_once_with(
            TEST_USER_ID,
            mock_shared_query_service["shared_query"]
        )
    
    def test_update_shared_link(self, mock_auth, mock_shared_query_service):
        """Test updating a shared link"""
        response = client.put(
            f"/api/shared-query/{TEST_SHARED_ID}",
            json={
                "allowed_users": ["test-user-789", "test-user-101"],
                "expires_in_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_SHARED_ID
        
        # Verify service call
        mock_shared_query_service["update"].assert_called_once_with(
            user_id=TEST_USER_ID,
            shared_id=TEST_SHARED_ID,
            allowed_users=["test-user-789", "test-user-101"],
            expires_in_days=30
        )
    
    def test_refresh_access_token(self, mock_auth, mock_shared_query_service):
        """Test refreshing an access token"""
        response = client.post(f"/api/shared-query/{TEST_SHARED_ID}/refresh-token")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_SHARED_ID
        assert data["access_token"] == "new-token-123"
        
        # Verify service call
        mock_shared_query_service["refresh"].assert_called_once_with(
            user_id=TEST_USER_ID,
            shared_id=TEST_SHARED_ID
        )
    
    def test_delete_shared_link(self, mock_auth, mock_shared_query_service):
        """Test deleting a shared link"""
        response = client.delete(f"/api/shared-query/{TEST_SHARED_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Shared link deleted successfully"
        
        # Verify service call
        mock_shared_query_service["delete"].assert_called_once_with(
            user_id=TEST_USER_ID,
            shared_id=TEST_SHARED_ID
        )
    
    def test_access_shared_query(self, mock_auth, mock_shared_query_service):
        """Test accessing a shared query"""
        # Mock query execution service
        with patch("sql_agent.backend.services.query_execution_service.QueryExecutionService.get_query_by_id") as mock_get_query, \
             patch("sql_agent.backend.services.query_execution_service.QueryExecutionService.get_query_result") as mock_get_result:
            
            # Setup mock return values
            mock_get_query.return_value = {
                "id": TEST_QUERY_ID,
                "user_id": TEST_USER_ID,
                "natural_language": "Show me sales data",
                "generated_sql": "SELECT * FROM sales",
                "status": "completed",
                "result_id": "test-result-123"
            }
            
            mock_get_result.return_value = {
                "id": "test-result-123",
                "query_id": TEST_QUERY_ID,
                "columns": [{"name": "id", "type": "int"}, {"name": "value", "type": "float"}],
                "rows": [[1, 100.0], [2, 200.0]],
                "row_count": 2
            }
            
            response = client.get(f"/api/shared-query/access/{TEST_ACCESS_TOKEN}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["shared_info"]["id"] == TEST_SHARED_ID
            assert data["query"]["id"] == TEST_QUERY_ID
            assert data["query"]["result"]["row_count"] == 2
            
            # Verify service calls
            mock_shared_query_service["get_by_token"].assert_called_once_with(TEST_ACCESS_TOKEN)
            mock_shared_query_service["check_access"].assert_called_once_with(
                TEST_USER_ID,
                mock_shared_query_service["shared_query"]
            )
            mock_get_query.assert_called_once_with(TEST_QUERY_ID)
            mock_get_result.assert_called_once_with("test-result-123")