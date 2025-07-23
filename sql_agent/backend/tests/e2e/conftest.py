"""
Fixtures and configuration for end-to-end tests.
"""
import os
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.main import app
from backend.db.session import Base, get_db
from backend.core.config import settings
from backend.models.user_models import User, UserPermission
from backend.models.database_models import Database, DatabaseSchema
from backend.core.security import get_password_hash

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test user credentials
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "role": "user"
}

TEST_ADMIN = {
    "username": "testadmin",
    "email": "admin@example.com",
    "password": "adminpassword123",
    "role": "admin"
}

# Test database connection
TEST_DB_CONNECTION = {
    "name": "Test DB",
    "type": "mssql",
    "host": "localhost",
    "port": 1433,
    "username": "sa",
    "password": "YourStrong@Passw0rd",
    "database": "TestDB"
}


def override_get_db():
    """Override the database dependency to use the test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create test database tables and seed with test data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    # Create test user
    hashed_password = get_password_hash(TEST_USER["password"])
    user = User(
        username=TEST_USER["username"],
        email=TEST_USER["email"],
        hashed_password=hashed_password,
        role=TEST_USER["role"],
        is_active=True
    )
    db.add(user)
    
    # Create test admin
    hashed_admin_password = get_password_hash(TEST_ADMIN["password"])
    admin = User(
        username=TEST_ADMIN["username"],
        email=TEST_ADMIN["email"],
        hashed_password=hashed_admin_password,
        role=TEST_ADMIN["role"],
        is_active=True
    )
    db.add(admin)
    
    # Create test database connection
    test_db = Database(
        name=TEST_DB_CONNECTION["name"],
        type=TEST_DB_CONNECTION["type"],
        host=TEST_DB_CONNECTION["host"],
        port=TEST_DB_CONNECTION["port"],
        username=TEST_DB_CONNECTION["username"],
        password_encrypted=TEST_DB_CONNECTION["password"],  # In a real app, this would be encrypted
        database=TEST_DB_CONNECTION["database"]
    )
    db.add(test_db)
    db.commit()
    
    # Add permissions for the test user
    user_permission = UserPermission(
        user_id=user.id,
        database_id=test_db.id,
        can_query=True,
        can_view_schema=True
    )
    db.add(user_permission)
    
    # Add permissions for the admin
    admin_permission = UserPermission(
        user_id=admin.id,
        database_id=test_db.id,
        can_query=True,
        can_view_schema=True,
        can_manage=True
    )
    db.add(admin_permission)
    
    # Add test schema
    test_schema = DatabaseSchema(
        database_id=test_db.id,
        schema_data={
            "schemas": [
                {
                    "name": "dbo",
                    "tables": [
                        {
                            "name": "employees",
                            "columns": [
                                {"name": "employee_id", "type": "INT", "nullable": False},
                                {"name": "first_name", "type": "VARCHAR(50)", "nullable": False},
                                {"name": "last_name", "type": "VARCHAR(50)", "nullable": False},
                                {"name": "email", "type": "VARCHAR(100)", "nullable": True},
                                {"name": "hire_date", "type": "DATE", "nullable": False},
                                {"name": "department_id", "type": "INT", "nullable": True}
                            ],
                            "primaryKey": ["employee_id"],
                            "foreignKeys": [
                                {
                                    "columns": ["department_id"],
                                    "referenceTable": "departments",
                                    "referenceColumns": ["department_id"]
                                }
                            ]
                        },
                        {
                            "name": "departments",
                            "columns": [
                                {"name": "department_id", "type": "INT", "nullable": False},
                                {"name": "department_name", "type": "VARCHAR(100)", "nullable": False},
                                {"name": "location_id", "type": "INT", "nullable": True}
                            ],
                            "primaryKey": ["department_id"],
                            "foreignKeys": []
                        }
                    ]
                }
            ]
        }
    )
    db.add(test_schema)
    db.commit()
    
    yield db
    
    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI app."""
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Reset the dependency override
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def auth_headers(client):
    """Get authentication headers for the test user."""
    response = client.post(
        "/api/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client):
    """Get authentication headers for the admin user."""
    response = client.post(
        "/api/auth/login",
        data={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}