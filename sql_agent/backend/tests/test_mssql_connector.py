"""
Unit tests for the MS-SQL database connector.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
import uuid

from sql_agent.backend.models.database import Database, DBType, ConnectionConfig
from sql_agent.backend.db.connectors.mssql import MSSQLConnector
from sql_agent.backend.db.connectors.pool import DefaultConnectionPoolManager
from sql_agent.backend.models.query import QueryResult, ResultColumn

class TestMSSQLConnector(unittest.TestCase):
    """
    Tests for the MS-SQL connector.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a mock connection pool manager
        self.pool_manager = MagicMock(spec=DefaultConnectionPoolManager)
        
        # Create the connector with the mock pool manager
        self.connector = MSSQLConnector(self.pool_manager)
        
        # Create a mock database configuration
        self.db_config = Database(
            id="test-db",
            name="Test Database",
            type=DBType.MSSQL,
            host="localhost",
            port=1433,
            default_schema="master",
            connection_config=ConnectionConfig(
                username="sa",
                password_encrypted="encrypted_password",
                options={"timeout": 30, "encrypt": True}
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
    
    @patch('sql_agent.backend.db.connectors.mssql.pyodbc', create=True)
    def test_create_connection_pyodbc(self, mock_pyodbc):
        """
        Test creating a connection using pyodbc.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pyodbc.connect.return_value = mock_connection
        
        # Call the method
        connection = self.connector._create_connection(self.db_config)
        
        # Verify the connection was created with the correct parameters
        mock_pyodbc.connect.assert_called_once()
        conn_str = mock_pyodbc.connect.call_args[0][0]
        self.assertIn("SERVER=localhost,1433", conn_str)
        self.assertIn("DATABASE=master", conn_str)
        self.assertIn("UID=sa", conn_str)
        self.assertIn("PWD=encrypted_password", conn_str)
        self.assertIn("timeout=30", conn_str)
        self.assertIn("encrypt=True", conn_str)
        
        # Verify the connection settings were configured
        self.assertEqual(mock_cursor.execute.call_count, 5)
        mock_cursor.execute.assert_has_calls([
            call("SET ARITHABORT ON"),
            call("SET ANSI_NULLS ON"),
            call("SET ANSI_WARNINGS ON"),
            call("SET QUOTED_IDENTIFIER ON"),
            call("SET CONCAT_NULL_YIELDS_NULL ON")
        ])
        
        # Verify the cursor was closed
        mock_cursor.close.assert_called_once()
        
        # Verify the connection was returned
        self.assertEqual(connection, mock_connection)
    
    @patch('sql_agent.backend.db.connectors.mssql.pymssql', create=True)
    @patch('sql_agent.backend.db.connectors.mssql.pyodbc', None)
    def test_create_connection_pymssql(self, mock_pymssql):
        """
        Test creating a connection using pymssql.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        
        # Call the method
        connection = self.connector._create_connection(self.db_config)
        
        # Verify the connection was created with the correct parameters
        mock_pymssql.connect.assert_called_once_with(
            server="localhost",
            port=1433,
            database="master",
            user="sa",
            password="encrypted_password",
            timeout=30,
            encrypt=True,
            login_timeout=30,
            as_dict=False,
            autocommit=True
        )
        
        # Verify the connection was returned
        self.assertEqual(connection, mock_connection)
    
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
        mock_cursor.execute.assert_called_once_with("SELECT 1")
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
    
    @patch('sql_agent.backend.db.connectors.mssql.MSSQLConnector._create_connection')
    def test_test_connection(self, mock_create_connection):
        """
        Test testing a connection.
        """
        # Set up the mock connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["SQL Server 2019"]
        mock_connection.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_connection
        
        # Call the method
        success, message = self.connector.test_connection(self.db_config)
        
        # Verify the connection was created
        mock_create_connection.assert_called_once_with(self.db_config)
        
        # Verify the test query was executed
        mock_cursor.execute.assert_called_once_with("SELECT @@VERSION")
        mock_cursor.fetchone.assert_called_once()
        mock_cursor.close.assert_called_once()
        
        # Verify the connection was closed
        mock_connection.close.assert_called_once()
        
        # Verify the result
        self.assertTrue(success)
        self.assertIn("Successfully connected to MS-SQL Server", message)
        self.assertIn("SQL Server 2019", message)
    
    @patch('sql_agent.backend.db.connectors.mssql.MSSQLConnector._create_connection')
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
    
    @patch('sql_agent.backend.db.connectors.mssql.MSSQLConnector._execute_query_with_retry')
    def test_execute_query(self, mock_execute_query_with_retry):
        """
        Test executing a query.
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
        query = "SELECT * FROM users"
        params = {"user_id": 123}
        timeout = 60
        max_rows = 100
        result = self.connector.execute_query(self.db_config, query, params, timeout, max_rows)
        
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
        query = "INSERT INTO users (name) VALUES ('John')"
        
        # Verify that an exception is raised
        with self.assertRaises(ValueError) as context:
            self.connector.execute_query(self.db_config, query)
        
        # Verify the error message
        self.assertIn("Invalid query", str(context.exception))
    
    @patch('sql_agent.backend.db.connectors.mssql.pyodbc', create=True)
    def test_execute_query_with_retry(self, mock_pyodbc):
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
        query = "SELECT * FROM users WHERE id = :user_id"
        params = {"user_id": 123}
        timeout = 60
        max_rows = 100
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._execute_query_with_retry(
            mock_connection, query, params, timeout, max_rows, query_id
        )
        
        # Verify the cursor was created with the timeout
        mock_connection.cursor.assert_called_once()
        
        # Verify the query was executed with parameters
        # For pyodbc, named parameters should be converted to positional
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = ?", [123])
        
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
    
    @patch('sql_agent.backend.db.connectors.mssql.pymssql', create=True)
    @patch('sql_agent.backend.db.connectors.mssql.pyodbc', None)
    def test_execute_query_with_retry_pymssql(self, mock_pymssql):
        """
        Test executing a query with retry logic using pymssql.
        """
        # Set up the mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Set up the mock result
        mock_result = MagicMock(spec=QueryResult)
        self.connector.query_processor.process_result = MagicMock(return_value=mock_result)
        
        # Call the method
        query = "SELECT * FROM users WHERE id = :user_id"
        params = {"user_id": 123}
        timeout = 60
        max_rows = 100
        query_id = "12345678-1234-5678-1234-567812345678"
        result = self.connector._execute_query_with_retry(
            mock_connection, query, params, timeout, max_rows, query_id
        )
        
        # Verify the cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify the query was executed with parameters
        # For pymssql, named parameters can be used directly
        mock_cursor.execute.assert_called_once_with(query, params)
        
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
        error_with_code.args = (40143, "Transient error message")
        self.assertTrue(self.connector._is_transient_error(error_with_code))
        
        # Test with error message
        error_with_message = Exception("Connection reset by peer")
        self.assertTrue(self.connector._is_transient_error(error_with_message))
        
        # Test with non-transient error
        non_transient_error = Exception("Syntax error")
        self.assertFalse(self.connector._is_transient_error(non_transient_error))
    
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
    
    def test_format_error(self):
        """
        Test formatting errors.
        """
        # Test with a generic exception
        error = Exception("Something went wrong")
        formatted = self.connector.format_error(error)
        self.assertEqual(formatted, "Exception: Something went wrong")
        
        # Test with an error code
        error_with_code = Exception()
        error_with_code.args = (1205, "Transaction deadlock")
        formatted = self.connector.format_error(error_with_code)
        self.assertEqual(formatted, "MS-SQL error 1205: Transaction deadlock")

if __name__ == "__main__":
    unittest.main()