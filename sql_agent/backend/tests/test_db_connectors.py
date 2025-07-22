"""
Tests for the database connector interface.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from sql_agent.backend.models.database import Database, DBType, ConnectionConfig
from sql_agent.backend.db.connectors.base import DBConnector, ConnectionPoolManager
from sql_agent.backend.db.connectors.pool import DefaultConnectionPoolManager
from sql_agent.backend.db.connectors.factory import DBConnectorFactory
from sql_agent.backend.db.connectors.sql_validator import SQLValidator

class TestSQLValidator(unittest.TestCase):
    """
    Tests for the SQL validator.
    """
    
    def test_is_read_only_query(self):
        """
        Test the is_read_only_query method.
        """
        validator = SQLValidator()
        
        # Test read-only queries
        self.assertTrue(validator.is_read_only_query("SELECT * FROM users"))
        self.assertTrue(validator.is_read_only_query("SELECT id, name FROM users WHERE id = 1"))
        self.assertTrue(validator.is_read_only_query("SHOW TABLES"))
        self.assertTrue(validator.is_read_only_query("DESCRIBE users"))
        self.assertTrue(validator.is_read_only_query("EXPLAIN SELECT * FROM users"))
        
        # Test non-read-only queries
        self.assertFalse(validator.is_read_only_query("INSERT INTO users (name) VALUES ('John')"))
        self.assertFalse(validator.is_read_only_query("UPDATE users SET name = 'John' WHERE id = 1"))
        self.assertFalse(validator.is_read_only_query("DELETE FROM users WHERE id = 1"))
        self.assertFalse(validator.is_read_only_query("DROP TABLE users"))
        self.assertFalse(validator.is_read_only_query("CREATE TABLE users (id INT, name VARCHAR(255))"))
        self.assertFalse(validator.is_read_only_query("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
        
        # Test edge cases
        self.assertFalse(validator.is_read_only_query(""))  # Empty query
        self.assertFalse(validator.is_read_only_query("   "))  # Whitespace only
        self.assertFalse(validator.is_read_only_query("-- This is a comment"))  # Comment only
    
    def test_validate_query(self):
        """
        Test the validate_query method.
        """
        validator = SQLValidator()
        
        # Test valid queries
        valid, error = validator.validate_query("SELECT * FROM users")
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        valid, error = validator.validate_query("SELECT id, name FROM users WHERE id = 1")
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Test invalid queries
        valid, error = validator.validate_query("")
        self.assertFalse(valid)
        self.assertEqual(error, "Query is empty")
        
        valid, error = validator.validate_query("SELECT * FROM users; DROP TABLE users")
        self.assertFalse(valid)
        self.assertEqual(error, "Multiple SQL statements are not allowed")
        
        valid, error = validator.validate_query("INSERT INTO users (name) VALUES ('John')")
        self.assertFalse(valid)
        self.assertEqual(error, "Only read-only queries are allowed")
        
        valid, error = validator.validate_query("SELECT * FROM users; --DROP TABLE users")
        self.assertFalse(valid)
        self.assertEqual(error, "Multiple SQL statements are not allowed")

class TestConnectionPoolManager(unittest.TestCase):
    """
    Tests for the connection pool manager.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.pool_manager = DefaultConnectionPoolManager(max_pool_size=5)
        
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
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Register a mock connection creator
        self.mock_connection = MagicMock()
        self.pool_manager.register_connection_creator(
            "mssql",
            lambda db_config: self.mock_connection
        )
        
        # Register a mock connection validator
        self.pool_manager.register_connection_validator(
            "mssql",
            lambda conn: True
        )
    
    def test_get_connection(self):
        """
        Test getting a connection from the pool.
        """
        # Get a connection
        connection = self.pool_manager.get_connection(self.db_config)
        
        # Verify that the connection is the mock connection
        self.assertEqual(connection, self.mock_connection)
        
        # Verify that the pool has one connection
        stats = self.pool_manager.get_pool_stats(self.db_config.id)
        self.assertEqual(stats[self.db_config.id]["total_connections"], 1)
        self.assertEqual(stats[self.db_config.id]["active_connections"], 1)
    
    def test_release_connection(self):
        """
        Test releasing a connection back to the pool.
        """
        # Get a connection
        connection = self.pool_manager.get_connection(self.db_config)
        
        # Verify that the connection is in use
        stats = self.pool_manager.get_pool_stats(self.db_config.id)
        self.assertEqual(stats[self.db_config.id]["active_connections"], 1)
        
        # Release the connection
        self.pool_manager.release_connection(connection, self.db_config.id)
        
        # Verify that the connection is no longer in use
        stats = self.pool_manager.get_pool_stats(self.db_config.id)
        self.assertEqual(stats[self.db_config.id]["active_connections"], 0)
        self.assertEqual(stats[self.db_config.id]["idle_connections"], 1)
    
    def test_close_all_connections(self):
        """
        Test closing all connections.
        """
        # Get a connection
        connection = self.pool_manager.get_connection(self.db_config)
        
        # Close all connections
        self.pool_manager.close_all_connections()
        
        # Verify that the pool is empty
        stats = self.pool_manager.get_pool_stats(self.db_config.id)
        self.assertEqual(stats[self.db_config.id]["total_connections"], 0)
        
        # Verify that the connection was closed
        self.mock_connection.close.assert_called_once()

class TestDBConnectorFactory(unittest.TestCase):
    """
    Tests for the database connector factory.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.factory = DBConnectorFactory()
        
        # Create a mock connector class
        self.MockConnector = MagicMock(spec=DBConnector)
        self.MockConnector.return_value = MagicMock(spec=DBConnector)
        
        # Register the mock connector
        self.factory.register_connector("mssql", self.MockConnector)
        
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
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_create_connector(self):
        """
        Test creating a connector.
        """
        # Create a connector
        connector = self.factory.create_connector(self.db_config)
        
        # Verify that the connector was created with the correct pool manager
        self.MockConnector.assert_called_once()
        self.assertEqual(connector, self.MockConnector.return_value)
    
    def test_create_connector_unknown_type(self):
        """
        Test creating a connector for an unknown database type.
        """
        # Create a database configuration with an unknown type
        db_config = Database(
            id="test-db",
            name="Test Database",
            type=DBType.HANA,  # Not registered
            host="localhost",
            port=1433,
            default_schema="master",
            connection_config=ConnectionConfig(
                username="sa",
                password_encrypted="encrypted_password",
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Verify that creating a connector raises an exception
        with self.assertRaises(ValueError):
            self.factory.create_connector(db_config)

if __name__ == "__main__":
    unittest.main()