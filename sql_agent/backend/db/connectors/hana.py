"""
SAP HANA database connector implementation.
This module provides a full implementation of the DBConnector interface for SAP HANA.
"""

import logging
import time
import uuid
import re
import backoff
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from datetime import datetime
from contextlib import contextmanager

# Import the SAP HANA database client library
try:
    import hdbcli.dbapi as hana_dbapi
    HANA_DRIVER = "hdbcli"
except ImportError:
    HANA_DRIVER = None

from sql_agent.backend.models.database import Database, DatabaseSchema, Schema, Table, Column, ForeignKey
from sql_agent.backend.models.query import QueryResult, ResultColumn
from sql_agent.backend.db.connectors.base import DBConnector, ConnectionPoolManager
from sql_agent.backend.db.connectors.query_executor import QueryResultProcessor, QueryExecutionTracker
from sql_agent.backend.db.connectors.sql_validator import SQLValidator

logger = logging.getLogger(__name__)

class HANAConnector(DBConnector):
    """
    SAP HANA database connector implementation.
    
    This connector provides functionality to:
    - Connect to SAP HANA databases
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
        -10709,  # Connection failed (RTE:[300015])
        -10108,  # Session not connected
        -10104,  # Invalid session ID
        -10103,  # Session not found
        -10102,  # Session already closed
        -10101,  # Session limit exceeded
        -10100,  # Session timeout
        -10061,  # Connection refused
        -10060,  # Connection timeout
        -10054,  # Connection reset by peer
        -10053,  # Software caused connection abort
        -10048,  # Address already in use
        -10047,  # Address family not supported
        -10046,  # Protocol family not supported
        -10045,  # Operation not supported
        -10044,  # Socket type not supported
        -10043,  # Protocol not supported
        -10042,  # Protocol wrong type for socket
        -10041,  # Protocol not available
        -10040,  # Too many processes
        -10039,  # Directory not empty
        -10038,  # Function not implemented
        -10037,  # No locks available
        -10036,  # Resource deadlock avoided
        -10035,  # Resource temporarily unavailable
        -10034,  # Numerical result out of range
        -10033,  # Numerical argument out of domain
        -10032,  # Broken pipe
        -10031,  # Too many links
        -10030,  # Read-only file system
        -10029,  # Illegal seek
        -10028,  # No space left on device
        -10027,  # File too large
        -10026,  # Text file busy
        -10025,  # Inappropriate ioctl for device
        -10024,  # Too many open files
        -10023,  # File table overflow
        -10022,  # Invalid argument
        -10021,  # Is a directory
        -10020,  # Not a directory
        -10019,  # No such device
        -10018,  # Cross-device link
        -10017,  # File exists
        -10016,  # Device or resource busy
        -10015,  # Block device required
        -10014,  # Bad address
        -10013,  # Permission denied
        -10012,  # Cannot allocate memory
        -10011,  # Resource temporarily unavailable
        -10010,  # No child processes
        -10009,  # Bad file descriptor
        -10008,  # Exec format error
        -10007,  # Argument list too long
        -10006,  # No such device or address
        -10005,  # Input/output error
        -10004,  # Interrupted system call
        -10003,  # No such process
        -10002,  # No such file or directory
        -10001,  # Operation not permitted
        # Query execution errors
        129,     # Transaction rolled back by lock wait timeout
        131,     # Transaction rolled back by deadlock detection
        146,     # Resource container limit exceeded
        1205,    # Lock wait timeout
        1213,    # Deadlock found when trying to get lock
        # HANA specific error codes
        2,       # SQL syntax error
        7,       # Request timeout
        10,      # Feature not supported
        258,     # Insufficient privilege
        259,     # Invalid user name or password
        414,     # Invalid table name
        423,     # Lock wait timeout exceeded
        1299,    # Resource limit exceeded
    }
    
    # List of error messages that indicate transient errors
    TRANSIENT_ERROR_MESSAGES = [
        "connection failed",
        "connection timeout",
        "connection reset",
        "connection refused",
        "connection closed",
        "network error",
        "socket error",
        "timeout expired",
        "lock wait timeout",
        "deadlock",
        "resource limit",
        "server busy",
        "temporary failure",
        "retry later",
        "service unavailable",
        "communication link failure",
        "transport-level error"
    ]
    
    def __init__(self, connection_pool_manager: ConnectionPoolManager):
        """
        Initialize the SAP HANA database connector.
        
        Args:
            connection_pool_manager: Connection pool manager instance
        """
        super().__init__(connection_pool_manager)
        self.query_processor = QueryResultProcessor()
        self.sql_validator = SQLValidator()
        self.query_tracker = QueryExecutionTracker()
        
        # Register connection creator and validator with the pool manager
        connection_pool_manager.register_connection_creator("hana", self._create_connection)
        connection_pool_manager.register_connection_validator("hana", self._validate_connection)
    
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
        if hasattr(error, 'errorcode') and error.errorcode in self.TRANSIENT_ERROR_CODES:
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
        giveup=lambda e: not isinstance(e, Exception) or not HANAConnector._is_transient_error(HANAConnector, e),
        factor=RETRY_DELAY
    )
    def _create_connection(self, db_config: Database) -> Any:
        """
        Create a new SAP HANA database connection with retry logic for transient errors.
        
        Args:
            db_config: Database configuration
            
        Returns:
            New database connection
            
        Raises:
            RuntimeError: If SAP HANA driver is not available
            Exception: If connection fails after retries
        """
        if HANA_DRIVER is None:
            raise RuntimeError("SAP HANA driver (hdbcli) is not available")
        
        # Get connection parameters
        host = db_config.host
        port = db_config.port
        database = db_config.default_schema
        username = db_config.connection_config.username
        # In a real implementation, decrypt this password
        password = db_config.connection_config.password_encrypted
        
        try:
            # Default connection options
            options = {
                "autocommit": True,
                "timeout": 30,
                "reconnect": True,
                "packetSize": 1048576,  # 1MB packet size
                "compress": True,
                "communicationTimeout": 0,  # No timeout for communication
                "connectTimeout": 30000,  # 30 seconds connection timeout
            }
            
            # Update with user-provided options
            options.update(db_config.connection_config.options)
            
            # Create connection
            connection = hana_dbapi.connect(
                address=host,
                port=port,
                user=username,
                password=password,
                databaseName=database,
                **options
            )
            
            # Configure connection settings
            cursor = connection.cursor()
            
            # Set session parameters for optimal performance
            cursor.execute("SET SESSION 'QUERY_TIMEOUT' = '300'")  # 5 minutes query timeout
            cursor.execute("SET SESSION 'IDLE_TIMEOUT' = '1800'")  # 30 minutes idle timeout
            cursor.execute("SET SESSION 'ABAP_AS_DECIMAL' = 'TRUE'")  # Handle ABAP decimals correctly
            
            cursor.close()
            
            logger.info(f"Created new SAP HANA connection to {host}:{port}/{database}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create SAP HANA connection: {str(e)}")
            # Re-raise the exception to trigger retry if it's a transient error
            raise
    
    def _validate_connection(self, connection: Any) -> bool:
        """
        Validate that a SAP HANA connection is still valid.
        
        Args:
            connection: SAP HANA connection object
            
        Returns:
            True if the connection is valid, False otherwise
        """
        try:
            # Execute a simple query to check if the connection is still valid
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM SYS.DUMMY")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"SAP HANA connection validation failed: {str(e)}")
            return False
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not HANAConnector._is_transient_error(HANAConnector, e),
        factor=RETRY_DELAY
    )
    def test_connection(self, db_config: Database) -> Tuple[bool, Optional[str]]:
        """
        Test the connection to the SAP HANA database with retry logic.
        
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
            cursor.execute("SELECT VERSION FROM SYS.M_DATABASE")
            version = cursor.fetchone()[0]
            cursor.close()
            
            # Close the connection
            connection.close()
            
            return True, f"Successfully connected to SAP HANA: {version}"
        except Exception as e:
            logger.error(f"Failed to connect to SAP HANA database: {str(e)}")
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
                cursor.execute(f"SET SESSION 'QUERY_TIMEOUT' = '{timeout}'")
            
            yield cursor
        finally:
            cursor.close()
    
    def _execute_query_impl(self, db_config: Database, query: str, params: Optional[Dict[str, Any]] = None, 
                          timeout: Optional[int] = None, max_rows: Optional[int] = None) -> QueryResult:
        """
        Implementation of query execution for SAP HANA.
        
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
                logger.error(f"Error executing SAP HANA query: {str(e)}")
                raise
            finally:
                # Unregister the query from the tracker
                self.query_tracker.unregister_query(query_id)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=MAX_RETRY_ATTEMPTS,
        giveup=lambda e: not isinstance(e, Exception) or not HANAConnector._is_transient_error(HANAConnector, e),
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
                    # SAP HANA supports named parameters with :parameter_name syntax
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Process the results
                result = self.query_processor.process_result(cursor, query, max_rows)
                result.query_id = query_id
                
                execution_time = time.time() - start_time
                logger.info(f"Executed SAP HANA query in {execution_time:.2f}s: {query[:100]}...")
                
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
            # SAP HANA supports query cancellation through connection.cancel()
            if hasattr(connection, 'cancel'):
                connection.cancel()
                logger.info(f"Cancelled SAP HANA query {query_id}")
                return True
            else:
                # Alternative method: close the connection to cancel the query
                # This is more drastic but effective
                connection.close()
                logger.info(f"Closed connection to cancel SAP HANA query {query_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error cancelling SAP HANA query {query_id}: {str(e)}")
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
        giveup=lambda e: not isinstance(e, Exception) or not HANAConnector._is_transient_error(HANAConnector, e),
        factor=RETRY_DELAY
    )
    def get_schema(self, db_config: Database) -> DatabaseSchema:
        """
        Get the SAP HANA database schema with retry logic for transient errors.
        
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
                    FROM SYS.SCHEMAS
                    WHERE HAS_PRIVILEGES = 'TRUE'
                    ORDER BY SCHEMA_NAME
                """)
                
                schema_names = [row[0] for row in cursor.fetchall()]
                
                # Process each schema
                for schema_name in schema_names:
                    tables = []
                    
                    # Get tables in the schema
                    cursor.execute("""
                        SELECT TABLE_NAME, TABLE_TYPE, COMMENTS
                        FROM SYS.TABLES
                        WHERE SCHEMA_NAME = ?
                        AND TABLE_TYPE IN ('ROW', 'COLUMN')
                        ORDER BY TABLE_NAME
                    """, (schema_name,))
                    
                    table_rows = cursor.fetchall()
                    
                    # Process each table
                    for table_row in table_rows:
                        table_name = table_row[0]
                        table_type = table_row[1]
                        table_description = table_row[2]
                        
                        columns = []
                        
                        # Get columns in the table
                        cursor.execute("""
                            SELECT 
                                COLUMN_NAME, 
                                DATA_TYPE_NAME,
                                IS_NULLABLE,
                                DEFAULT_VALUE,
                                COMMENTS
                            FROM SYS.TABLE_COLUMNS
                            WHERE SCHEMA_NAME = ? AND TABLE_NAME = ?
                            ORDER BY POSITION
                        """, (schema_name, table_name))
                        
                        for col_row in cursor.fetchall():
                            col_name = col_row[0]
                            col_type = col_row[1]
                            col_nullable = col_row[2] == 'TRUE'
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
                            FROM SYS.CONSTRAINTS C
                            JOIN SYS.CONSTRAINT_COLUMNS CC ON C.CONSTRAINT_NAME = CC.CONSTRAINT_NAME
                                AND C.SCHEMA_NAME = CC.SCHEMA_NAME
                            WHERE C.SCHEMA_NAME = ? AND C.TABLE_NAME = ?
                                AND C.CONSTRAINT_TYPE = 'PRIMARY KEY'
                            ORDER BY CC.POSITION
                        """, (schema_name, table_name))
                        
                        primary_key = [row[0] for row in cursor.fetchall()]
                        
                        # Get foreign keys
                        cursor.execute("""
                            SELECT
                                C.CONSTRAINT_NAME,
                                CC.COLUMN_NAME,
                                C.REFERENCED_SCHEMA_NAME,
                                C.REFERENCED_TABLE_NAME,
                                RC.COLUMN_NAME AS REFERENCED_COLUMN_NAME
                            FROM SYS.REFERENTIAL_CONSTRAINTS C
                            JOIN SYS.CONSTRAINT_COLUMNS CC ON C.CONSTRAINT_NAME = CC.CONSTRAINT_NAME
                                AND C.SCHEMA_NAME = CC.SCHEMA_NAME
                            JOIN SYS.CONSTRAINT_COLUMNS RC ON C.REFERENCED_CONSTRAINT_NAME = RC.CONSTRAINT_NAME
                                AND C.REFERENCED_SCHEMA_NAME = RC.SCHEMA_NAME
                                AND CC.POSITION = RC.POSITION
                            WHERE C.SCHEMA_NAME = ? AND C.TABLE_NAME = ?
                            ORDER BY C.CONSTRAINT_NAME, CC.POSITION
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
        if hasattr(error, 'errorcode'):
            error_code = error.errorcode
        
        # Format based on error type and code
        if HANA_DRIVER == "hdbcli":
            if hasattr(error, 'errorcode'):
                if error_code == 258:
                    return f"Insufficient privileges: {error_message}"
                elif error_code == 259:
                    return f"Authentication failed: {error_message}"
                elif error_code == 414:
                    return f"Invalid table name: {error_message}"
                elif error_code == 423:
                    return f"Lock wait timeout: {error_message}"
                elif error_code == 1299:
                    return f"Resource limit exceeded: {error_message}"
                elif error_code == 2:
                    return f"SQL syntax error: {error_message}"
                elif error_code == 7:
                    return f"Request timeout: {error_message}"
                elif error_code == 10:
                    return f"Feature not supported: {error_message}"
                elif self._is_transient_error(error):
                    return f"Transient error (will retry): {error_message}"
                else:
                    return f"SAP HANA error {error_code}: {error_message}"
        
        # Default formatting
        return f"{type(error).__name__}: {error_message}"