"""
End-to-end tests for query history management and sharing functionality.
"""
import pytest
from fastapi.testclient import TestClient


def test_query_history_management_flow(client, auth_headers):
    """
    Test the complete flow for query history management.
    
    This test verifies:
    1. Queries are automatically saved to history
    2. User can view query history
    3. User can filter and search history
    4. User can mark favorites and add tags
    """
    # Step 1: Get available databases
    db_list_response = client.get("/api/db/list", headers=auth_headers)
    assert db_list_response.status_code == 200
    db_list = db_list_response.json()
    test_db = db_list[0]
    
    # Step 2: Connect to database
    connect_response = client.post(
        f"/api/db/connect/{test_db['id']}",
        headers=auth_headers
    )
    assert connect_response.status_code == 200
    
    # Step 3: Execute a SQL query
    sql_query = "SELECT * FROM dbo.employees"
    execute_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": sql_query
        },
        headers=auth_headers
    )
    assert execute_response.status_code == 200
    execute_result = execute_response.json()
    query_id = execute_result["query_id"]
    
    # Step 4: Execute another SQL query
    sql_query2 = "SELECT * FROM dbo.departments"
    execute_response2 = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": sql_query2
        },
        headers=auth_headers
    )
    assert execute_response2.status_code == 200
    
    # Step 5: Get query history
    history_response = client.get(
        "/api/history",
        headers=auth_headers
    )
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert isinstance(history_data, list)
    assert len(history_data) >= 2  # At least our two queries
    
    # Find our first query in the history
    query_history_item = next((item for item in history_data if item["query_id"] == query_id), None)
    assert query_history_item is not None
    history_id = query_history_item["id"]
    
    # Step 6: Mark query as favorite
    favorite_response = client.put(
        f"/api/history/{history_id}/favorite",
        json={"favorite": True},
        headers=auth_headers
    )
    assert favorite_response.status_code == 200
    
    # Step 7: Add tags to query
    tags_response = client.put(
        f"/api/history/{history_id}/tags",
        json={"tags": ["important", "test"]},
        headers=auth_headers
    )
    assert tags_response.status_code == 200
    
    # Step 8: Filter history by favorite
    favorite_filter_response = client.get(
        "/api/history?favorite=true",
        headers=auth_headers
    )
    assert favorite_filter_response.status_code == 200
    favorite_data = favorite_filter_response.json()
    assert len(favorite_data) > 0
    assert any(item["id"] == history_id for item in favorite_data)
    
    # Step 9: Filter history by tag
    tag_filter_response = client.get(
        "/api/history?tag=important",
        headers=auth_headers
    )
    assert tag_filter_response.status_code == 200
    tag_data = tag_filter_response.json()
    assert len(tag_data) > 0
    assert any(item["id"] == history_id for item in tag_data)
    
    # Step 10: Search history by query text
    search_response = client.get(
        "/api/history?search=employees",
        headers=auth_headers
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert len(search_data) > 0
    assert any("employees" in item["sql"].lower() for item in search_data)


def test_query_sharing_flow(client, auth_headers, admin_auth_headers):
    """
    Test the complete flow for query sharing.
    
    This test verifies:
    1. User can execute a query
    2. User can share the query and results
    3. Other users can access the shared query
    4. Access controls are properly enforced
    """
    # Step 1: Get available databases
    db_list_response = client.get("/api/db/list", headers=auth_headers)
    assert db_list_response.status_code == 200
    db_list = db_list_response.json()
    test_db = db_list[0]
    
    # Step 2: Connect to database
    connect_response = client.post(
        f"/api/db/connect/{test_db['id']}",
        headers=auth_headers
    )
    assert connect_response.status_code == 200
    
    # Step 3: Execute a SQL query
    sql_query = """
    SELECT d.department_name, COUNT(e.employee_id) AS employee_count 
    FROM dbo.departments d 
    LEFT JOIN dbo.employees e ON d.department_id = e.department_id 
    GROUP BY d.department_name
    """
    execute_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": sql_query
        },
        headers=auth_headers
    )
    assert execute_response.status_code == 200
    execute_result = execute_response.json()
    query_id = execute_result["query_id"]
    result_id = execute_result["result_id"]
    
    # Step 4: Share the query and results
    share_response = client.post(
        f"/api/share/query/{query_id}",
        json={
            "expiration_days": 7,
            "allow_comments": True,
            "allowed_users": ["testadmin"]  # Share with admin user
        },
        headers=auth_headers
    )
    assert share_response.status_code == 200
    share_data = share_response.json()
    assert "share_id" in share_data
    assert "access_url" in share_data
    
    share_id = share_data["share_id"]
    
    # Step 5: Access shared query as admin user
    shared_query_response = client.get(
        f"/api/share/{share_id}",
        headers=admin_auth_headers
    )
    assert shared_query_response.status_code == 200
    shared_query_data = shared_query_response.json()
    assert shared_query_data["query_id"] == query_id
    assert "sql" in shared_query_data
    assert "result" in shared_query_data
    
    # Step 6: Add comment to shared query
    comment_response = client.post(
        f"/api/share/{share_id}/comment",
        json={"comment": "This is a test comment"},
        headers=admin_auth_headers
    )
    assert comment_response.status_code == 200
    
    # Step 7: Get comments on shared query
    comments_response = client.get(
        f"/api/share/{share_id}/comments",
        headers=auth_headers
    )
    assert comments_response.status_code == 200
    comments_data = comments_response.json()
    assert len(comments_data) > 0
    assert comments_data[0]["comment"] == "This is a test comment"
    
    # Step 8: Try to access with unauthorized user (should fail)
    # Create a new user for this test
    client.post(
        "/api/admin/users",
        json={
            "username": "unauthorized_user",
            "email": "unauthorized@example.com",
            "password": "password123",
            "role": "user"
        },
        headers=admin_auth_headers
    )
    
    # Login as unauthorized user
    unauth_login_response = client.post(
        "/api/auth/login",
        data={"username": "unauthorized_user", "password": "password123"}
    )
    unauth_token = unauth_login_response.json()["access_token"]
    unauth_headers = {"Authorization": f"Bearer {unauth_token}"}
    
    # Try to access shared query
    unauth_query_response = client.get(
        f"/api/share/{share_id}",
        headers=unauth_headers
    )
    assert unauth_query_response.status_code == 403  # Forbidden
    
    # Step 9: Update sharing settings
    update_share_response = client.put(
        f"/api/share/{share_id}",
        json={
            "expiration_days": 14,  # Extend expiration
            "allow_comments": False,  # Disable comments
            "allowed_users": ["testadmin", "unauthorized_user"]  # Add unauthorized user
        },
        headers=auth_headers
    )
    assert update_share_response.status_code == 200
    
    # Step 10: Now unauthorized user should be able to access
    auth_query_response = client.get(
        f"/api/share/{share_id}",
        headers=unauth_headers
    )
    assert auth_query_response.status_code == 200
    
    # Step 11: But should not be able to comment (comments disabled)
    unauth_comment_response = client.post(
        f"/api/share/{share_id}/comment",
        json={"comment": "This should fail"},
        headers=unauth_headers
    )
    assert unauth_comment_response.status_code == 400  # Bad request