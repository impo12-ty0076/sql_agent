"""
End-to-end tests for report generation and data visualization.
"""
import pytest
from fastapi.testclient import TestClient
import time


def test_report_generation_flow(client, auth_headers):
    """
    Test the complete flow for report generation from query results.
    
    This test verifies:
    1. User can execute a query
    2. User can request a report based on query results
    3. System generates visualizations and insights
    4. User can view the generated report
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
    
    # Step 3: Execute a SQL query that returns data suitable for visualization
    sql_query = """
    SELECT d.department_name, COUNT(e.employee_id) AS employee_count 
    FROM dbo.departments d 
    LEFT JOIN dbo.employees e ON d.department_id = e.department_id 
    GROUP BY d.department_name 
    ORDER BY employee_count DESC
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
    assert "result_id" in execute_result
    
    result_id = execute_result["result_id"]
    
    # Step 4: Request report generation
    report_request_response = client.post(
        f"/api/result/{result_id}/report",
        json={
            "report_type": "comprehensive",
            "visualization_types": ["bar", "pie"]
        },
        headers=auth_headers
    )
    assert report_request_response.status_code == 202  # Accepted (async processing)
    report_request_data = report_request_response.json()
    assert "report_id" in report_request_data
    assert "status" in report_request_data
    assert report_request_data["status"] in ["pending", "processing"]
    
    report_id = report_request_data["report_id"]
    
    # Step 5: Poll for report completion (with timeout)
    max_attempts = 10
    attempt = 0
    report_status = "pending"
    
    while report_status in ["pending", "processing"] and attempt < max_attempts:
        time.sleep(1)  # Wait before checking status
        report_status_response = client.get(
            f"/api/report/{report_id}/status",
            headers=auth_headers
        )
        assert report_status_response.status_code == 200
        status_data = report_status_response.json()
        report_status = status_data["status"]
        attempt += 1
    
    assert report_status == "completed", f"Report generation did not complete in time. Status: {report_status}"
    
    # Step 6: Get the generated report
    report_response = client.get(
        f"/api/report/{report_id}",
        headers=auth_headers
    )
    assert report_response.status_code == 200
    report_data = report_response.json()
    
    # Verify report structure
    assert "visualizations" in report_data
    assert len(report_data["visualizations"]) > 0
    assert "insights" in report_data
    assert len(report_data["insights"]) > 0
    
    # Verify visualization structure
    first_viz = report_data["visualizations"][0]
    assert "type" in first_viz
    assert "title" in first_viz
    assert "image_data" in first_viz


def test_natural_language_summary_generation(client, auth_headers):
    """
    Test natural language summary generation for query results.
    
    This test verifies:
    1. User can execute a query
    2. User can request a natural language summary of the results
    3. System generates a meaningful summary
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
    result_id = execute_result["result_id"]
    
    # Step 4: Request natural language summary
    summary_response = client.get(
        f"/api/result/{result_id}/summary",
        headers=auth_headers
    )
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    
    # Verify summary structure
    assert "summary" in summary_data
    assert len(summary_data["summary"]) > 0
    
    # Verify summary content (basic checks)
    summary_text = summary_data["summary"]
    assert "employee" in summary_text.lower()


def test_python_code_execution_for_analysis(client, auth_headers):
    """
    Test Python code execution for custom data analysis.
    
    This test verifies:
    1. User can execute a query
    2. User can submit custom Python code for analysis
    3. System executes the code and returns results
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
    result_id = execute_result["result_id"]
    
    # Step 4: Submit Python code for analysis
    python_code = """
    import pandas as pd
    import matplotlib.pyplot as plt
    import io
    import base64
    
    # Convert result to DataFrame
    df = pd.DataFrame(data=result_data['rows'], columns=[col['name'] for col in result_data['columns']])
    
    # Calculate statistics
    total_employees = df['employee_count'].sum()
    avg_employees = df['employee_count'].mean()
    max_dept = df.loc[df['employee_count'].idxmax()]
    
    # Create visualization
    plt.figure(figsize=(10, 6))
    bars = plt.bar(df['department_name'], df['employee_count'])
    plt.title('Employee Count by Department')
    plt.xlabel('Department')
    plt.ylabel('Number of Employees')
    plt.xticks(rotation=45, ha='right')
    
    # Highlight max department
    max_index = df['employee_count'].idxmax()
    bars[max_index].set_color('red')
    
    # Save plot to base64
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Return results
    analysis_result = {
        'total_employees': int(total_employees),
        'average_employees_per_dept': float(avg_employees),
        'department_with_most_employees': {
            'name': max_dept['department_name'],
            'count': int(max_dept['employee_count'])
        },
        'visualization': {
            'type': 'bar_chart',
            'title': 'Employee Count by Department',
            'image_data': f'data:image/png;base64,{image_base64}'
        }
    }
    """
    
    python_execute_response = client.post(
        f"/api/result/{result_id}/python",
        json={
            "code": python_code
        },
        headers=auth_headers
    )
    assert python_execute_response.status_code == 202  # Accepted (async processing)
    python_job_data = python_execute_response.json()
    assert "job_id" in python_job_data
    
    job_id = python_job_data["job_id"]
    
    # Step 5: Poll for Python execution completion (with timeout)
    max_attempts = 10
    attempt = 0
    job_status = "pending"
    
    while job_status in ["pending", "processing"] and attempt < max_attempts:
        time.sleep(1)  # Wait before checking status
        job_status_response = client.get(
            f"/api/python/job/{job_id}",
            headers=auth_headers
        )
        assert job_status_response.status_code == 200
        status_data = job_status_response.json()
        job_status = status_data["status"]
        attempt += 1
    
    assert job_status == "completed", f"Python execution did not complete in time. Status: {job_status}"
    
    # Step 6: Get the Python execution results
    results_response = client.get(
        f"/api/python/job/{job_id}/results",
        headers=auth_headers
    )
    assert results_response.status_code == 200
    results_data = results_response.json()
    
    # Verify results structure
    assert "analysis_result" in results_data
    analysis = results_data["analysis_result"]
    assert "total_employees" in analysis
    assert "average_employees_per_dept" in analysis
    assert "department_with_most_employees" in analysis
    assert "visualization" in analysis