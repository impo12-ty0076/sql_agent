"""
Unit tests for the SAP HANA database connector.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.models.database import Database, DBType, ConnectionConfig
from backend.db.connectors.hana import HANAConnector
from backend.db.connectors.pool import DefaultConnectionPoolManager
from backend.models.query import QueryResult, ResultColumn

class TestHANAConnector(unittest.TestCase):
    """
    Tests for the SAP HANA connector.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a mock connection pool manager
        self.pool_manager = MagicMock(spec=DefaultConnectionPoolManager)
        
        # Create the connector with the mock pool manager
        self.connector = HANAConnector(self.pool_manager)
        
        # Create a mock database configuration
        self.db_config = Database(
            id="test-hana-db",
            name="Test HANA Database",
            type=DBType.HANA,
            host="hana-server",
            port=30015,
            default_schema="TESTDB",
            connection_config=ConnectionConfig(
                username="TESTUSER",
                password_encrypted="encrypted_password",
                options={"timeout": 30, "compress": True}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock the UUID generation to get predictable query IDs
        self.uuid_patch = patch('uuid.uuid4')
        self.mock_uuid = self.uuid_patch.start()
        self.mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    
    def tearDown(self):
        """
        Clean up test fixtures.
        """
        self.uuid_patch.stop()
    
    @patch('sql_agent.backend.db.connectors.hana.hana_dbapi', create=True)
    def test_create_connection(self, mock_hana_dbapi):
        """
        Test creating a connection using hdbcli.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_hana_dbapi.connect.return_value = mock_connection
        
        # Call the method
        connection = self.connector._create_connection(self.db_config)
        
        # Verify the connection was created with the correct parameters
        mock_hana_dbapi.connect.assert_called_once_with(
            address="hana-server",
            port=30015,
            user="TESTUSER",
            password="encrypted_password",
            databaseName="TESTDB",
            autocommit=True,
            timeout=30,
            reconnect=True,
            packetSize=1048576,
            compress=True,
            communicationTimeout=0,
            connectTimeout=30000
        )
        
        # Verify the connection settings were configured
        self.assertEqual(mock_cursor.execute.call_count, 3)
        mock_cursor.execute.assert_has_calls([
            call("SET SESSION 'QUERY_TIMEOUT' = '300'"),
            call("SET SESSION 'IDLE_TIMEOUT' = '1800'"),
            call("SET SESSION 'ABAP_AS_DECIMAL' = 'TRUE'")
        ])
        
        # Verify the cursor was closed
        mock_cursor.close.assert_called_once()
        
        # Verify the connection was returned
        self.assertEqual(connection, mock_connection)
    
    def test_create_connection_no_driver(self):
        """
        Test creating a connection when driver is not available.
        """
        # Temporarily set the driver to None
        original_driver = self.connector.__class__.__dict__.get('HANA_DRIVER')
        with patch('sql_agent.backend.db.connectors.hana.HANA_DRIVER', None):
            # Call the method and expect an exception
            with self.assertRaises(RuntimeError) as context:
                self.connector._create_connection(self.db_config)
            
            # Verify the error message
            self.assertIn("SAP HANA driver (hdbcli) is not available", str(context.exception))
    
    def test_validate_connection(self):
        """
        Test validating a connection.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Call the method
        result = self.connector._validate_connection(mock_connection)
        
        # Verify the validation query was executed
        mock_cursor.execute.assert_called_once_with("SELECT 1 FROM SYS.DUMMY")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_validate_connection_failure(self):
        """
        Test validating a connection that fails.
        """
        # Set up the mock connection to raise an exception
        mock_connection = MagicMock()
        mock_connection.cursor.side_effect = Exception("Connection error")
        
        # Call the method
        result = self.connector._validate_connection(mock_connection)
        
        # Verify the result
        self.assertFalse(result)
    
    @patch('sql_agent.backend.db.connectors.hana.HANAConnector._create_connection')
    def test_test_connection(self, mock_create_connection):
        """
        Test testing a connection.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["SAP HANA 2.0.040.00.1553674765"]
        mock_connection.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_connection
        
        # Call the method
        success, message = self.connector.test_connection(self.db_config)
        
        # Verify the connection was created
        mock_create_connection.assert_called_once_with(self.db_config)
        
        # Verify the test query was executed
        mock_cursor.execute.assert_called_once_with("SELECT VERSION FROM SYS.M_DATABASE")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
        
        # Verify the connection was closed
        mock_connection.close.assert_called_once()
        
        # Verify the result
        self.assertTrue(success)
        self.assertIn("Successfully connected to SAP HANA", message)
        self.assertIn("SAP HANA 2.0.040.00.1553674765", message)
    
    @patch('sql_agent.backend.db.connectors.hana.HANAConnector._create_connection')
    def test_test_connection_failure(self, mock_create_connection):
        """
        Test testing a connection that fails.
        """
        # Set up the mock connection to raise an exception
        mock_create_connection.side_effect = Exception("Connection error")
        
        # Call the method
        success, message = self.connector.test_connection(self.db_config)
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn("Connection failed", message)
        self.assertIn("Connection error", message)
    
    @patch('sql_agent.backend.db.connectors.hana.HANAConnector._execute_query_with_retry')
    def test_execute_query_impl(self, mock_execute_query_with_retry):
        """
        Test executing a query implementation.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        
        # Set up the mock result
        mock_result = MagicMock(spec=QueryResult)
        mock_execute_query_with_retry.return_value = mock_result
        
        # Mock the get_connection context manager
        self.connector.get_connection = MagicMock()
        self.connector.get_connection.return_value.__enter__.return_value = mock_connection
        
        # Mock the validate_query method
        self.connector.validate_query = MagicMock(return_value=(True, None))
        
        # Call the method
        query = "SELECT * FROM USERS"
        params = {"user_id": 123}
        timeout = 60
        max_rows = 100
        result = self.connector._execute_query_impl(self.db_config, query, params, timeout, max_rows)
        
        # Verify the query was validated
        self.connector.validate_query.assert_called_once_with(self.db_config, query)
        
        # Verify the query was registered with the tracker
        self.connector.query_tracker.register_query.assert_called_once()
        query_id = self.connector.query_tracker.register_query.call_args[0][0]
        self.assertEqual(query_id, "12345678-1234-5678-1234-567812345678")
        
        # Verify the query was executed
        mock_execute_query_with_retry.assert_called_once_with(
            mock_connection, query, params, timeout, max_rows, query_id
        )
        
        # Verify the query was unregistered
        self.connector.query_tracker.unregister_query.assert_called_once_with(query_id)
        
        # Verify the result was returned
        self.assertEqual(result, mock_result)
    
    def test_execute_query_invalid_query(self):
        """
        Test executing an invalid query.
        """
        # Mock the validate_query method to return invalid
        self.connector.validate_query = MagicMock(return_value=(False, "Invalid query"))
        
        # Call the method
        query = "INSERT INTO USERS (NAME) VALUES ('John')"
        
        # Verify that an exception is raised
        with self.assertRaises(ValueError) as context:
            self.connector._execute_query_impl(self.db_config, query)
        
        # Verify the error message
        self.assertIn("Invalid query", str(context.exception))
    
    def test_execute_query_with_retry(self):
        """
        Test executing a query with retry logic.
        """
        # Set up the mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock result
        mock_result = MagicMock(spec=QueryResult)
        self.connector.query_processor.process_result = MagicMock(return_value=mock_result)
        
        # Call the method
        query = "SELECT * FROM USERS WHERE ID = :user_id"
        params = {"user_id": 123}
        timeout = 60
        max_rows = 100
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._execute_query_with_retry(
            mock_connection, query, params, timeout, max_rows, query_id
        )
        
        # Verify the cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify the timeout was set
        mock_cursor.execute.assert_any_call("SET SESSION 'QUERY_TIMEOUT' = '60'")
        
        # Verify the query was executed with parameters
        mock_cursor.execute.assert_any_call(query, params)
        
        # Verify the result was processed
        self.connector.query_processor.process_result.assert_called_once_with(
            mock_cursor, query, max_rows
        )
        
        # Verify the query ID was set
        self.assertEqual(mock_result.query_id, query_id)
        
        # Verify the cursor was closed
        mock_cursor.close.assert_called_once()
        
        # Verify the result was returned
        self.assertEqual(result, mock_result)
    
    def test_execute_query_with_retry_no_params(self):
        """
        Test executing a query without parameters.
        """
        # Set up the mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock result
        mock_result = MagicMock(spec=QueryResult)
        self.connector.query_processor.process_result = MagicMock(return_value=mock_result)
        
        # Call the method
        query = "SELECT * FROM USERS"
        params = None
        timeout = None
        max_rows = None
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._execute_query_with_retry(
            mock_connection, query, params, timeout, max_rows, query_id
        )
        
        # Verify the cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify the query was executed without parameters
        mock_cursor.execute.assert_called_once_with(query)
        
        # Verify the result was processed
        self.connector.query_processor.process_result.assert_called_once_with(
            mock_cursor, query, max_rows
        )
        
        # Verify the query ID was set
        self.assertEqual(mock_result.query_id, query_id)
        
        # Verify the cursor was closed
        mock_cursor.close.assert_called_once()
        
        # Verify the result was returned
        self.assertEqual(result, mock_result)
    
    def test_is_transient_error(self):
        """
        Test identifying transient errors.
        """
        # Test with error code
        error_with_code = Exception()
        error_with_code.errorcode = 129
        self.assertTrue(self.connector._is_transient_error(error_with_code))
        
        # Test with error message
        error_with_message = Exception("Connection timeout")
        self.assertTrue(self.connector._is_transient_error(error_with_message))
        
        # Test with non-transient error
        non_transient_error = Exception("Syntax error")
        self.assertFalse(self.connector._is_transient_error(non_transient_error))
    
    def test_cancel_query_internal_with_cancel_method(self):
        """
        Test cancelling a query using connection.cancel().
        """
        # Set up the mock connection with cancel method
        mock_connection = MagicMock()
        mock_connection.cancel = MagicMock()
        
        # Call the method
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._cancel_query_internal(mock_connection, query_id)
        
        # Verify the cancel method was called
        mock_connection.cancel.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_cancel_query_internal_without_cancel_method(self):
        """
        Test cancelling a query by closing the connection.
        """
        # Set up the mock connection without cancel method
        mock_connection = MagicMock()
        del mock_connection.cancel  # Remove the cancel method
        
        # Call the method
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._cancel_query_internal(mock_connection, query_id)
        
        # Verify the connection was closed
        mock_connection.close.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_cancel_query_internal_exception(self):
        """
        Test cancelling a query that raises an exception.
        """
        # Set up the mock connection to raise an exception
        mock_connection = MagicMock()
        mock_connection.cancel.side_effect = Exception("Cancel error")
        
        # Call the method
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._cancel_query_internal(mock_connection, query_id)
        
        # Verify the result
        self.assertFalse(result)
    
    def test_cancel_query(self):
        """
        Test cancelling a query.
        """
        # Mock the query tracker
        self.connector.query_tracker.cancel_query = MagicMock(return_value=True)
        
        # Call the method
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector.cancel_query(query_id)
        
        # Verify the query tracker was called
        self.connector.query_tracker.cancel_query.assert_called_once_with(query_id)
        
        # Verify the result
        self.assertTrue(result)
    
    @patch('sql_agent.backend.db.connectors.hana.HANAConnector.get_connection')
    def test_get_schema(self, mock_get_connection):
        """
        Test getting the database schema.
        """
        # Set up the mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value.__enter__.return_value = mock_connection
        
        # Mock the schema query results
        mock_cursor.fetchall.side_effect = [
            # Schemas
            [("TESTSCHEMA",)],
            # Tables
            [("USERS", "ROW", "User table"), ("ORDERS", "COLUMN", "Order table")],
            # Columns for USERS table
            [
                ("ID", "INTEGER", "FALSE", None, "User ID"),
                ("NAME", "NVARCHAR", "TRUE", None, "User name"),
                ("EMAIL", "NVARCHAR", "FALSE", None, "User email")
            ],
            # Primary key for USERS table
            [("ID",)],
            # Foreign keys for USERS table
            [],
            # Columns for ORDERS table
            [
                ("ORDER_ID", "INTEGER", "FALSE", None, "Order ID"),
                ("USER_ID", "INTEGER", "FALSE", None, "User ID"),
                ("AMOUNT", "DECIMAL", "FALSE", "0", "Order amount")
            ],
            # Primary key for ORDERS table
            [("ORDER_ID",)],
            # Foreign keys for ORDERS table
            [("FK_USER", "USER_ID", "TESTSCHEMA", "USERS", "ID")]
        ]
        
        # Call the method
        schema = self.connector.get_schema(self.db_config)
        
        # Verify the schema structure
        self.assertEqual(schema.db_id, "test-hana-db")
        self.assertEqual(len(schema.schemas), 1)
        
        test_schema = schema.schemas[0]
        self.assertEqual(test_schema.name, "TESTSCHEMA")
        self.assertEqual(len(test_schema.tables), 2)
        
        # Verify USERS table
        users_table = test_schema.tables[0]
        self.assertEqual(users_table.name, "USERS")
        self.assertEqual(users_table.description, "User table")
        self.assertEqual(len(users_table.columns), 3)
        self.assertEqual(users_table.primary_key, ["ID"])
        self.assertEqual(len(users_table.foreign_keys), 0)
        
        # Verify ORDERS table
        orders_table = test_schema.tables[1]
        self.assertEqual(orders_table.name, "ORDERS")
        self.assertEqual(orders_table.description, "Order table")
        self.assertEqual(len(orders_table.columns), 3)
        self.assertEqual(orders_table.primary_key, ["ORDER_ID"])
        self.assertEqual(len(orders_table.foreign_keys), 1)
        
        # Verify foreign key
        fk = orders_table.foreign_keys[0]
        self.assertEqual(fk.columns, ["USER_ID"])
        self.assertEqual(fk.reference_table, "TESTSCHEMA.USERS")
        self.assertEqual(fk.reference_columns, ["ID"])
    
    def test_validate_query(self):
        """
        Test validating a query.
        """
        # Mock the SQL validator
        self.connector.sql_validator.validate_query = MagicMock(return_value=(True, None))
        
        # Call the method
        query = "SELECT * FROM USERS"
        is_valid, error_message = self.connector.validate_query(self.db_config, query)
        
        # Verify the validator was called
        self.connector.sql_validator.validate_query.assert_called_once_with(query)
        
        # Verify the result
        self.assertTrue(is_valid)
        self.assertIsNone(error_message)
    
    def test_is_read_only_query(self):
        """
        Test checking if a query is read-only.
        """
        # Mock the SQL validator
        self.connector.sql_validator.is_read_only_query = MagicMock(return_value=True)
        
        # Call the method
        query = "SELECT * FROM USERS"
        is_read_only = self.connector.is_read_only_query(query)
        
        # Verify the validator was called
        self.connector.sql_validator.is_read_only_query.assert_called_once_with(query)
        
        # Verify the result
        self.assertTrue(is_read_only)
    
    def test_format_error_with_error_code(self):
        """
        Test formatting errors with error codes.
        """
        # Test with authentication error
        error = Exception("Authentication failed")
        error.errorcode = 259
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "Authentication failed: Authentication failed")
        
        # Test with syntax error
        error = Exception("SQL syntax error")
        error.errorcode = 2
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "SQL syntax error: SQL syntax error")
        
        # Test with timeout error
        error = Exception("Request timeout")
        error.errorcode = 7
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "Request timeout: Request timeout")
    
    def test_format_error_without_error_code(self):
        """
        Test formatting errors without error codes.
        """
        # Test with a generic exception
        error = Exception("Something went wrong")
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "Exception: Something went wrong")
    
    def test_format_error_transient(self):
        """
        Test formatting transient errors.
        """
        # Test with a transient error
        error = Exception("Connection timeout")
        error.errorcode = 129
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "Transient error (will retry): Connection timeout")

if __name__ == "__main__":
    unittest.main()