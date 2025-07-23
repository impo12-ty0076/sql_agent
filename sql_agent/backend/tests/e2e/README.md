# End-to-End Tests for SQL DB LLM Agent

This directory contains end-to-end tests for the SQL DB LLM Agent system. These tests verify the complete flow from frontend to backend and ensure that all components work together correctly.

## Test Categories

The end-to-end tests are organized into the following categories:

1. **Authentication and Database Connection** (`test_e2e_auth_and_db.py`)
   - User login and session management
   - Database connection and schema retrieval
   - Access control and permissions

2. **Natural Language to SQL Conversion** (`test_e2e_nl_to_sql.py`)
   - Natural language query processing
   - SQL generation and validation
   - Context-aware follow-up queries

3. **Report Generation and Data Visualization** (`test_e2e_report_generation.py`)
   - Query result visualization
   - Natural language summary generation
   - Python code execution for custom analysis

4. **History Management and Sharing** (`test_e2e_history_and_sharing.py`)
   - Query history tracking and filtering
   - Favorites and tagging
   - Query sharing and collaboration

5. **Error Scenarios and Edge Cases** (`test_e2e_error_scenarios.py`)
   - Error handling for invalid queries
   - Handling of ambiguous natural language
   - Long-running query management
   - Large result set handling

## Running the Tests

You can run the end-to-end tests using the provided `run_e2e_tests.py` script:

```bash
# Run all end-to-end tests
python -m backend.tests.e2e.run_e2e_tests

# Run tests with verbose output
python -m backend.tests.e2e.run_e2e_tests --verbose

# Run specific test categories
python -m backend.tests.e2e.run_e2e_tests --pattern auth
python -m backend.tests.e2e.run_e2e_tests --pattern nl_to_sql
python -m backend.tests.e2e.run_e2e_tests --pattern report
```

## Test Environment

The tests use an in-memory SQLite database for testing, with pre-configured test data. The test environment includes:

- Test users (regular user and admin)
- Test database connections
- Sample database schema
- Mock data for testing

## Test Reports

After running the tests, an HTML report is generated at `backend/tests/e2e/e2e_test_report.html`. This report includes:

- Test results summary
- Detailed test outcomes
- Error messages for failed tests
- Test execution time

## Adding New Tests

To add new end-to-end tests:

1. Create a new test file in the `backend/tests/e2e` directory
2. Import the necessary fixtures from `conftest.py`
3. Write test functions that verify complete user flows
4. Run the tests to ensure they pass

## Best Practices

When writing end-to-end tests:

- Focus on complete user flows rather than individual functions
- Test realistic user scenarios
- Verify both success and error cases
- Keep tests independent of each other
- Use descriptive test names and documentation
- Minimize test execution time where possible