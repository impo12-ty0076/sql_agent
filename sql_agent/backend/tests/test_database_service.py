import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from ..services.database import DatabaseService

class TestDatabaseService:
    """Tests for the DatabaseService class"""
    
    async def test_get_user_databases(self):
        """Test getting databases for a user"""
        # Call the service method
        result = await DatabaseService.get_user_databases("test_user_id")
        
        # Check the result
        assert len(result) == 2
        assert result[0]["id"] == "db1"
        assert result[0]["type"] == "mssql"
        assert result[1]["id"] == "db2"
        assert result[1]["type"] == "hana"
    
    async def test_connect_database_success(self):
        """Test successful database connection"""
        # Call the service method
        result = await DatabaseService.connect_database("db1", "test_user_id")
        
        # Check the result
        assert result["status"] == "connected"
        assert result["db_id"] == "db1"
        assert "connection_id" in result
        assert "connected_at" in result
    
    async def test_connect_database_not_found(self):
        """Test database connection with non-existent database"""
        # Call the service method and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await DatabaseService.connect_database("non_existent_db", "test_user_id")
        
        # Check the exception
        assert excinfo.value.status_code == 404
        assert "not found" in excinfo.value.detail
    
    async def test_get_database_schema_success(self):
        """Test successful schema retrieval"""
        # Call the service method
        result = await DatabaseService.get_database_schema("db1", "test_user_id")
        
        # Check the result
        assert result["db_id"] == "db1"
        assert "schemas" in result
        assert len(result["schemas"]) > 0
        assert "last_updated" in result
    
    async def test_get_database_schema_not_found(self):
        """Test schema retrieval with non-existent database"""
        # Call the service method and expect an exception
        with pytest.raises(HTTPException) as excinfo:
            await DatabaseService.get_database_schema("non_existent_db", "test_user_id")
        
        # Check the exception
        assert excinfo.value.status_code == 404
        assert "not found" in excinfo.value.detail
    
    async def test_disconnect_database(self):
        """Test database disconnection"""
        # Call the service method
        result = await DatabaseService.disconnect_database("conn_test_123", "test_user_id")
        
        # Check the result
        assert result["status"] == "disconnected"
        assert result["connection_id"] == "conn_test_123"
        assert "disconnected_at" in result