import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from sql_agent.backend.services.auth import AuthService
from sql_agent.backend.models.auth import LoginRequest
from sql_agent.backend.db.models.user import User, UserSession

def test_verify_password():
    # Create a password hash
    password = "test_password"
    hashed_password = AuthService.get_password_hash(password)
    
    # Verify correct password
    assert AuthService.verify_password(password, hashed_password) is True
    
    # Verify incorrect password
    assert AuthService.verify_password("wrong_password", hashed_password) is False

def test_authenticate_user():
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Create a test user
    user = User(
        id="test_id",
        username="testuser",
        email="test@example.com",
        password_hash=AuthService.get_password_hash("test_password"),
        role="user",
        is_active=True
    )
    
    # Mock database query
    db.query.return_value.filter.return_value.first.return_value = user
    
    # Test successful authentication
    authenticated_user = AuthService.authenticate_user(db, "testuser", "test_password")
    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"
    
    # Test failed authentication with wrong password
    db.query.return_value.filter.return_value.first.return_value = user
    authenticated_user = AuthService.authenticate_user(db, "testuser", "wrong_password")
    assert authenticated_user is None
    
    # Test failed authentication with non-existent user
    db.query.return_value.filter.return_value.first.return_value = None
    authenticated_user = AuthService.authenticate_user(db, "nonexistent", "test_password")
    assert authenticated_user is None

def test_create_access_token():
    # Test token creation with default expiry
    token_data = {"sub": "testuser", "role": "user"}
    token = AuthService.create_access_token(token_data)
    assert token is not None
    assert isinstance(token, str)
    
    # Test token creation with custom expiry
    expires_delta = timedelta(minutes=30)
    token = AuthService.create_access_token(token_data, expires_delta)
    assert token is not None
    assert isinstance(token, str)

def test_create_user_session():
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Create a test user
    user = User(
        id="test_id",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user",
        is_active=True
    )
    
    # Test session creation
    token = "test_token"
    ip_address = "127.0.0.1"
    user_agent = "Test User Agent"
    
    session = AuthService.create_user_session(db, user, token, ip_address, user_agent)
    
    # Verify session was added to database
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    
    # Verify session properties
    assert session.user_id == user.id
    assert session.token == token
    assert session.ip_address == ip_address
    assert session.user_agent == user_agent
    assert session.is_active is True

def test_invalidate_session():
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Create a test session
    session = UserSession(
        id="test_session_id",
        user_id="test_user_id",
        token="test_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_active=True
    )
    
    # Mock database query
    db.query.return_value.filter.return_value.first.return_value = session
    
    # Test successful session invalidation
    result = AuthService.invalidate_session(db, "test_token")
    assert result is True
    assert session.is_active is False
    db.commit.assert_called_once()
    
    # Test failed session invalidation
    db.reset_mock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = AuthService.invalidate_session(db, "nonexistent_token")
    assert result is False
    db.commit.assert_not_called()

@patch('sql_agent.backend.services.auth.jwt.decode')
def test_get_user_from_token(mock_jwt_decode):
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Mock JWT decode
    mock_jwt_decode.return_value = {"sub": "testuser", "role": "user"}
    
    # Create a test user
    user = User(
        id="test_id",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user",
        is_active=True
    )
    
    # Create a test session
    session = UserSession(
        id="test_session_id",
        user_id=user.id,
        token="test_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        is_active=True
    )
    
    # Mock database queries
    db.query.return_value.filter.return_value.first.side_effect = [session, user]
    
    # Test successful user retrieval
    retrieved_user = AuthService.get_user_from_token(db, "test_token")
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username
    
    # Test session update
    assert session.last_activity is not None
    db.commit.assert_called_once()
    
    # Test failed user retrieval with invalid token
    db.reset_mock()
    db.query.return_value.filter.return_value.first.return_value = None
    retrieved_user = AuthService.get_user_from_token(db, "invalid_token")
    assert retrieved_user is None
    
    # Test failed user retrieval with expired session
    db.reset_mock()
    session.expires_at = datetime.utcnow() - timedelta(hours=1)
    db.query.return_value.filter.return_value.first.return_value = session
    retrieved_user = AuthService.get_user_from_token(db, "expired_token")
    assert retrieved_user is None

@patch('sql_agent.backend.services.auth.AuthService.authenticate_user')
@patch('sql_agent.backend.services.auth.AuthService.create_access_token')
@patch('sql_agent.backend.services.auth.AuthService.create_user_session')
def test_login(mock_create_session, mock_create_token, mock_authenticate):
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Create a test user
    user = User(
        id="test_id",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user",
        is_active=True
    )
    
    # Mock authentication
    mock_authenticate.return_value = user
    
    # Mock token creation
    mock_create_token.return_value = "test_token"
    
    # Test successful login
    login_data = LoginRequest(username="testuser", password="test_password")
    login_response = AuthService.login(db, login_data, "127.0.0.1", "Test User Agent")
    
    assert login_response is not None
    assert login_response.access_token == "test_token"
    assert login_response.user_id == user.id
    assert login_response.username == user.username
    assert login_response.role == user.role
    
    # Verify user last_login was updated
    assert user.last_login is not None
    db.commit.assert_called_once()
    
    # Test failed login
    db.reset_mock()
    mock_authenticate.return_value = None
    login_response = AuthService.login(db, login_data, "127.0.0.1", "Test User Agent")
    assert login_response is None
    db.commit.assert_not_called()

@patch('sql_agent.backend.services.auth.AuthService.invalidate_session')
def test_logout(mock_invalidate_session):
    # Mock database session
    db = MagicMock(spec=Session)
    
    # Test successful logout
    mock_invalidate_session.return_value = True
    result = AuthService.logout(db, "test_token")
    assert result is True
    mock_invalidate_session.assert_called_once_with(db, "test_token")
    
    # Test failed logout
    mock_invalidate_session.reset_mock()
    mock_invalidate_session.return_value = False
    result = AuthService.logout(db, "invalid_token")
    assert result is False
    mock_invalidate_session.assert_called_once_with(db, "invalid_token")