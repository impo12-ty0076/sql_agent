"""
Unit tests for the Result API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from ..main import app
from ..db.crud.query_result import get_query_result_by_id, update_query_result_summary
from ..llm.result_summary_service import ResultSummaryService
from ..services.report_generation import ReportGenerator, report_storage_service

# Test client
client = TestClient(app)

# Mock data
mock_result_id = "test-result-id"
mock_query_id = "test-query-id"
mock_user_id = "test-user-id"
mock_token = "test-token"

mock_result = MagicMock()
mock_result.id = mock_result_id
mock_result.query_id = mock_query_id
mock_result.columns = [
    {"name": "id", "type": "int"},
    {"name": "username", "type": "varchar"},
    {"name": "email", "type": "varchar"}
]
mock_result.rows = [
    [1, "user1", "user1@example.com"],
    [2, "user2", "user2@example.com"]
]
mock_result.row_count = 2
mock_result.truncated = False
mock_result.total_row_count = 2
mock_result.summary = None
mock_result.created_at = datetime.utcnow()

# Mock authentication
@pytest.fixture(autouse=True)
def mock_auth():
    with patch("..core.auth.get_current_user_id", new_callable=AsyncMock) as mock:
        mock.return_value = mock_user_id
        yield mock

# Mock get_query_result_by_id
@pytest.fixture
def mock_get_result():
    with patch("..db.crud.query_result.get_query_result_by_id", new_callable=AsyncMock) as mock:
        mock.return_value = mock_result
        yield mock

# Mock update_query_result_summary
@pytest.fixture
def mock_update_summary():
    with patch("..db.crud.query_result.update_query_result_summary", new_callable=AsyncMock) as mock:
        mock.return_value = mock_result
        yield mock

# Mock generate_summary
@pytest.fixture
def mock_generate_summary():
    with patch("..llm.result_summary_service.ResultSummaryService.generate_summary", new_callable=AsyncMock) as mock:
        mock.return_value = "This is a test summary."
        yield mock

# Mock save_report
@pytest.fixture
def mock_save_report():
    with patch("..services.report_generation.report_storage_service.save_report") as mock:
        mock.return_value = "test-report-id"
        yield mock

# Mock create_report_from_analysis
@pytest.fixture
def mock_create_report():
    with patch("..services.report_generation.ReportGenerator.create_report_from_analysis") as mock:
        mock_report = MagicMock()
        mock_report.id = "test-report-id"
        mock.return_value = mock_report
        yield mock


class TestResultAPI:
    """Test cases for the Result API endpoints."""
    
    def test_get_result(self, mock_get_result):
        """Test getting a query result."""
        response = client.get(
            f"/api/result/{mock_result_id}",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == mock_result_id
        assert data["query_id"] == mock_query_id
        assert len(data["columns"]) == 3
        assert len(data["rows"]) == 2
        assert data["row_count"] == 2
        assert data["truncated"] is False
        
        mock_get_result.assert_called_once_with(mock_result_id)
    
    def test_get_result_not_found(self, mock_get_result):
        """Test getting a non-existent query result."""
        mock_get_result.return_value = None
        
        response = client.get(
            f"/api/result/{mock_result_id}",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_paginated_result(self, mock_get_result):
        """Test getting a paginated query result."""
        response = client.post(
            f"/api/result/{mock_result_id}/paginated",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "page": 1,
                "page_size": 10,
                "sort_column": "username",
                "sort_direction": "asc"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == mock_result_id
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 1
        assert data["total_rows"] == 2
        assert data["sort_column"] == "username"
        assert data["sort_direction"] == "asc"
        
        mock_get_result.assert_called_once_with(mock_result_id)
    
    def test_generate_result_summary(self, mock_get_result, mock_generate_summary, mock_update_summary):
        """Test generating a result summary."""
        response = client.post(
            f"/api/result/{mock_result_id}/summary",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "result_id": mock_result_id,
                "summary_type": "basic",
                "include_insights": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == mock_result_id
        assert data["summary"] == "This is a test summary."
        assert data["generated_now"] is True
        
        mock_get_result.assert_called_once_with(mock_result_id)
        mock_generate_summary.assert_called_once()
        mock_update_summary.assert_called_once_with(mock_result_id, "This is a test summary.")
    
    def test_generate_result_summary_existing(self, mock_get_result, mock_generate_summary, mock_update_summary):
        """Test generating a result summary when one already exists."""
        # Set an existing summary
        mock_result.summary = "Existing summary"
        
        response = client.post(
            f"/api/result/{mock_result_id}/summary",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "result_id": mock_result_id,
                "summary_type": "basic",
                "include_insights": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == mock_result_id
        assert data["summary"] == "Existing summary"
        assert data["generated_now"] is False
        
        mock_get_result.assert_called_once_with(mock_result_id)
        mock_generate_summary.assert_not_called()
        mock_update_summary.assert_not_called()
        
        # Reset for other tests
        mock_result.summary = None
    
    def test_create_report_from_result(self, mock_get_result):
        """Test creating a report from a query result."""
        response = client.post(
            "/api/result/report",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "result_id": mock_result_id,
                "title": "Test Report",
                "description": "Test Description",
                "author": "Test Author",
                "template_type": "default",
                "include_summary": True,
                "include_visualizations": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "task_id" in data
        assert "message" in data
        
        mock_get_result.assert_called_once_with(mock_result_id)
    
    def test_get_report_generation_status_not_found(self):
        """Test getting a non-existent report generation task status."""
        response = client.get(
            "/api/result/report-status/non-existent-task",
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]