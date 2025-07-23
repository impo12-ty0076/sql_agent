"""
End-to-end tests for authentication and database connection.
"""
import pytest
from fastapi.testclient import TestClient


def test_login_and_db_connection_flow(client):
    """
    Test the complete user flow from login to database connection.
    
    This test verifies:
    1. User can successfully log in
    2. User can view available databases
    3. User can connect to a database
    4. User can view database schema
    """
    # Step 1: User login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Set up auth headers for subsequent requests
    auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Step 2: Get available databases
    db_list_response = client.get("/api/db/list", headers=auth_headers)
    assert db_list_response.status_code == 200
    db_list = db_list_response.json()
    assert isinstance(db_list, list)
    assert len(db_list) > 0
    test_db = db_list[0]
    
    # Step 3: Connect to database
    connect_response = client.post(
        f"/api/db/connect/{test_db['id']}",
        headers=auth_headers
    )
    assert connect_response.status_code == 200
    connect_data = connect_response.json()
    assert connect_data["status"] == "connected"
    assert connect_data["database_id"] == test_db["id"]
    
    # Step 4: Get database schema
    schema_response = client.get(
        f"/api/db/schema/{test_db['id']}",
        headers=auth_headers
    )
    assert schema_response.status_code == 200
    schema_data = schema_response.json()
    assert "schemas" in schema_data
    assert len(schema_data["schemas"]) > 0
    
    # Verify schema structure
    first_schema = schema_data["schemas"][0]
    assert "name" in first_schema
    assert "tables" in first_schema
    assert len(first_schema["tables"]) > 0
    
    # Verify tables structure
    first_table = first_schema["tables"][0]
    assert "name" in first_table
    assert "columns" in first_table
    assert len(first_table["columns"]) > 0


def test_failed_login_attempt(client):
    """
    Test failed login attempt with incorrect credentials.
    """
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert login_response.status_code == 401
    error_data = login_response.json()
    assert "detail" in error_data


def test_unauthorized_access(client):
    """
    Test unauthorized access to protected endpoints.
    """
    # Try to access database list without authentication
    db_list_response = client.get("/api/db/list")
    assert db_list_response.status_code == 401
    
    # Try to access database schema without authentication
    schema_response = client.get("/api/db/schema/1")
    assert schema_response.status_code == 401


def test_session_expiry_and_refresh(client):
    """
    Test token refresh functionality.
    """
    # Step 1: User login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    
    # Set up auth headers for subsequent requests
    auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Step 2: Use refresh token to get a new access token
    refresh_response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {token_data['refresh_token']}"}
    )
    assert refresh_response.status_code == 200
    new_token_data = refresh_response.json()
    assert "access_token" in new_token_data
    assert new_token_data["access_token"] != token_data["access_token"]
    
    # Step 3: Verify the new token works
    new_auth_headers = {"Authorization": f"Bearer {new_token_data['access_token']}"}
    db_list_response = client.get("/api/db/list", headers=new_auth_headers)
    assert db_list_response.status_code == 200