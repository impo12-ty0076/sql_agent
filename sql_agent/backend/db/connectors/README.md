# Database Connectors

This directory contains the database connector interface and implementations for the SQL DB LLM Agent system.

## Overview

The database connectors provide a unified interface for connecting to different types of databases, executing queries, and retrieving schema information. The system is designed to be extensible, allowing new database types to be added easily.

## Components

### Base Interface (`base.py`)

The base interface defines the contract that all database connectors must implement:

- `DBConnector`: Abstract base class for database connectors
- `ConnectionPoolManager`: Abstract base class for managing database connection pools

### Connection Pool Management (`pool.py`)

The connection pool manager handles the creation, reuse, and cleanup of database connections:

- `DefaultConnectionPoolManager`: Default implementation of the connection pool manager
- `PooledConnection`: Wrapper for a database connection with metadata for pool management

### Query Execution and Result Processing (`query_executor.py`)

Utilities for executing queries and processing results:

- `QueryExecutionTracker`: Tracks running queries and provides methods to cancel them
- `QueryResultProcessor`: Processes query results into a standardized format

### SQL Validation (`sql_validator.py`)

Utilities for validating SQL queries:

- `SQLValidator`: Validates SQL queries for safety and correctness

### Connector Factory (`factory.py`)

Factory for creating database connectors based on database type:

- `DBConnectorFactory`: Factory for creating database connectors
- `connector_factory`: Global instance of the connector factory

### Connector Implementations

- `mssql.py`: MS-SQL database connector implementation
- (Future) `hana.py`: SAP HANA database connector implementation

### Initialization (`init_connectors.py`)

Initializes and registers database connectors:

- `init_db_connectors()`: Initialize and register database connectors
- `get_connector_factory()`: Get the global connector factory instance

## Usage

### Initializing Connectors

```python
from sql_agent.backend.db.connectors.init_connectors import init_db_connectors

# Initialize database connectors
init_db_connectors()
```

### Creating and Using a Connector

```python
from sql_agent.backend.models.database import Database
from sql_agent.backend.db.connectors.init_connectors import get_connector_factory

# Get the connector factory
factory = get_connector_factory()

# Create a connector for a database
connector = factory.create_connector(db_config)

# Test the connection
success, message = connector.test_connection(db_config)

# Get the database schema
schema = connector.get_schema(db_config)

# Execute a query
result = connector.execute_query(db_config, "SELECT * FROM users", max_rows=100)

# Process the results
for row in result.rows:
    print(row)
```

### Implementing a New Connector

To add support for a new database type:

1. Create a new file for the connector implementation (e.g., `oracle.py`)
2. Implement the `DBConnector` interface
3. Register the connector in `init_connectors.py`

Example:

```python
from sql_agent.backend.db.connectors.base import DBConnector

class OracleConnector(DBConnector):
    # Implement the required methods
    ...

# In init_connectors.py
from sql_agent.backend.db.connectors.oracle import OracleConnector

def init_db_connectors():
    ...
    connector_factory.register_connector("oracle", OracleConnector)
```

## Features

- Connection pooling for efficient resource usage
- Query execution with timeout and row limit
- Query cancellation
- Schema discovery
- SQL validation for security
- Standardized error handling
- Support for multiple database types

## Implementation Notes

- All connectors use a common interface for consistency
- Connection pooling improves performance and resource usage
- SQL validation prevents SQL injection and ensures read-only operations
- Error handling is standardized across all connectors
- The factory pattern allows for easy extension with new database types
