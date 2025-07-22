"""
Unit tests for the base database connector.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.models.database import Database, DBType, ConnectionConfig
from backend.db.connectors.base import DBConnector
from backend.models.query import QueryResult

class TestBaseConnector(unittest.TestCase):
    """
    Tests for the base database connector.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create a mock connection pool manager
        self.pool_manager = MagicMock()
        
        # Create a concrete implementation of the abstract base class for testing
        class ConcreteDBConnector(DBConnector):
            def __init__(self, connection_pool_manager):
                super().__init__(connection_pool_manager)
            
            def test_connection(self, db_config):
                return True, "Connected"
            
            def _execute_query_impl(self, db_config, query, params=None, timeout=None, max_rows=None):
                result = MagicMock(spec=QueryResult)
                result.query_id = "test-query-id"
                return result
            
            def cancel_query(self, query_id):
                return True
            
            def get_schema(self, db_config):
                return MagicMock()
            
            def validate_query(self, db_config, query):
                return True, None
            
            def is_read_only_query(self, query):
                return True
        
        # Create an instance of the concrete connector
        self.connector = ConcreteDBConnector(self.pool_manager)
        
        # Create a mock database configuration
        self.db_config = Database(
            id="test-db",
            name="Test Database",
            type=DBType.MSSQL,
            host="db-server",
            port=1433,
            default_schema="dbo",
            connection_config=ConnectionConfig(
                username="testuser",
                password_encrypted="encrypted_password",
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @patch('sql_agent.backend.db.connectors.sql_converter.SQLConverter.auto_convert')
    def test_execute_query_with_auto_convert(self, mock_auto_convert):
        """
        Test executing a query with automatic SQL conversion.
        """
        # Set up the mock auto_convert to return a converted query
        original_query = "SELECT TOP 10 * FROM Products"
        converted_query = "SELECT * FROM Products LIMIT 10"
        mock_auto_convert.return_value = (converted_query, ["Query converted"])
        
        # Call the method
        result = self.connector.execute_query(self.db_config, original_query)
        
        # Verify auto_convert was called
        mock_auto_convert.assert_called_once_with(original_query, self.db_config)
        
        # Verify _execute_query_impl was called with the converted query
        self.assertEqual(result.query_id, "test-query-id")
    
    @patch('sql_agent.backend.db.connectors.sql_converter.SQLConverter.auto_convert')
    def test_execute_query_without_auto_convert(self, mock_auto_convert):
        """
        Test executing a query without automatic SQL conversion.
        """
        # Set up the query
        query = "SELECT * FROM Products"
        
        # Call the method with auto_convert=False
        result = self.connector.execute_query(self.db_config, query, auto_convert=False)
        
        # Verify auto_convert was not called
        mock_auto_convert.assert_not_called()
        
        # Verify _execute_query_impl was called with the original query
        self.assertEqual(result.query_id, "test-query-id")
    
    @patch('sql_agent.backend.db.connectors.sql_converter.SQLConverter.auto_convert')
    def test_execute_query_no_conversion_needed(self, mock_auto_convert):
        """
        Test executing a query that doesn't need conversion.
        """
        # Set up the mock auto_convert to return the original query
        query = "SELECT * FROM Products"
        mock_auto_convert.return_value = (query, [])
        
        # Call the method
        result = self.connector.execute_query(self.db_config, query)
        
        # Verify auto_convert was called
        mock_auto_convert.assert_called_once_with(query, self.db_config)
        
        # Verify _execute_query_impl was called with the original query
        self.assertEqual(result.query_id, "test-query-id")

if __name__ == "__main__":
    unittest.main()