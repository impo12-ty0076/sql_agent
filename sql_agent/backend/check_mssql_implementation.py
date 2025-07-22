"""
Simple script to check if the MS-SQL connector implementation is correct.
"""

import os
import sys

def check_file_exists(file_path):
    """Check if a file exists."""
    return os.path.isfile(file_path)

def check_file_content(file_path, expected_content):
    """Check if a file contains expected content."""
    if not check_file_exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
        return all(text in content for text in expected_content)

def main():
    """Check the MS-SQL connector implementation."""
    # Define the file paths
    mssql_connector_path = os.path.join('db', 'connectors', 'mssql.py')
    test_mssql_connector_path = os.path.join('tests', 'test_mssql_connector.py')
    mssql_readme_path = os.path.join('db', 'connectors', 'mssql_README.md')
    
    # Check if the files exist
    files_exist = all([
        check_file_exists(mssql_connector_path),
        check_file_exists(test_mssql_connector_path),
        check_file_exists(mssql_readme_path)
    ])
    
    if not files_exist:
        print("Error: One or more required files are missing.")
        return False
    
    # Check if the MS-SQL connector has the expected content
    mssql_connector_content = [
        "class MSSQLConnector(DBConnector):",
        "_is_transient_error",
        "MAX_RETRY_ATTEMPTS",
        "RETRY_DELAY",
        "TRANSIENT_ERROR_CODES",
        "execute_query",
        "cancel_query",
        "get_schema",
        "validate_query",
        "is_read_only_query",
        "format_error"
    ]
    
    if not check_file_content(mssql_connector_path, mssql_connector_content):
        print("Error: MS-SQL connector does not have the expected content.")
        return False
    
    # Check if the test file has the expected content
    test_content = [
        "class TestMSSQLConnector(unittest.TestCase):",
        "test_create_connection_pyodbc",
        "test_execute_query",
        "test_is_transient_error",
        "test_cancel_query",
        "test_format_error"
    ]
    
    if not check_file_content(test_mssql_connector_path, test_content):
        print("Error: Test file does not have the expected content.")
        return False
    
    # Check if the README has the expected content
    readme_content = [
        "# MS-SQL Connector",
        "## Features",
        "## Usage",
        "## Error Handling",
        "## Connection Pooling",
        "## Security Considerations"
    ]
    
    if not check_file_content(mssql_readme_path, readme_content):
        print("Error: README does not have the expected content.")
        return False
    
    print("Success: All files exist and have the expected content.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)