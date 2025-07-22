import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from ..services.database import DatabaseService

# Mock database data
mock_databases = [
    {
        "id": "db1",
        "name": "Test MS-SQL DB",
        "type": "mssql",
        "host": "localhost",
        "port": 1433,
        "default_schema": "dbo",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    },
    {
        "id": "db2",
        "name": "Test SAP HANA DB",
        "type": "hana",
        "host": "localhost",
        "port": 30015,
        "default_schema": "SYSTEM",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
]

# Mock connection data
mock_connection = {
    "status": "connected",
    "db_id": "db1",
    "connection_id": "conn_test_123",
    "connected_at": datetime.now().isoformat(),
}

# Mock schema data
mock_schema = {
    "db_id": "db1",
    "schemas": [
        {
            "name": "sales",
            "tables": [
                {
                    "name": "customers",
                    "columns": [
                        {"name": "customer_id", "type": "int", "nullable": False},
                        {"name": "name", "type": "varchar(100)", "nullable": False},
                        {"name": "email", "type": "varchar(100)", "nullable": True},
                    ],
                    "primary_key": ["customer_id"],
                    "foreign_keys": [],
                    "description": "Customer information"
                }
            ]
        }
    ],
    "last_updated": datetime.now().isoformat()
}

# Mock disconnection data
mock_disconnection = {
    "status": "disconnected",
    "connection_id": "conn_test_123",
    "disconnected_at": datetime.now().isoformat(),
}

class TestDatabaseAPI:
    """Tests for the database API endpoints"""
    
    @patch("sql_agent.backend.services.auth.get_current_user")
    @patch.object(DatabaseService, "get_user_databases")
    def test_list_databases(self, mock_get_dbs, mock_get_user, client, test_user, auth_token):
        """Test listing databases"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_get_dbs.return_value = mock_databases
        
        # Make request
        response = client.get("/api/db/list", headers={"Authorization": f"Bearer {auth_token}"})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "db1"
        assert data[1]["id"] == "db2"
        
        # Verify mocks called correctly
        mock_get_user.assert_called_once()
        mock_get_dbs.assert_called_once_with(test_user.id)
    
    @patch("sql_agent.backend.services.auth.get_current_user")
    @patch.object(DatabaseService, "connect_database")
    def test_connect_database(self, mock_connect, mock_get_user, client, test_user, auth_token):
        """Test connecting to a database"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_connect.return_value = mock_connection
        
        # Make request
        response = client.post(
            "/api/db/connect",
            json={"db_id": "db1"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["db_id"] == "db1"
        assert "connection_id" in data
        
        # Verify mocks called correctly
        mock_get_user.assert_called_once()
        mock_connect.assert_called_once_with("db1", test_user.id)
    
    @patch("sql_agent.backend.services.auth.get_current_user")
    @patch.object(DatabaseService, "get_database_schema")
    def test_get_database_schema(self, mock_get_schema, mock_get_user, client, test_user, auth_token):
        """Test getting database schema"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_get_schema.return_value = mock_schema
        
        # Make request
        response = client.get(
            "/api/db/schema?db_id=db1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["db_id"] == "db1"
        assert len(data["schemas"]) == 1
        assert data["schemas"][0]["name"] == "sales"
        assert len(data["schemas"][0]["tables"]) == 1
        assert data["schemas"][0]["tables"][0]["name"] == "customers"
        
        # Verify mocks called correctly
        mock_get_user.assert_called_once()
        mock_get_schema.assert_called_once_with("db1", test_user.id)
    
    @patch("sql_agent.backend.services.auth.get_current_user")
    @patch.object(DatabaseService, "disconnect_database")
    def test_disconnect_database(self, mock_disconnect, mock_get_user, client, test_user, auth_token):
        """Test disconnecting from a database"""
        # Setup mocks
        mock_get_user.return_value = test_user
        mock_disconnect.return_value = mock_disconnection
        
        # Make request
        response = client.post(
            "/api/db/disconnect",
            json={"connection_id": "conn_test_123"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
        assert data["connection_id"] == "conn_test_123"
        
        # Verify mocks called correctly
        mock_get_user.assert_called_once()
        mock_disconnect.assert_called_once_with("conn_test_123", test_user.id)