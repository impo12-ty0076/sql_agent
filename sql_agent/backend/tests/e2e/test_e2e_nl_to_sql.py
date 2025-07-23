"""
End-to-end tests for natural language to SQL conversion and query execution.
"""
import pytest
from fastapi.testclient import TestClient


def test_nl_to_sql_conversion_flow(client, auth_headers):
    """
    Test the complete flow from natural language query to SQL execution.
    
    This test verifies:
    1. User can submit a natural language query
    2. System converts it to SQL
    3. User can review and execute the SQL
    4. System returns query results
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
    
    # Step 3: Submit natural language query
    nl_query = "Show me all employees in the sales department"
    nl_query_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": nl_query
        },
        headers=auth_headers
    )
    assert nl_query_response.status_code == 200
    nl_query_result = nl_query_response.json()
    assert "query_id" in nl_query_result
    assert "generated_sql" in nl_query_result
    assert "explanation" in nl_query_result
    
    query_id = nl_query_result["query_id"]
    generated_sql = nl_query_result["generated_sql"]
    
    # Step 4: Execute the generated SQL
    execute_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "query_id": query_id,
            "sql": generated_sql
        },
        headers=auth_headers
    )
    assert execute_response.status_code == 200
    execute_result = execute_response.json()
    assert "result_id" in execute_result
    
    result_id = execute_result["result_id"]
    
    # Step 5: Get query results
    result_response = client.get(
        f"/api/result/{result_id}",
        headers=auth_headers
    )
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert "columns" in result_data
    assert "rows" in result_data
    assert "row_count" in result_data


def test_nl_to_sql_with_context_flow(client, auth_headers):
    """
    Test natural language query with context from previous queries.
    
    This test verifies:
    1. User can submit an initial query
    2. User can submit a follow-up query that references the previous query
    3. System maintains context between queries
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
    
    # Step 3: Submit initial natural language query
    initial_query = "Show me all departments"
    initial_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": initial_query
        },
        headers=auth_headers
    )
    assert initial_response.status_code == 200
    initial_result = initial_response.json()
    assert "conversation_id" in initial_result
    
    conversation_id = initial_result["conversation_id"]
    
    # Step 4: Submit follow-up query with context
    followup_query = "How many employees are in each of them?"
    followup_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": followup_query,
            "conversation_id": conversation_id
        },
        headers=auth_headers
    )
    assert followup_response.status_code == 200
    followup_result = followup_response.json()
    assert "generated_sql" in followup_result
    assert "conversation_id" in followup_result
    assert followup_result["conversation_id"] == conversation_id
    
    # Verify the SQL references both tables (departments and employees)
    generated_sql = followup_result["generated_sql"].lower()
    assert "departments" in generated_sql
    assert "employees" in generated_sql
    assert "count" in generated_sql


def test_sql_validation_and_error_handling(client, auth_headers):
    """
    Test SQL validation and error handling.
    
    This test verifies:
    1. System validates SQL before execution
    2. System properly handles SQL errors
    3. System prevents execution of dangerous SQL commands
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
    
    # Step 3: Try to execute invalid SQL
    invalid_sql = "SELECT * FROM nonexistent_table"
    invalid_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": invalid_sql
        },
        headers=auth_headers
    )
    assert invalid_response.status_code == 400
    error_data = invalid_response.json()
    assert "error" in error_data
    
    # Step 4: Try to execute dangerous SQL (data modification)
    dangerous_sql = "DROP TABLE employees"
    dangerous_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": dangerous_sql
        },
        headers=auth_headers
    )
    assert dangerous_response.status_code == 400
    error_data = dangerous_response.json()
    assert "error" in error_data
    assert "data modification" in error_data["error"].lower() or "not allowed" in error_data["error"].lower()