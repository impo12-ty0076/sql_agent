"""
End-to-end tests for error scenarios and edge cases.
"""
import pytest
from fastapi.testclient import TestClient


def test_error_handling_for_invalid_queries(client, auth_headers):
    """
    Test error handling for invalid queries.
    
    This test verifies:
    1. System properly handles syntax errors in SQL
    2. System provides helpful error messages
    3. System prevents execution of dangerous queries
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
    
    # Step 3: Test SQL syntax error
    invalid_sql = "SELECT * FORM employees"  # Intentional typo
    syntax_error_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": invalid_sql
        },
        headers=auth_headers
    )
    assert syntax_error_response.status_code == 400
    error_data = syntax_error_response.json()
    assert "error" in error_data
    assert "syntax" in error_data["error"].lower()
    assert "suggestions" in error_data
    
    # Step 4: Test non-existent table
    nonexistent_sql = "SELECT * FROM nonexistent_table"
    table_error_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": nonexistent_sql
        },
        headers=auth_headers
    )
    assert table_error_response.status_code == 400
    error_data = table_error_response.json()
    assert "error" in error_data
    assert "table" in error_data["error"].lower()
    
    # Step 5: Test data modification attempt
    modification_sql = "DELETE FROM employees"
    modification_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": modification_sql
        },
        headers=auth_headers
    )
    assert modification_response.status_code == 400
    error_data = modification_response.json()
    assert "error" in error_data
    assert "modification" in error_data["error"].lower() or "not allowed" in error_data["error"].lower()
    
    # Step 6: Test SQL injection attempt
    injection_sql = "SELECT * FROM employees; DROP TABLE employees;"
    injection_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": injection_sql
        },
        headers=auth_headers
    )
    assert injection_response.status_code == 400
    error_data = injection_response.json()
    assert "error" in error_data
    assert "multiple" in error_data["error"].lower() or "not allowed" in error_data["error"].lower()


def test_error_handling_for_natural_language_queries(client, auth_headers):
    """
    Test error handling for problematic natural language queries.
    
    This test verifies:
    1. System handles ambiguous natural language queries
    2. System provides clarification requests
    3. System handles queries outside the database domain
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
    
    # Step 3: Test ambiguous query
    ambiguous_query = "Show me the data"
    ambiguous_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": ambiguous_query
        },
        headers=auth_headers
    )
    assert ambiguous_response.status_code == 200
    ambiguous_data = ambiguous_response.json()
    assert "clarification_needed" in ambiguous_data
    assert ambiguous_data["clarification_needed"] == True
    assert "clarification_questions" in ambiguous_data
    assert len(ambiguous_data["clarification_questions"]) > 0
    
    # Step 4: Test out-of-domain query
    irrelevant_query = "What is the weather like today?"
    irrelevant_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": irrelevant_query
        },
        headers=auth_headers
    )
    assert irrelevant_response.status_code == 400
    irrelevant_data = irrelevant_response.json()
    assert "error" in irrelevant_data
    assert "database" in irrelevant_data["error"].lower()
    
    # Step 5: Test query with missing context
    context_query = "How many of them are there?"
    context_response = client.post(
        "/api/query/natural",
        json={
            "database_id": test_db["id"],
            "query": context_query
        },
        headers=auth_headers
    )
    assert context_response.status_code == 200
    context_data = context_response.json()
    assert "clarification_needed" in context_data
    assert context_data["clarification_needed"] == True


def test_error_handling_for_long_running_queries(client, auth_headers):
    """
    Test error handling for long-running queries.
    
    This test verifies:
    1. System handles queries that exceed timeout limits
    2. User can cancel long-running queries
    3. System provides status updates for long-running queries
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
    
    # Step 3: Execute a long-running query
    long_query = """
    WITH numbers AS (
        SELECT 1 AS n
        UNION ALL
        SELECT n + 1 FROM numbers WHERE n < 1000000
    )
    SELECT COUNT(*) FROM numbers
    """
    
    long_query_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": long_query,
            "timeout": 1  # Set a very short timeout (1 second)
        },
        headers=auth_headers
    )
    
    # The query should either time out or be accepted for async execution
    if long_query_response.status_code == 400:
        # Query timed out immediately
        error_data = long_query_response.json()
        assert "error" in error_data
        assert "timeout" in error_data["error"].lower()
    else:
        # Query was accepted for async execution
        assert long_query_response.status_code == 202
        query_data = long_query_response.json()
        assert "query_id" in query_data
        
        query_id = query_data["query_id"]
        
        # Step 4: Check query status
        status_response = client.get(
            f"/api/query/{query_id}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["pending", "executing", "completed", "failed", "cancelled"]
        
        # Step 5: Cancel the query if it's still running
        if status_data["status"] in ["pending", "executing"]:
            cancel_response = client.post(
                f"/api/query/{query_id}/cancel",
                headers=auth_headers
            )
            assert cancel_response.status_code == 200
            
            # Verify the query was cancelled
            status_response = client.get(
                f"/api/query/{query_id}/status",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "cancelled"


def test_error_handling_for_large_result_sets(client, auth_headers):
    """
    Test error handling for queries that return large result sets.
    
    This test verifies:
    1. System properly handles large result sets
    2. Pagination works correctly for large results
    3. System provides performance metrics for large queries
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
    
    # Step 3: Execute a query that returns a large result set
    # This is a simulated large result query - in a real test, you'd use a query that actually returns many rows
    large_query = "SELECT * FROM dbo.employees CROSS JOIN dbo.departments"
    
    large_query_response = client.post(
        "/api/query/execute",
        json={
            "database_id": test_db["id"],
            "sql": large_query
        },
        headers=auth_headers
    )
    
    # The query should be accepted
    assert large_query_response.status_code in [200, 202]
    query_data = large_query_response.json()
    
    if "result_id" in query_data:
        result_id = query_data["result_id"]
        
        # Step 4: Get the first page of results
        first_page_response = client.get(
            f"/api/result/{result_id}?page=1&page_size=100",
            headers=auth_headers
        )
        assert first_page_response.status_code == 200
        first_page_data = first_page_response.json()
        
        # Verify pagination info
        assert "rows" in first_page_data
        assert "row_count" in first_page_data
        assert "total_row_count" in first_page_data
        assert "page" in first_page_data
        assert "total_pages" in first_page_data
        assert first_page_data["page"] == 1
        
        # If there are multiple pages, check the second page
        if first_page_data["total_pages"] > 1:
            second_page_response = client.get(
                f"/api/result/{result_id}?page=2&page_size=100",
                headers=auth_headers
            )
            assert second_page_response.status_code == 200
            second_page_data = second_page_response.json()
            assert second_page_data["page"] == 2
            
            # Verify different rows are returned
            assert first_page_data["rows"] != second_page_data["rows"]
        
        # Step 5: Check performance metrics
        metrics_response = client.get(
            f"/api/result/{result_id}/metrics",
            headers=auth_headers
        )
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        
        # Verify metrics structure
        assert "execution_time_ms" in metrics_data
        assert "row_count" in metrics_data
        assert "memory_usage_kb" in metrics_data