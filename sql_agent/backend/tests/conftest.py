import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient

from ..main import app
from ..core.config import settings
from ..models.user import User

# Test client
@pytest.fixture
def client():
    return TestClient(app)

# Mock user for authentication
@pytest.fixture
def test_user():
    return User(
        id="test_user_id",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )

# Generate a test authentication token
@pytest.fixture
def auth_token():
    # Create a token with an expiration time
    expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Create the JWT payload
    to_encode = {
        "sub": "test_user_id",
        "exp": expire,
        "username": "testuser",
        "email": "test@example.com"
    }
    
    # Create the JWT token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt