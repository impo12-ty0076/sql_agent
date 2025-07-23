"""
Unit tests for SQL query execution API
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ..api.query import router as query_router
from ..models.query import QueryStatus, QueryResult, ResultColumn
from ..services.query_execution_service import QueryExecutionService

# Create test app
app = FastAPI()
app.include_router(query_router)

# Mock authentication
@app.middleware("http")
async def mock_auth_middleware(request, call_next):
    request.state.user_id = "test_user"
    response = await call_next(request)
    return response

# Mock get_current_user_id function
async def mock_get_current_user_id(token):
    return "test_user"

# Apply patch for authentication
patch("sql_agent.backend.api.query.get_current_user_id", mock_get_current_user_id).start()

# Test client
client = TestClient(app)

@pytest.fixture
def mock_query_execution_service():
    """Mock QueryExecutionService for testing"""
    with patch("sql_agent.backend.api.query.query_execution_service") as mock_service:
        yield mock_service

@pytest.fixture
def mock_get_query_by_id():
    """Mock get_query_by_id function for testing"""
    with patch("sql_agent.backend.api.query.get_query_by_id") as mock_get:
        yield mock_get

@pytest.mark.asyncio
async def test_execute_query(mock_query_execution_service):
    """Test execute_query endpoint"""
    # Mock data
    query_id = str(uuid.uuid4())
    db_id = "db1"
    sql = "SELECT * FROM users"
    
    # Mock service response
    mock_query_execution_service.execute_query.return_value = {
        "query_id": query_id,
        "status": QueryStatus.EXECUTING.value,
        "start_time": datetime.utcnow().isoformat()
    }
    
    # Make request
    response = client.post(
        "/api/query/execute",
        json={
            "sql": sql,
            "db_id": db_id
        },
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["query_id"] == query_id
    assert response.json()["status"] == QueryStatus.EXECUTING.value
    
    # Check service call
    mock_query_execution_service.execute_query.assert_called_once_with(
        user_id="test_user",
        db_id=db_id,
        sql=sql,
        query_id=None,
        timeout=300,
        max_rows=10000
    )

@pytest.mark.asyncio
async def test_get_query_status(mock_query_execution_service, mock_get_query_by_id):
    """Test get_query_status endpoint"""
    # Mock data
    query_id = str(uuid.uuid4())
    result_id = str(uuid.uuid4())
    
    # Mock query object
    mock_query = MagicMock()
    mock_query.id = query_id
    mock_query.user_id = "test_user"
    mock_get_query_by_id.return_value = mock_query
    
    # Mock service response
    mock_query_execution_service.get_query_status.return_value = {
        "query_id": query_id,
        "status": QueryStatus.COMPLETED.value,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "result_id": result_id,
        "is_running": False
    }
    
    # Make request
    response = client.get(
        f"/api/query/status/{query_id}",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["query_id"] == query_id
    assert response.json()["status"] == QueryStatus.COMPLETED.value
    assert response.json()["result_id"] == result_id
    
    # Check service call
    mock_query_execution_service.get_query_status.assert_called_once_with(query_id)

@pytest.mark.asyncio
async def test_cancel_query(mock_query_execution_service, mock_get_query_by_id):
    """Test cancel_query endpoint"""
    # Mock data
    query_id = str(uuid.uuid4())
    
    # Mock query object
    mock_query = MagicMock()
    mock_query.id = query_id
    mock_query.user_id = "test_user"
    mock_get_query_by_id.return_value = mock_query
    
    # Mock service response
    mock_query_execution_service.cancel_query.return_value = {
        "query_id": query_id,
        "status": QueryStatus.CANCELLED.value,
        "cancelled": True,
        "message": "Query cancelled successfully"
    }
    
    # Make request
    response = client.post(
        f"/api/query/cancel/{query_id}",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check response
    assert response.status_code == 200
    assert response.json()["query_id"] == query_id
    assert response.json()["status"] == QueryStatus.CANCELLED.value
    assert response.json()["cancelled"] is True
    
    # Check service call
    mock_query_execution_service.cancel_query.assert_called_once_with(query_id)

@pytest.mark.asyncio
async def test_get_running_queries(mock_query_execution_service):
    """Test get_running_queries endpoint"""
    # Mock data
    query_id = str(uuid.uuid4())
    
    # Mock service response
    mock_query_execution_service.get_running_queries.return_value = [
        {
            "query_id": query_id,
            "user_id": "test_user",
            "db_id": "db1",
            "status": QueryStatus.EXECUTING.value,
            "start_time": datetime.utcnow().isoformat(),
            "natural_language": "Show me all users",
            "executed_sql": "SELECT * FROM users"
        }
    ]
    
    # Make request
    response = client.get(
        "/api/query/running",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Check response
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["query_id"] == query_id
    assert response.json()[0]["status"] == QueryStatus.EXECUTING.value
    
    # Check service call
    mock_query_execution_service.get_running_queries.assert_called_once_with("test_user")

@pytest.mark.asyncio
async def test_query_execution_service():
    """Test QueryExecutionService functionality"""
    # Create service instance
    service = QueryExecutionService()
    
    # Mock dependencies
    with patch("sql_agent.backend.services.query_execution_service.get_query_by_id") as mock_get_query, \
         patch("sql_agent.backend.services.query_execution_service.update_query") as mock_update_query, \
         patch("sql_agent.backend.services.query_execution_service.connector_factory") as mock_factory, \
         patch("sql_agent.backend.services.query_execution_service.create_query_result") as mock_create_result:
        
        # Mock data
        query_id = str(uuid.uuid4())
        db_id = "db1"
        sql = "SELECT * FROM users"
        user_id = "test_user"
        
        # Mock query object
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.user_id = user_id
        mock_query.status = QueryStatus.EXECUTING
        mock_get_query.return_value = mock_query
        
        # Mock connector
        mock_connector = MagicMock()
        mock_connector.is_read_only_query.return_value = True
        mock_factory.create_connector.return_value = mock_connector
        
        # Test execute_query
        result = await service.execute_query(user_id, db_id, sql)
        
        # Check result
        assert result["status"] == QueryStatus.EXECUTING.value
        
        # Test get_query_status
        mock_get_query.return_value = mock_query
        
        status_result = await service.get_query_status(query_id)
        
        # Check result
        assert status_result["query_id"] == query_id
        assert status_result["status"] == QueryStatus.EXECUTING
        
        # Test cancel_query
        mock_task = AsyncMock()
        service._running_tasks[query_id] = mock_task
        
        cancel_result = await service.cancel_query(query_id)
        
        # Check result
        assert cancel_result["query_id"] == query_id
        assert cancel_result["cancelled"] is True
        
        # Check that task was cancelled
        mock_task.cancel.assert_called_once()