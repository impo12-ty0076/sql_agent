import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from ..main import app
from ..models.query import QueryStatus

client = TestClient(app)

# Mock token for testing
TEST_TOKEN = "test_token"
TEST_USER_ID = "test_user_123"
TEST_DB_ID = "test_db_123"

@pytest.fixture
def mock_auth():
    """Mock authentication to return test user ID"""
    with patch("sql_agent.backend.api.query.get_current_user_id", new_callable=AsyncMock) as mock:
        mock.return_value = TEST_USER_ID
        yield mock

@pytest.fixture
def mock_nl_to_sql():
    """Mock NL to SQL conversion service"""
    with patch("sql_agent.backend.api.query.nl_to_sql_service.convert_nl_to_sql", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sql": "SELECT * FROM users WHERE name LIKE '%John%'",
            "confidence": 0.95,
            "explanation": "This query searches for users with 'John' in their name.",
            "conversation_id": "conv_123"
        }
        yield mock

@pytest.fixture
def mock_db_service():
    """Mock database service"""
    with patch("sql_agent.backend.api.query.db_service.get_database_schema", new_callable=AsyncMock) as mock_schema:
        mock_schema.return_value = {
            "schemas": [
                {
                    "name": "dbo",
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {"name": "id", "type": "int"},
                                {"name": "name", "type": "varchar"}
                            ]
                        }
                    ]
                }
            ]
        }
        
        with patch("sql_agent.backend.api.query.db_service.get_database_by_id", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = {
                "id": TEST_DB_ID,
                "name": "Test DB",
                "type": "mssql"
            }
            
            yield mock_schema, mock_db

@pytest.fixture
def mock_create_query():
    """Mock query creation in database"""
    with patch("sql_agent.backend.api.query.create_query", new_callable=AsyncMock) as mock:
        mock.return_value = MagicMock(
            id="query_123",
            user_id=TEST_USER_ID,
            db_id=TEST_DB_ID,
            natural_language="Find users named John",
            generated_sql="SELECT * FROM users WHERE name LIKE '%John%'",
            status=QueryStatus.PENDING,
            start_time=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        yield mock

@pytest.fixture
def mock_rag_service():
    """Mock RAG service"""
    with patch("sql_agent.backend.api.query.rag_service.generate_response_async", new_callable=AsyncMock) as mock:
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.response = "Users table contains information about system users including their IDs and names."
        
        # Create mock source documents
        mock_doc1 = MagicMock()
        mock_doc1.id = "doc_1"
        mock_doc1.doc_type = "table"
        mock_doc1.metadata = {"table_name": "users", "schema_name": "dbo"}
        
        mock_source1 = MagicMock()
        mock_source1.document = mock_doc1
        mock_source1.score = 0.95
        
        mock_response.sources = [mock_source1]
        
        mock.return_value = mock_response
        yield mock

def test_process_natural_language_query(mock_auth, mock_nl_to_sql, mock_db_service, mock_create_query):
    """Test natural language query processing endpoint"""
    response = client.post(
        "/api/query/natural",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "Find users named John",
            "db_id": TEST_DB_ID,
            "use_rag": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["natural_language"] == "Find users named John"
    assert data["generated_sql"] == "SELECT * FROM users WHERE name LIKE '%John%'"
    assert data["db_id"] == TEST_DB_ID
    assert data["confidence"] == 0.95
    assert data["explanation"] == "This query searches for users with 'John' in their name."
    assert data["conversation_id"] == "conv_123"
    assert data["status"] == "pending"
    assert "created_at" in data

def test_process_rag_query(mock_auth, mock_rag_service):
    """Test RAG query processing endpoint"""
    response = client.post(
        "/api/query/rag",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "What information is in the users table?",
            "db_id": TEST_DB_ID,
            "top_k": 5,
            "include_citations": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["natural_language"] == "What information is in the users table?"
    assert data["db_id"] == TEST_DB_ID
    assert data["response"] == "Users table contains information about system users including their IDs and names."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_type"] == "table"
    assert data["sources"][0]["metadata"]["table_name"] == "users"
    assert "created_at" in data

def test_natural_language_query_with_rag(mock_auth, mock_rag_service):
    """Test natural language query with RAG option enabled"""
    response = client.post(
        "/api/query/natural",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "What information is in the users table?",
            "db_id": TEST_DB_ID,
            "use_rag": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["natural_language"] == "What information is in the users table?"
    assert data["db_id"] == TEST_DB_ID
    assert data["response"] == "Users table contains information about system users including their IDs and names."
    assert len(data["sources"]) == 1
    assert "created_at" in data

def test_modify_sql(mock_auth):
    """Test SQL modification endpoint"""
    with patch("sql_agent.backend.api.query.get_query_by_id", new_callable=AsyncMock) as mock_get_query:
        mock_get_query.return_value = MagicMock(
            id="query_123",
            user_id=TEST_USER_ID,
            db_id=TEST_DB_ID,
            natural_language="Find users named John",
            generated_sql="SELECT * FROM users WHERE name LIKE '%John%'",
            status=QueryStatus.PENDING
        )
        
        with patch("sql_agent.backend.api.query.update_query", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = MagicMock(
                id="query_123",
                user_id=TEST_USER_ID,
                db_id=TEST_DB_ID,
                natural_language="Find users named John",
                generated_sql="SELECT * FROM users WHERE name LIKE '%John%' AND active = 1",
                status=QueryStatus.PENDING
            )
            
            response = client.post(
                "/api/query/modify-sql",
                headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                json={
                    "query_id": "query_123",
                    "sql": "SELECT * FROM users WHERE name LIKE '%John%' AND active = 1"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["query_id"] == "query_123"
            assert data["generated_sql"] == "SELECT * FROM users WHERE name LIKE '%John%' AND active = 1"
            assert "updated_at" in data

def test_db_not_found(mock_auth, mock_db_service):
    """Test error handling when database is not found"""
    mock_schema, _ = mock_db_service
    mock_schema.return_value = None
    
    response = client.post(
        "/api/query/natural",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        json={
            "query": "Find users named John",
            "db_id": "non_existent_db",
            "use_rag": False
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_unauthorized_query_modification(mock_auth):
    """Test unauthorized query modification"""
    with patch("sql_agent.backend.api.query.get_query_by_id", new_callable=AsyncMock) as mock_get_query:
        mock_get_query.return_value = MagicMock(
            id="query_123",
            user_id="different_user",  # Different from TEST_USER_ID
            db_id=TEST_DB_ID,
            natural_language="Find users named John",
            generated_sql="SELECT * FROM users WHERE name LIKE '%John%'",
            status=QueryStatus.PENDING
        )
        
        response = client.post(
            "/api/query/modify-sql",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            json={
                "query_id": "query_123",
                "sql": "SELECT * FROM users WHERE name LIKE '%John%' AND active = 1"
            }
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"]