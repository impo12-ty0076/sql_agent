"""
Configuration settings for performance tests.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent.parent

# Test database settings
TEST_DB_URL = os.environ.get("PERF_TEST_DB_URL", "sqlite:///./test_performance.db")

# Test user credentials
TEST_USER = {
    "username": "perftest",
    "password": "perftest123",
    "email": "perftest@example.com"
}

# Test admin credentials
TEST_ADMIN = {
    "username": "perfadmin",
    "password": "perfadmin123",
    "email": "perfadmin@example.com"
}

# Performance test settings
LOAD_TEST_USERS = int(os.environ.get("PERF_TEST_USERS", "50"))
LOAD_TEST_DURATION = int(os.environ.get("PERF_TEST_DURATION", "60"))  # seconds
LOAD_TEST_RAMP_UP = int(os.environ.get("PERF_TEST_RAMP_UP", "10"))  # seconds

# Test queries of varying complexity
TEST_QUERIES = {
    "simple": "SELECT * FROM dbo.employees LIMIT 10",
    "medium": """
        SELECT d.department_name, COUNT(e.employee_id) AS employee_count 
        FROM dbo.departments d 
        LEFT JOIN dbo.employees e ON d.department_id = e.department_id 
        GROUP BY d.department_name 
        ORDER BY employee_count DESC
    """,
    "complex": """
        WITH dept_stats AS (
            SELECT 
                d.department_id,
                d.department_name,
                COUNT(e.employee_id) AS employee_count,
                AVG(DATEDIFF(day, e.hire_date, GETDATE())) AS avg_tenure_days
            FROM dbo.departments d
            LEFT JOIN dbo.employees e ON d.department_id = e.department_id
            GROUP BY d.department_id, d.department_name
        )
        SELECT 
            ds.department_name,
            ds.employee_count,
            ds.avg_tenure_days,
            RANK() OVER (ORDER BY ds.employee_count DESC) AS size_rank,
            RANK() OVER (ORDER BY ds.avg_tenure_days DESC) AS tenure_rank
        FROM dept_stats ds
        ORDER BY ds.employee_count DESC
    """
}

# Natural language queries for testing
NL_TEST_QUERIES = [
    "Show me all employees",
    "How many employees are in each department?",
    "Which department has the highest average tenure?",
    "Show me the top 5 departments by employee count",
    "What's the distribution of employees across departments?",
    "Compare the number of employees in sales versus marketing"
]

# Large result test settings
LARGE_RESULT_ROWS = int(os.environ.get("PERF_TEST_LARGE_ROWS", "10000"))

# Performance thresholds
RESPONSE_TIME_THRESHOLD = {
    "p50": 500,  # milliseconds
    "p90": 1000,  # milliseconds
    "p99": 2000   # milliseconds
}

# Memory usage thresholds
MEMORY_THRESHOLD = {
    "max_per_request": 100 * 1024 * 1024,  # 100 MB
    "leak_tolerance": 5 * 1024 * 1024      # 5 MB
}

# Database connection pool settings
DB_POOL_SETTINGS = {
    "min_connections": 5,
    "max_connections": 20,
    "overflow": 10,
    "timeout": 30  # seconds
}

# Output directory for test results
RESULTS_DIR = BASE_DIR / "backend" / "tests" / "performance" / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Locust settings
LOCUST_HOST = os.environ.get("LOCUST_HOST", "http://localhost:8000")
LOCUST_WEB_PORT = int(os.environ.get("LOCUST_WEB_PORT", "8089"))
LOCUST_HEADLESS = os.environ.get("LOCUST_HEADLESS", "true").lower() == "true"