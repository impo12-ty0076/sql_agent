# MS-SQL Connector

This module provides a connector for Microsoft SQL Server databases in the SQL DB LLM Agent system.

## Features

- Connection management with connection pooling
- Query execution with parameter support
- Schema discovery and metadata retrieval
- Query validation and security checks
- Error handling and retry logic for transient errors
- Query cancellation support
- Comprehensive logging

## Requirements

- Python 3.8+
- One of the following MS-SQL drivers:
  - `pyodbc` (recommended)
  - `pymssql` (alternative)
- SQL Server 2012 or later

## Installation

Install the required dependencies:

```bash
pip install pyodbc backoff
# or
pip install pymssql backoff
```

For `pyodbc`, you also need to install the Microsoft ODBC Driver for SQL Server:

- Windows: [Download ODBC Driver](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Linux: [Install ODBC Driver on Linux](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- macOS: [Install ODBC Driver on macOS](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos)

## Usage

### Basic Usage

```python
from sql_agent.backend.models.database import Database, DBType, ConnectionConfig
from sql_agent.backend.db.connectors.init_connectors import init_db_connectors, get_connector_factory
from datetime import datetime

# Initialize connectors
init_db_connectors()

# Create database configuration
db_config = Database(
    id="my-mssql-db",
    name="My SQL Server",
    type=DBType.MSSQL,
    host="localhost",
    port=1433,
    default_schema="master",
    connection_config=ConnectionConfig(
        username="sa",
        password_encrypted="your_password",  # In production, use encrypted password
        options={
            "timeout": 30,
            "encrypt": "yes",
            "trustservercertificate": "yes"
        }
    ),
    created_at=datetime.now(),
    updated_at=datetime.now()
)

# Get connector factory
factory = get_connector_factory()

# Create connector
connector = factory.create_connector(db_config)

# Test connection
success, message = connector.test_connection(db_config)
if success:
    print(f"Connection successful: {message}")
else:
    print(f"Connection failed: {message}")

# Execute query
result = connector.execute_query(
    db_config,
    "SELECT TOP 10 * FROM sys.objects",
    max_rows=10
)

# Process results
print(f"Query returned {result.row_count} rows")
for row in result.rows:
    print(row)

# Close connections
factory.close_all_connections()
```

### Parameterized Queries

```python
# Execute query with parameters
result = connector.execute_query(
    db_config,
    "SELECT * FROM users WHERE department = :dept AND active = :status",
    params={
        "dept": "Engineering",
        "status": True
    },
    max_rows=100
)
```

### Schema Discovery

```python
# Get database schema
schema = connector.get_schema(db_config)

# Print schema information
for schema_obj in schema.schemas:
    print(f"Schema: {schema_obj.name}")
    for table in schema_obj.tables:
        print(f"  Table: {table.name}")
        for column in table.columns:
            print(f"    Column: {column.name} ({column.type})")
```

### Query Validation

```python
# Validate a query without executing it
is_valid, error_message = connector.validate_query(db_config, "SELECT * FROM users")
if is_valid:
    print("Query is valid")
else:
    print(f"Query is invalid: {error_message}")

# Check if a query is read-only
is_read_only = connector.is_read_only_query("SELECT * FROM users")
print(f"Query is read-only: {is_read_only}")
```

### Query Cancellation

```python
import threading

# Start a long-running query in a separate thread
def execute_long_query():
    try:
        connector.execute_query(
            db_config,
            "WAITFOR DELAY '00:00:30'; SELECT * FROM sys.objects",  # 30-second delay
            timeout=60
        )
    except Exception as e:
        print(f"Query was cancelled: {str(e)}")

thread = threading.Thread(target=execute_long_query)
thread.start()

# Wait a bit and then cancel the query
import time
time.sleep(2)

# Get running queries
running_queries = connector.query_tracker.get_running_queries()
if running_queries:
    query_id = list(running_queries.keys())[0]
    print(f"Cancelling query {query_id}...")
    cancelled = connector.cancel_query(query_id)
    print(f"Query cancellation result: {cancelled}")

# Wait for the thread to finish
thread.join()
```

## Error Handling

The connector implements retry logic for transient errors such as connection timeouts, deadlocks, and other temporary issues. The retry behavior can be customized by modifying the following class variables:

```python
# Maximum number of retry attempts
MSSQLConnector.MAX_RETRY_ATTEMPTS = 3

# Delay between retry attempts (in seconds)
MSSQLConnector.RETRY_DELAY = 1
```

## Connection Pooling

The connector uses a connection pool to efficiently manage database connections. The pool settings can be configured when initializing the connectors:

```python
from sql_agent.backend.db.connectors.init_connectors import init_db_connectors

init_db_connectors({
    "connection_pool_size": 20,       # Maximum connections per database
    "connection_timeout": 300,        # Idle connection timeout in seconds
    "max_connection_age": 1800        # Maximum connection age in seconds
})
```

## Security Considerations

- The connector enforces read-only operations by default
- SQL injection protection through query validation
- Parameter binding for safe query execution
- Connection encryption support
- Timeout settings to prevent long-running queries

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify the server address, port, and credentials
   - Check network connectivity and firewall settings
   - Ensure the SQL Server instance is running

2. **Driver Issues**:
   - Verify that either `pyodbc` or `pymssql` is installed
   - For `pyodbc`, ensure the ODBC driver is installed correctly

3. **Permission Issues**:
   - Verify the user has appropriate permissions on the database
   - Check if the database is accessible to the user

4. **Query Timeout**:
   - Increase the timeout value for long-running queries
   - Optimize the query to improve performance

### Logging

The connector uses Python's standard logging module. To enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. Use connection pooling (enabled by default)
2. Set appropriate timeout values
3. Limit result sets with `max_rows` parameter
4. Use parameterized queries
5. Close connections when done using `factory.close_all_connections()`