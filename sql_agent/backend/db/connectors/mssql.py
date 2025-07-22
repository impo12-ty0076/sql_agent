"""
MS-SQL database connector implementation.
This module provides a full implementation of the DBConnector interface for MS-SQL Server.
"""

import logging
import time
import uuid
import re
import backoff
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from datetime import datetime
from contextlib import contextmanager

# Import the actual pyodbc or pymssql library
try:
    import pyodbc
    MSSQL_DRIVER = "pyodbc"
except ImportError:
    try:
        import pymssql
        MSSQL_DRIVER = "pymssql"
    except ImportError:
        MSSQL_DRIVER = None

from sql_agent.backend.models.database import Database, DatabaseSchema, Schema, Table, Column, ForeignKey
from sql_agent.backend.models.query import QueryResult, ResultColumn
from sql_agent.backend.db.connectors.base import DBConnector, ConnectionPoolManager
from sql_agent.backend.db.connectors.query_executor import QueryResultProcessor, QueryExecutionTracker
from sql_agent.backend.db.connectors.sql_validator import SQLValidator

logger = logging.getLogger(__name__)

class MSSQLConnector(DBConnector):
    """
    MS-SQL database connector implementation.
    
    This connector provides functionality to:
    - Connect to MS-SQL Server databases
    - Execute queries and process results
    - Retrieve database schema information
    - Validate and check queries
    - Handle errors and implement retry logic
    """
    
    # Maximum number of retry attempts for transient errors
    MAX_RETRY_ATTEMPTS = 3
    
    # Delay between retry attempts (in seconds)
    RETRY_DELAY = 1
    
    # List of error codes that are considered transient and can be retried
    TRANSIENT_ERROR_CODES = {
        # Connection-related errors
        -2, 53, 40143, 40613, 40197, 40501, 40544, 40549, 40550, 40551, 40552, 40553, 40554, 40555, 40556, 40557, 40558, 40559, 40560, 40561, 40562, 40563, 40564, 40565, 40566, 40567, 40568, 40569, 40570, 40571,
        # Query execution errors
        233, 1205, 1222, 1204, 1203, 1211, 1236, 1237
    }
    
    # List of error messages that indicate transient errors
    TRANSIENT_ERROR_MESSAGES = [
        "timeout expired",
        "connection reset",
        "connection forcibly closed",
        "socket closed",
        "transport-level error",
        "communication link failure",
        "resource deadlock",
        "resource timeout",
        "server is busy",
        "database is under recovery",
        "connection is broken"
    ]
    
    def __init__(self, connection_pool_manager: ConnectionPoolManager):
        """
        Initialize the MS-SQL database connector.
        
        Args:
            connection_pool_manager: Connection pool manager instance
        """
        super().__init__(connection_pool_manager)
        self.query_processor = QueryResultProcessor()
        self.sql_validator = SQLValidator()
        self.query_tracker = QueryExecutionTracker()
        
        # Register connection creator and validator with the pool manager
        connection_pool_manager.register_connection_creator("mssql", self._create_connection)
        connection_pool_manager.register_connection_validator("mssql", self._validate_connection)
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Check if an error is transient and can be retried.
        
        Args:
            error: Exception object
            
        Returns:
            True if the error is transient, False otherwise
        """
        error_str = str(error).lower()
        
        # Check for specific error codes
        if hasattr(error, 'args') and len(error.args) > 0:
            if isinstance(error.args[0], int) and error.args[0] in self.TRANSIENT_ERROR_CODES:
                return True
        
        # Check for error messages that indicate transient errors
        for message in self.TRANSIENT_ERROR_MESSAGES:
            if message.lower() in error_str:
                return True
        
        return False
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not MSSQLConnector._is_transient_error(MSSQLConnector, e),
        factor=RETRY_DELAY
    )
    def _create_connection(self, db_config: Database) -> Any:
        """
        Create a new MS-SQL database connection with retry logic for transient errors.
        
        Args:
            db_config: Database configuration
            
        Returns:
            New database connection
            
        Raises:
            RuntimeError: If MS-SQL driver is not available
            Exception: If connection fails after retries
        """
        if MSSQL_DRIVER is None:
            raise RuntimeError("No MS-SQL driver (pyodbc or pymssql) is available")
        
        # Get connection parameters
        host = db_config.host
        port = db_config.port
        database = db_config.default_schema
        username = db_config.connection_config.username
        # In a real implementation, decrypt this password
        password = db_config.connection_config.password_encrypted
        
        try:
            # Create connection based on available driver
            if MSSQL_DRIVER == "pyodbc":
                # Connection string for pyodbc
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password}"
                
                # Add additional connection options
                for key, value in db_config.connection_config.options.items():
                    conn_str += f";{key}={value}"
                
                # Set default connection options if not specified
                if "timeout" not in db_config.connection_config.options:
                    conn_str += ";timeout=30"
                if "encrypt" not in db_config.connection_config.options:
                    conn_str += ";encrypt=yes"
                if "trustservercertificate" not in db_config.connection_config.options:
                    conn_str += ";trustservercertificate=yes"
                
                connection = pyodbc.connect(conn_str)
                
                # Configure connection settings
                cursor = connection.cursor()
                cursor.execute("SET ARITHABORT ON")
                cursor.execute("SET ANSI_NULLS ON")
                cursor.execute("SET ANSI_WARNINGS ON")
                cursor.execute("SET QUOTED_IDENTIFIER ON")
                cursor.execute("SET CONCAT_NULL_YIELDS_NULL ON")
                cursor.close()
                
            else:  # pymssql
                # Default options for pymssql
                options = {
                    "login_timeout": 30,
                    "timeout": 30,
                    "as_dict": False,
                    "autocommit": True
                }
                
                # Update with user-provided options
                options.update(db_config.connection_config.options)
                
                connection = pymssql.connect(
                    server=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    **options
                )
            
            logger.info(f"Created new MS-SQL connection to {host}:{port}/{database}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create MS-SQL connection: {str(e)}")
            # Re-raise the exception to trigger retry if it's a transient error
            raise
    
    def _validate_connection(self, connection: Any) -> bool:
        """
        Validate that a MS-SQL connection is still valid.
        
        Args:
            connection: MS-SQL connection object
            
        Returns:
            True if the connection is valid, False otherwise
        """
        try:
            # Execute a simple query to check if the connection is still valid
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"MS-SQL connection validation failed: {str(e)}")
            return False
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not MSSQLConnector._is_transient_error(MSSQLConnector, e),
        factor=RETRY_DELAY
    )
    def test_connection(self, db_config: Database) -> Tuple[bool, Optional[str]]:
        """
        Test the connection to the MS-SQL database with retry logic.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Create a test connection
            connection = self._create_connection(db_config)
            
            # Execute a simple query to get server version
            cursor = connection.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.close()
            
            # Close the connection
            connection.close()
            
            return True, f"Successfully connected to MS-SQL Server: {version}"
        except Exception as e:
            logger.error(f"Failed to connect to MS-SQL database: {str(e)}")
            return False, f"Connection failed: {str(e)}"
    
    @contextmanager
    def _get_cursor(self, connection: Any, timeout: Optional[int] = None):
        """
        Context manager for getting a cursor with timeout settings.
        
        Args:
            connection: Database connection
            timeout: Optional query timeout in seconds
            
        Yields:
            Database cursor
        """
        cursor = connection.cursor()
        try:
            # Set timeout if specified
            if timeout is not None:
                if MSSQL_DRIVER == "pyodbc":
                    cursor.timeout = timeout
                else:  # pymssql
                    cursor.execute(f"SET QUERY_GOVERNOR_COST_LIMIT {timeout * 1000}")
            
            yield cursor
        finally:
            cursor.close()
    
    def _execute_query_impl(self, db_config: Database, query: str, params: Optional[Dict[str, Any]] = None, 
                          timeout: Optional[int] = None, max_rows: Optional[int] = None) -> QueryResult:
        """
        Implementation of query execution for MS-SQL.
        
        Args:
            db_config: Database configuration
            query: SQL query string
            params: Optional query parameters
            timeout: Optional query timeout in seconds
            max_rows: Optional maximum number of rows to return
            
        Returns:
            QueryResult object containing the query results
            
        Raises:
            ValueError: If the query is not valid
            Exception: If query execution fails after retries
        """
        # Validate the query
        is_valid, error_message = self.validate_query(db_config, query)
        if not is_valid:
            raise ValueError(f"Invalid query: {error_message}")
        
        # Generate a query ID
        query_id = str(uuid.uuid4())
        
        # Get a connection from the pool
        with self.get_connection(db_config) as connection:
            # Register the query with the tracker
            self.query_tracker.register_query(
                query_id, 
                db_config.id, 
                lambda: self._cancel_query_internal(connection, query_id)
            )
            
            try:
                # Execute the query with retry logic for transient errors
                return self._execute_query_with_retry(
                    connection, query, params, timeout, max_rows, query_id
                )
            except Exception as e:
                logger.error(f"Error executing MS-SQL query: {str(e)}")
                raise
            finally:
                # Unregister the query from the tracker
                self.query_tracker.unregister_query(query_id)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not MSSQLConnector._is_transient_error(MSSQLConnector, e),
        factor=RETRY_DELAY
    )
    def _execute_query_with_retry(self, connection: Any, query: str, params: Optional[Dict[str, Any]], 
                                timeout: Optional[int], max_rows: Optional[int], query_id: str) -> QueryResult:
        """
        Execute a SQL query with retry logic for transient errors.
        
        Args:
            connection: Database connection
            query: SQL query string
            params: Optional query parameters
            timeout: Optional query timeout in seconds
            max_rows: Optional maximum number of rows to return
            query_id: Query identifier
            
        Returns:
            QueryResult object containing the query results
        """
        with self._get_cursor(connection, timeout) as cursor:
            # Execute the query
            start_time = time.time()
            
            try:
                if params:
                    # Convert named parameters to positional parameters if using pyodbc
                    if MSSQL_DRIVER == "pyodbc":
                        # Extract parameter names from the query
                        param_names = re.findall(r':(\w+)', query)
                        
                        # Replace named parameters with ? placeholders
                        query_with_placeholders = re.sub(r':(\w+)', '?', query)
                        
                        # Create a list of parameter values in the correct order
                        param_values = [params[name] for name in param_names]
                        
                        cursor.execute(query_with_placeholders, param_values)
                    else:
                        cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Process the results
                result = self.query_processor.process_result(cursor, query, max_rows)
                result.query_id = query_id
                
                execution_time = time.time() - start_time
                logger.info(f"Executed MS-SQL query in {execution_time:.2f}s: {query[:100]}...")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Query execution failed after {execution_time:.2f}s: {str(e)}")
                
                # Check if this is a transient error that can be retried
                if self._is_transient_error(e):
                    logger.info(f"Transient error detected, will retry: {str(e)}")
                    raise  # Re-raise to trigger retry
                else:
                    # Non-transient error, format and raise
                    raise type(e)(self.format_error(e))
    
    def _cancel_query_internal(self, connection: Any, query_id: str) -> bool:
        """
        Internal method to cancel a running query.
        
        Args:
            connection: Database connection
            query_id: Query identifier
            
        Returns:
            True if the query was successfully cancelled, False otherwise
        """
        try:
            # For pyodbc
            if MSSQL_DRIVER == "pyodbc" and hasattr(connection, 'cancel'):
                connection.cancel()
                logger.info(f"Cancelled MS-SQL query {query_id}")
                return True
            
            # For pymssql or if pyodbc cancel is not available
            # We need to use a separate connection to kill the query
            # This requires the session ID (SPID) which we don't have here
            # In a real implementation, you would store the SPID when starting the query
            logger.warning(f"Direct query cancellation not supported for {MSSQL_DRIVER}")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling MS-SQL query {query_id}: {str(e)}")
            return False
    
    def cancel_query(self, query_id: str) -> bool:
        """
        Cancel a running query.
        
        Args:
            query_id: Query identifier
            
        Returns:
            True if the query was successfully cancelled, False otherwise
        """
        return self.query_tracker.cancel_query(query_id)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not MSSQLConnector._is_transient_error(MSSQLConnector, e),
        factor=RETRY_DELAY
    )
    def get_schema(self, db_config: Database) -> DatabaseSchema:
        """
        Get the MS-SQL database schema with retry logic for transient errors.
        
        Args:
            db_config: Database configuration
            
        Returns:
            DatabaseSchema object containing the database schema
        """
        schemas = []
        
        with self.get_connection(db_config) as connection:
            with self._get_cursor(connection) as cursor:
                # Get all schemas
                cursor.execute("""
                    SELECT SCHEMA_NAME
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    ORDER BY SCHEMA_NAME
                """)
                
                schema_names = [row[0] for row in cursor.fetchall()]
                
                # Process each schema
                for schema_name in schema_names:
                    tables = []
                    
                    # Get tables in the schema
                    cursor.execute("""
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = ?
                        ORDER BY TABLE_NAME
                    """, (schema_name,))
                    
                    table_names = [row[0] for row in cursor.fetchall()]
                    
                    # Process each table
                    for table_name in table_names:
                        columns = []
                        
                        # Get columns in the table with additional metadata
                        cursor.execute("""
                            SELECT 
                                C.COLUMN_NAME, 
                                C.DATA_TYPE, 
                                C.IS_NULLABLE,
                                C.COLUMN_DEFAULT,
                                EP.value AS DESCRIPTION
                            FROM INFORMATION_SCHEMA.COLUMNS C
                            LEFT JOIN sys.columns SC ON SC.name = C.COLUMN_NAME
                                AND SC.object_id = OBJECT_ID(CONCAT(C.TABLE_SCHEMA, '.', C.TABLE_NAME))
                            LEFT JOIN sys.extended_properties EP ON EP.major_id = SC.object_id
                                AND EP.minor_id = SC.column_id
                                AND EP.name = 'MS_Description'
                            WHERE C.TABLE_SCHEMA = ? AND C.TABLE_NAME = ?
                            ORDER BY C.ORDINAL_POSITION
                        """, (schema_name, table_name))
                        
                        for col_row in cursor.fetchall():
                            col_name = col_row[0]
                            col_type = col_row[1]
                            col_nullable = col_row[2] == 'YES'
                            col_default = col_row[3]
                            col_description = col_row[4]
                            
                            columns.append(Column(
                                name=col_name,
                                type=col_type,
                                nullable=col_nullable,
                                default_value=col_default,
                                description=col_description
                            ))
                        
                        # Get primary key columns
                        cursor.execute("""
                            SELECT COLUMN_NAME
                            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                                AND CONSTRAINT_NAME IN (
                                    SELECT CONSTRAINT_NAME
                                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                                        AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                                )
                            ORDER BY ORDINAL_POSITION
                        """, (schema_name, table_name, schema_name, table_name))
                        
                        primary_key = [row[0] for row in cursor.fetchall()]
                        
                        # Get foreign keys
                        cursor.execute("""
                            SELECT
                                KCU1.CONSTRAINT_NAME,
                                KCU1.COLUMN_NAME,
                                KCU2.TABLE_SCHEMA,
                                KCU2.TABLE_NAME,
                                KCU2.COLUMN_NAME
                            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS RC
                            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU1
                                ON KCU1.CONSTRAINT_CATALOG = RC.CONSTRAINT_CATALOG
                                AND KCU1.CONSTRAINT_SCHEMA = RC.CONSTRAINT_SCHEMA
                                AND KCU1.CONSTRAINT_NAME = RC.CONSTRAINT_NAME
                            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU2
                                ON KCU2.CONSTRAINT_CATALOG = RC.UNIQUE_CONSTRAINT_CATALOG
                                AND KCU2.CONSTRAINT_SCHEMA = RC.UNIQUE_CONSTRAINT_SCHEMA
                                AND KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME
                                AND KCU2.ORDINAL_POSITION = KCU1.ORDINAL_POSITION
                            WHERE KCU1.TABLE_SCHEMA = ? AND KCU1.TABLE_NAME = ?
                            ORDER BY KCU1.CONSTRAINT_NAME, KCU1.ORDINAL_POSITION
                        """, (schema_name, table_name))
                        
                        # Group foreign keys by constraint name
                        fk_dict = {}
                        for row in cursor.fetchall():
                            constraint_name = row[0]
                            column_name = row[1]
                            ref_schema = row[2]
                            ref_table = row[3]
                            ref_column = row[4]
                            
                            if constraint_name not in fk_dict:
                                fk_dict[constraint_name] = {
                                    "columns": [],
                                    "reference_table": f"{ref_schema}.{ref_table}",
                                    "reference_columns": []
                                }
                            
                            fk_dict[constraint_name]["columns"].append(column_name)
                            fk_dict[constraint_name]["reference_columns"].append(ref_column)
                        
                        foreign_keys = [
                            ForeignKey(
                                columns=fk["columns"],
                                reference_table=fk["reference_table"],
                                reference_columns=fk["reference_columns"]
                            )
                            for fk in fk_dict.values()
                        ]
                        
                        # Get table description
                        cursor.execute("""
                            SELECT EP.value AS DESCRIPTION
                            FROM sys.tables T
                            LEFT JOIN sys.extended_properties EP ON EP.major_id = T.object_id
                                AND EP.minor_id = 0
                                AND EP.name = 'MS_Description'
                            WHERE T.schema_id = SCHEMA_ID(?) AND T.name = ?
                        """, (schema_name, table_name))
                        
                        table_description = None
                        result = cursor.fetchone()
                        if result:
                            table_description = result[0]
                        
                        # Create the table object
                        tables.append(Table(
                            name=table_name,
                            columns=columns,
                            primary_key=primary_key,
                            foreign_keys=foreign_keys,
                            description=table_description
                        ))
                    
                    # Create the schema object
                    schemas.append(Schema(
                        name=schema_name,
                        tables=tables
                    ))
        
        # Create the database schema object
        return DatabaseSchema(
            db_id=db_config.id,
            schemas=schemas,
            last_updated=datetime.now()
        )
    
    def validate_query(self, db_config: Database, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query without executing it.
        
        Args:
            db_config: Database configuration
            query: SQL query string
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Use the SQL validator to check if the query is valid
        return self.sql_validator.validate_query(query)
    
    def is_read_only_query(self, query: str) -> bool:
        """
        Check if a query is read-only (SELECT, SHOW, DESCRIBE, etc.).
        
        Args:
            query: SQL query string
            
        Returns:
            True if the query is read-only, False otherwise
        """
        # Use the SQL validator to check if the query is read-only
        return self.sql_validator.is_read_only_query(query)
    
    def format_error(self, error: Exception) -> str:
        """
        Format an exception into a user-friendly error message.
        
        Args:
            error: Exception object
            
        Returns:
            Formatted error message
        """
        error_message = str(error)
        
        # Extract error code if available
        error_code = None
        if hasattr(error, 'args') and len(error.args) > 0 and isinstance(error.args[0], int):
            error_code = error.args[0]
        
        # Format based on error type and code
        if MSSQL_DRIVER == "pyodbc":
            if isinstance(error, pyodbc.ProgrammingError):
                return f"SQL syntax error: {error_message}"
            elif isinstance(error, pyodbc.DataError):
                return f"Data error: {error_message}"
            elif isinstance(error, pyodbc.IntegrityError):
                return f"Integrity constraint violation: {error_message}"
            elif isinstance(error, pyodbc.OperationalError):
                if self._is_transient_error(error):
                    return f"Transient error (will retry): {error_message}"
                return f"Database operational error: {error_message}"
        elif MSSQL_DRIVER == "pymssql":
            if error_code:
                return f"MS-SQL error {error_code}: {error_message}"
        
        # Default formatting
        return f"{type(error).__name__}: {error_message}"