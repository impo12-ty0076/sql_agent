import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from sql_agent.backend.main import app
from sql_agent.backend.models.auth import LoginResponse
from sql_agent.backend.models.user import UserResponse, UserPreferences, UserPermissions

client = TestClient(app)

@patch('sql_agent.backend.api.auth.AuthService.login')
def test_login_success(mock_login):
    # Mock successful login
    mock_login.return_value = LoginResponse(
        access_token="test_token",
        token_type="bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        user_id="test_id",
        username="testuser",
        role="user"
    )
    
    # Test login endpoint
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "test_token"
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "test_id"
    assert data["username"] == "testuser"
    assert data["role"] == "user"

@patch('sql_agent.backend.api.auth.AuthService.login')
def test_login_failure(mock_login):
    # Mock failed login
    mock_login.return_value = None
    
    # Test login endpoint
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrong_password"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "잘못된 사용자 이름 또는 비밀번호"

@patch('sql_agent.backend.api.auth.AuthService.logout')
def test_logout_success(mock_logout):
    # Mock successful logout
    mock_logout.return_value = True
    
    # Test logout endpoint
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "성공적으로 로그아웃되었습니다."

@patch('sql_agent.backend.api.auth.AuthService.logout')
def test_logout_failure(mock_logout):
    # Mock failed logout
    mock_logout.return_value = False
    
    # Test logout endpoint
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "로그아웃 처리 중 오류가 발생했습니다."

@patch('sql_agent.backend.core.dependencies.get_current_active_user')
def test_get_current_user_info(mock_get_user):
    # Mock current user
    mock_get_user.return_value = UserResponse(
        id="test_id",
        username="testuser",
        email="test@example.com",
        role="user",
        last_login=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        preferences=UserPreferences(
            default_db=None,
            theme="light",
            results_per_page=50
        ),
        permissions=UserPermissions(
            allowed_databases=[]
        )
    )
    
    # Test get current user endpoint
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_id"
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"