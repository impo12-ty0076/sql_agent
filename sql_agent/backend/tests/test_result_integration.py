"""
Integration tests for the Result API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime
import uuid

from ..main import app
from ..models.query import QueryResult, QueryResultCreate
from ..db.crud.query_result import create_query_result
from ..llm.result_summary_service import ResultSummaryService

# Test client
client = TestClient(app)

# Mock data
mock_query_id = str(uuid.uuid4())
mock_user_id = "test-user-id"
mock_token = "test-token"

# Mock authentication
@pytest.fixture(autouse=True)
def mock_auth():
    with patch("..core.auth.get_current_user_id", new_callable=AsyncMock) as mock:
        mock.return_value = mock_user_id
        yield mock

# Mock create_query_result
@pytest.fixture
def mock_create_result():
    with patch("..db.crud.query_result.create_query_result", new_callable=AsyncMock) as mock:
        async def side_effect(result_data):
            result = QueryResult(
                id=str(uuid.uuid4()),
                query_id=result_data.query_id,
                columns=result_data.columns,
                rows=result_data.rows,
                row_count=result_data.row_count,
                truncated=result_data.truncated,
                total_row_count=result_data.total_row_count,
                summary=result_data.summary,
                created_at=datetime.utcnow()
            )
            return result
        
        mock.side_effect = side_effect
        yield mock

# Mock generate_summary
@pytest.fixture
def mock_generate_summary():
    with patch("..llm.result_summary_service.ResultSummaryService.generate_summary", new_callable=AsyncMock) as mock:
        mock.return_value = "This is a test summary with insights about the data."
        yield mock


class TestResultIntegration:
    """Integration test cases for the Result API endpoints."""
    
    @pytest.mark.asyncio
    async def test_result_workflow(self, mock_create_result, mock_generate_summary):
        """Test the complete result workflow: create, paginate, summarize, report."""
        # 1. Create a test result
        result_data = QueryResultCreate(
            query_id=mock_query_id,
            columns=[
                {"name": "id", "type": "int"},
                {"name": "username", "type": "varchar"},
                {"name": "email", "type": "varchar"},
                {"name": "age", "type": "int"}
            ],
            rows=[
                [1, "user1", "user1@example.com", 25],
                [2, "user2", "user2@example.com", 30],
                [3, "user3", "user3@example.com", 35],
                [4, "user4", "user4@example.com", 40],
                [5, "user5", "user5@example.com", 45]
            ],
            row_count=5,
            truncated=False,
            total_row_count=5
        )
        
        result = await mock_create_result(result_data)
        result_id = result.id
        
        # 2. Get the result
        with patch("..db.crud.query_result.get_query_result_by_id", new_callable=AsyncMock) as mock_get_result:
            mock_get_result.return_value = result
            
            response = client.get(
                f"/api/result/{result_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["result_id"] == result_id
            assert data["query_id"] == mock_query_id
            assert len(data["columns"]) == 4
            assert len(data["rows"]) == 5
            assert data["row_count"] == 5
            assert data["truncated"] is False
        
        # 3. Get paginated result with sorting
        with patch("..db.crud.query_result.get_query_result_by_id", new_callable=AsyncMock) as mock_get_result:
            mock_get_result.return_value = result
            
            response = client.post(
                f"/api/result/{result_id}/paginated",
                headers={"Authorization": f"Bearer {mock_token}"},
                json={
                    "page": 1,
                    "page_size": 3,
                    "sort_column": "age",
                    "sort_direction": "desc"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["result_id"] == result_id
            assert data["page"] == 1
            assert data["page_size"] == 3
            assert len(data["rows"]) == 3
            assert data["rows"][0][3] == 45  # First row should have age 45 (sorted desc)
            assert data["rows"][1][3] == 40  # Second row should have age 40
            assert data["rows"][2][3] == 35  # Third row should have age 35
        
        # 4. Generate summary
        with patch("..db.crud.query_result.get_query_result_by_id", new_callable=AsyncMock) as mock_get_result:
            with patch("..db.crud.query_result.update_query_result_summary", new_callable=AsyncMock) as mock_update_summary:
                mock_get_result.return_value = result
                mock_update_summary.return_value = result
                
                response = client.post(
                    f"/api/result/{result_id}/summary",
                    headers={"Authorization": f"Bearer {mock_token}"},
                    json={
                        "result_id": result_id,
                        "summary_type": "detailed",
                        "include_insights": True
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["result_id"] == result_id
                assert "summary" in data
                assert data["generated_now"] is True
                
                mock_generate_summary.assert_called_once()
        
        # 5. Create report
        with patch("..db.crud.query_result.get_query_result_by_id", new_callable=AsyncMock) as mock_get_result:
            mock_get_result.return_value = result
            
            response = client.post(
                "/api/result/report",
                headers={"Authorization": f"Bearer {mock_token}"},
                json={
                    "result_id": result_id,
                    "title": "Test Integration Report",
                    "description": "Report created during integration testing",
                    "author": "Test Framework",
                    "template_type": "default",
                    "include_summary": True,
                    "include_visualizations": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert "task_id" in data
            
            # 6. Check report status
            task_id = data["task_id"]
            
            # We can't easily test the actual background task execution in an integration test,
            # but we can verify that the task was created and the status endpoint works
            response = client.get(
                f"/api/result/report-status/{task_id}",
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert "status" in data
            assert "progress" in data