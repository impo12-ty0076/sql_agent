"""
Integration tests for SQL query execution
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
from datetime import datetime

from ..services.query_execution_service import QueryExecutionService
from ..models.query import QueryStatus, QueryResult, ResultColumn, QueryResultCreate
from ..models.database import Database

class MockConnector:
    """Mock database connector for testing"""
    
    def __init__(self):
        self.executed_queries = []
        self.cancelled_queries = set()
    
    def is_read_only_query(self, query):
        """Check if query is read-only"""
        query_upper = query.upper().strip()
        return query_upper.startswith("SELECT") or query_upper.startswith("SHOW") or query_upper.startswith("DESCRIBE")
    
    def execute_query(self, db_config, query, timeout=None, max_rows=None):
        """Execute a query"""
        if query in self.cancelled_queries:
            raise asyncio.CancelledError("Query was cancelled")
        
        self.executed_queries.append({
            "db_config": db_config,
            "query": query,
            "timeout": timeout,
            "max_rows": max_rows,
            "timestamp": datetime.utcnow()
        })
        
        # Create mock result
        columns = [
            ResultColumn(name="id", type="int"),
            ResultColumn(name="name", type="varchar"),
            ResultColumn(name="email", type="varchar")
        ]
        
        rows = [
            [1, "User 1", "user1@example.com"],
            [2, "User 2", "user2@example.com"],
            [3, "User 3", "user3@example.com"]
        ]
        
        return QueryResult(
            id=str(uuid.uuid4()),
            query_id="",
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=False,
            created_at=datetime.utcnow()
        )
    
    def cancel_query(self, query_id):
        """Cancel a query"""
        self.cancelled_queries.add(query_id)
        return True

@pytest.fixture
def mock_dependencies():
    """Set up mock dependencies for testing"""
    with patch("sql_agent.backend.services.query_execution_service.get_query_by_id") as mock_get_query, \
         patch("sql_agent.backend.services.query_execution_service.update_query") as mock_update_query, \
         patch("sql_agent.backend.services.query_execution_service.connector_factory") as mock_factory, \
         patch("sql_agent.backend.services.query_execution_service.create_query_result") as mock_create_result, \
         patch("sql_agent.backend.services.query_execution_service.get_query_result_by_id") as mock_get_result:
        
        # Set up mock connector
        mock_connector = MockConnector()
        mock_factory.create_connector.return_value = mock_connector
        mock_factory.get_query_tracker.return_value = MagicMock()
        
        # Set up mock query
        mock_query = MagicMock()
        mock_query.id = str(uuid.uuid4())
        mock_query.user_id = "test_user"
        mock_query.db_id = "db1"
        mock_query.status = QueryStatus.PENDING
        mock_query.natural_language = "Show me all users"
        mock_query.generated_sql = "SELECT * FROM users"
        mock_query.executed_sql = None
        mock_query.start_time = datetime.utcnow()
        mock_query.end_time = None
        mock_query.error = None
        mock_query.result_id = None
        mock_get_query.return_value = mock_query
        
        # Set up mock result creation
        mock_result = MagicMock()
        mock_result.id = str(uuid.uuid4())
        mock_create_result.return_value = mock_result
        mock_get_result.return_value = mock_result
        
        yield {
            "mock_get_query": mock_get_query,
            "mock_update_query": mock_update_query,
            "mock_factory": mock_factory,
            "mock_connector": mock_connector,
            "mock_create_result": mock_create_result,
            "mock_get_result": mock_get_result,
            "mock_query": mock_query,
            "mock_result": mock_result
        }

@pytest.mark.asyncio
async def test_execute_query_success(mock_dependencies):
    """Test successful query execution"""
    # Create service
    service = QueryExecutionService()
    
    # Execute query
    query_id = mock_dependencies["mock_query"].id
    db_id = "db1"
    sql = "SELECT * FROM users"
    user_id = "test_user"
    
    result = await service.execute_query(user_id, db_id, sql, query_id)
    
    # Check result
    assert result["query_id"] == query_id
    assert result["status"] == QueryStatus.EXECUTING.value
    
    # Wait for background task to complete
    await asyncio.sleep(0.1)
    
    # Check that query was updated
    mock_dependencies["mock_update_query"].assert_called()
    
    # Check that query was executed
    assert len(mock_dependencies["mock_connector"].executed_queries) == 1
    executed_query = mock_dependencies["mock_connector"].executed_queries[0]
    assert executed_query["query"] == sql
    assert executed_query["db_config"].id == db_id

@pytest.mark.asyncio
async def test_execute_non_readonly_query(mock_dependencies):
    """Test execution of non-read-only query (should be rejected)"""
    # Create service
    service = QueryExecutionService()
    
    # Mock connector to reject non-read-only query
    mock_dependencies["mock_connector"].is_read_only_query = lambda q: False
    
    # Execute query
    query_id = mock_dependencies["mock_query"].id
    db_id = "db1"
    sql = "DELETE FROM users"
    user_id = "test_user"
    
    result = await service.execute_query(user_id, db_id, sql, query_id)
    
    # Check result
    assert result["query_id"] == query_id
    assert result["status"] == QueryStatus.EXECUTING.value
    
    # Wait for background task to complete
    await asyncio.sleep(0.1)
    
    # Check that query was updated with error
    mock_dependencies["mock_update_query"].assert_called()
    last_call = mock_dependencies["mock_update_query"].call_args_list[-1]
    assert last_call[0][0] == query_id
    assert last_call[0][1].status == QueryStatus.FAILED
    assert "Only read-only queries are allowed" in last_call[0][1].error
    
    # Check that query was not executed
    assert len(mock_dependencies["mock_connector"].executed_queries) == 0

@pytest.mark.asyncio
async def test_cancel_query(mock_dependencies):
    """Test query cancellation"""
    # Create service
    service = QueryExecutionService()
    
    # Execute query
    query_id = mock_dependencies["mock_query"].id
    db_id = "db1"
    sql = "SELECT * FROM users"
    user_id = "test_user"
    
    # Start query execution
    result = await service.execute_query(user_id, db_id, sql, query_id)
    
    # Create a mock task
    mock_task = AsyncMock()
    service._running_tasks[query_id] = mock_task
    
    # Cancel the query
    cancel_result = await service.cancel_query(query_id)
    
    # Check result
    assert cancel_result["query_id"] == query_id
    assert cancel_result["cancelled"] is True
    assert cancel_result["status"] == QueryStatus.CANCELLED.value
    
    # Check that task was cancelled
    mock_task.cancel.assert_called_once()
    
    # Check that query was updated
    mock_dependencies["mock_update_query"].assert_called()
    
@pytest.mark.asyncio
async def test_get_query_status(mock_dependencies):
    """Test getting query status"""
    # Create service
    service = QueryExecutionService()
    
    # Set up mock query with result
    query_id = mock_dependencies["mock_query"].id
    result_id = mock_dependencies["mock_result"].id
    mock_dependencies["mock_query"].status = QueryStatus.COMPLETED
    mock_dependencies["mock_query"].result_id = result_id
    mock_dependencies["mock_query"].end_time = datetime.utcnow()
    
    # Get query status
    status_result = await service.get_query_status(query_id)
    
    # Check result
    assert status_result["query_id"] == query_id
    assert status_result["status"] == QueryStatus.COMPLETED
    assert status_result["result_id"] == result_id
    assert status_result["is_running"] is False

@pytest.mark.asyncio
async def test_get_running_queries(mock_dependencies):
    """Test getting running queries"""
    # Create service
    service = QueryExecutionService()
    
    # Set up mock tasks
    query_id1 = str(uuid.uuid4())
    query_id2 = str(uuid.uuid4())
    
    service._running_tasks[query_id1] = AsyncMock()
    service._running_tasks[query_id2] = AsyncMock()
    
    # Mock get_query_by_id to return different queries
    mock_query1 = MagicMock()
    mock_query1.id = query_id1
    mock_query1.user_id = "test_user"
    mock_query1.db_id = "db1"
    mock_query1.status = QueryStatus.EXECUTING
    
    mock_query2 = MagicMock()
    mock_query2.id = query_id2
    mock_query2.user_id = "other_user"
    mock_query2.db_id = "db2"
    mock_query2.status = QueryStatus.EXECUTING
    
    mock_dependencies["mock_get_query"].side_effect = lambda qid: mock_query1 if qid == query_id1 else mock_query2
    
    # Get running queries for test_user
    running_queries = await service.get_running_queries("test_user")
    
    # Check result
    assert len(running_queries) == 1
    assert running_queries[0]["query_id"] == query_id1
    assert running_queries[0]["user_id"] == "test_user"
    
    # Get all running queries
    all_running_queries = await service.get_running_queries()
    
    # Check result
    assert len(all_running_queries) == 2