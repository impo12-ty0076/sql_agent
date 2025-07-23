"""
Unit tests for admin dashboard API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

from ..main import app
from ..models.system import (
    SystemStatsResponse,
    PaginatedSystemLogs,
    SystemLogResponse,
    UserActivityStatsResponse,
    UserActivityStats,
    LogLevel,
    LogCategory
)
from ..services.system_monitoring_service import SystemMonitoringService


# Mock authentication for tests
@pytest.fixture
def mock_auth():
    with patch("sql_agent.backend.core.dependencies.get_current_admin_user") as mock:
        # Create a mock admin user
        mock_user = MagicMock()
        mock_user.id = str(uuid.uuid4())
        mock_user.username = "admin"
        mock_user.email = "admin@example.com"
        mock_user.role = "admin"
        
        mock.return_value = mock_user
        yield mock


@pytest.fixture
def client():
    return TestClient(app)


def test_get_system_stats(client, mock_auth):
    """Test getting system statistics"""
    # Mock the system monitoring service
    mock_stats = SystemStatsResponse(
        status="operational",
        user_count=10,
        active_users_24h=5,
        query_count_total=100,
        query_count_24h=20,
        avg_query_time_ms=150.5,
        error_count_24h=3,
        active_connections=2,
        system_uptime_seconds=3600,
        cpu_usage_percent=25.5,
        memory_usage_percent=40.2,
        storage_usage_percent=60.0
    )
    
    with patch.object(SystemMonitoringService, "get_system_stats", return_value=mock_stats):
        response = client.get("/api/admin/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "operational"
        assert data["user_count"] == 10
        assert data["active_users_24h"] == 5
        assert data["query_count_total"] == 100
        assert data["query_count_24h"] == 20
        assert data["avg_query_time_ms"] == 150.5
        assert data["error_count_24h"] == 3
        assert data["active_connections"] == 2
        assert data["system_uptime_seconds"] == 3600
        assert data["cpu_usage_percent"] == 25.5
        assert data["memory_usage_percent"] == 40.2
        assert data["storage_usage_percent"] == 60.0


def test_get_system_logs(client, mock_auth):
    """Test getting system logs"""
    # Create mock logs
    now = datetime.utcnow()
    mock_logs = [
        SystemLogResponse(
            id=str(uuid.uuid4()),
            timestamp=now - timedelta(minutes=i),
            level=LogLevel.INFO if i % 3 != 0 else LogLevel.ERROR,
            category=LogCategory.SYSTEM if i % 2 == 0 else LogCategory.AUTH,
            message=f"Test log message {i}",
            user_id=str(uuid.uuid4()) if i % 2 == 0 else None,
            details={"key": f"value{i}"} if i % 2 == 0 else None
        )
        for i in range(1, 6)
    ]
    
    mock_paginated_logs = PaginatedSystemLogs(
        logs=mock_logs,
        total=20,
        page=1,
        page_size=5,
        total_pages=4
    )
    
    with patch.object(SystemMonitoringService, "get_paginated_logs", return_value=mock_paginated_logs):
        response = client.get("/api/admin/logs?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 20
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 4
        assert len(data["logs"]) == 5
        
        # Check first log
        log = data["logs"][0]
        assert "id" in log
        assert "timestamp" in log
        assert "level" in log
        assert "category" in log
        assert "message" in log


def test_get_user_activity(client, mock_auth):
    """Test getting user activity statistics"""
    # Create mock user activity stats
    mock_user_stats = [
        UserActivityStats(
            user_id=str(uuid.uuid4()),
            username=f"user{i}",
            email=f"user{i}@example.com",
            query_count=i * 10,
            last_active=datetime.utcnow() - timedelta(hours=i),
            avg_query_time_ms=i * 50.5,
            error_count=i
        )
        for i in range(1, 6)
    ]
    
    mock_user_activity = UserActivityStatsResponse(
        users=mock_user_stats,
        total=20
    )
    
    with patch.object(SystemMonitoringService, "get_user_activity_stats", return_value=mock_user_activity):
        response = client.get("/api/admin/user-activity?days=7&limit=5&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 20
        assert len(data["users"]) == 5
        
        # Check first user
        user = data["users"][0]
        assert "user_id" in user
        assert "username" in user
        assert "email" in user
        assert "query_count" in user
        assert "last_active" in user
        assert "avg_query_time_ms" in user
        assert "error_count" in user


def test_create_system_log(client, mock_auth):
    """Test creating a system log event"""
    with patch.object(SystemMonitoringService, "log_system_event") as mock_log:
        response = client.post(
            "/api/admin/log-event",
            params={
                "level": "info",
                "category": "system",
                "message": "Test log message"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["message"] == "로그 이벤트가 생성되었습니다."
        
        # Verify the service method was called
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert kwargs["level"] == LogLevel.INFO
        assert kwargs["category"] == LogCategory.SYSTEM
        assert kwargs["message"] == "Test log message"