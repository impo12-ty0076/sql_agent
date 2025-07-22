"""
Unit tests for the SQL converter.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.models.database import Database, DBType, ConnectionConfig
from backend.db.connectors.sql_converter import SQLConverter
from backend.db.connectors.dialect_handler import SQLDialectHandler

class TestSQLConverter(unittest.TestCase):
    """
    Tests for the SQL converter.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        # Create mock database configurations
        self.mssql_db = Database(
            id="test-mssql-db",
            name="Test MS-SQL Database",
            type=DBType.MSSQL,
            host="mssql-server",
            port=1433,
            default_schema="dbo",
            connection_config=ConnectionConfig(
                username="sa",
                password_encrypted="encrypted_password",
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.hana_db = Database(
            id="test-hana-db",
            name="Test SAP HANA Database",
            type=DBType.HANA,
            host="hana-server",
            port=30015,
            default_schema="TESTDB",
            connection_config=ConnectionConfig(
                username="SYSTEM",
                password_encrypted="encrypted_password",
                options={}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_auto_convert_mssql_to_hana(self):
        """
        Test automatically converting MS-SQL query to SAP HANA.
        """
        # MS-SQL query with dialect-specific features
        mssql_query = """
            SELECT TOP 10 ProductName, Price,
                   DATEADD(day, 30, OrderDate) AS ExpiryDate,
                   ISNULL(Description, 'No description') AS ProductDesc
            FROM Products
            WHERE CHARINDEX('Widget', ProductName) > 0
            ORDER BY Price DESC
        """
        
        # Convert to SAP HANA
        converted_query, warnings = SQLConverter.auto_convert(mssql_query, self.hana_db)
        
        # Check that the query was converted
        self.assertNotEqual(converted_query, mssql_query)
        self.assertIn("LIMIT 10", converted_query)
        self.assertIn("IFNULL", converted_query)
        self.assertIn("LOCATE", converted_query)
        
        # Check warnings
        self.assertTrue(any("converted from mssql to hana" in warning.lower() for warning in warnings))
    
    def test_auto_convert_hana_to_mssql(self):
        """
        Test automatically converting SAP HANA query to MS-SQL.
        """
        # SAP HANA query with dialect-specific features
        hana_query = """
            SELECT ProductName, Price,
                   ADD_DAYS(CURRENT_TIMESTAMP, 30) AS ExpiryDate,
                   IFNULL(Description, 'No description') AS ProductDesc
            FROM Products
            WHERE LOCATE(ProductName, 'Widget') > 0
            ORDER BY Price DESC
            LIMIT 10
        """
        
        # Convert to MS-SQL
        converted_query, warnings = SQLConverter.auto_convert(hana_query, self.mssql_db)
        
        # Check that the query was converted
        self.assertNotEqual(converted_query, hana_query)
        self.assertIn("TOP 10", converted_query)
        self.assertIn("ISNULL", converted_query)
        self.assertIn("CHARINDEX", converted_query)
        
        # Check warnings
        self.assertTrue(any("converted from hana to mssql" in warning.lower() for warning in warnings))
    
    def test_auto_convert_no_dialect_features(self):
        """
        Test converting a query with no dialect-specific features.
        """
        # Generic SQL query
        generic_query = """
            SELECT ProductName, Price
            FROM Products
            WHERE CategoryID = 5
            ORDER BY Price DESC
        """
        
        # Convert to SAP HANA
        converted_query, warnings = SQLConverter.auto_convert(generic_query, self.hana_db)
        
        # Check that the query was not changed
        self.assertEqual(converted_query, generic_query)
        self.assertEqual(len(warnings), 0)
    
    def test_auto_convert_unsupported_db_type(self):
        """
        Test converting a query for an unsupported database type.
        """
        # Create a mock database with unsupported type
        unsupported_db = MagicMock()
        unsupported_db.type = "oracle"
        
        # MS-SQL query
        mssql_query = "SELECT TOP 10 * FROM Products"
        
        # Try to convert
        converted_query, warnings = SQLConverter.auto_convert(mssql_query, unsupported_db)
        
        # Check that the query was not changed
        self.assertEqual(converted_query, mssql_query)
        self.assertTrue(any("Unsupported database type" in warning for warning in warnings))
    
    def test_convert_with_dialect_mssql_to_hana(self):
        """
        Test converting a query with specified dialects.
        """
        # MS-SQL query
        mssql_query = "SELECT TOP 10 * FROM Products ORDER BY Price DESC"
        
        # Convert to SAP HANA
        converted_query, warnings = SQLConverter.convert_with_dialect(
            mssql_query,
            SQLDialectHandler.DB_TYPE_MSSQL,
            SQLDialectHandler.DB_TYPE_HANA
        )
        
        # Check that the query was converted
        self.assertNotEqual(converted_query, mssql_query)
        self.assertIn("LIMIT 10", converted_query)
        
        # Check warnings
        self.assertTrue(any("converted from mssql to hana" in warning.lower() for warning in warnings))
    
    def test_convert_with_dialect_same_dialect(self):
        """
        Test converting a query when source and target dialects are the same.
        """
        # MS-SQL query
        mssql_query = "SELECT TOP 10 * FROM Products ORDER BY Price DESC"
        
        # Convert to the same dialect
        converted_query, warnings = SQLConverter.convert_with_dialect(
            mssql_query,
            SQLDialectHandler.DB_TYPE_MSSQL,
            SQLDialectHandler.DB_TYPE_MSSQL
        )
        
        # Check that the query was not changed
        self.assertEqual(converted_query, mssql_query)
        self.assertEqual(len(warnings), 0)
    
    def test_convert_with_dialect_incompatible_query(self):
        """
        Test converting a query that is not fully compatible with the target dialect.
        """
        # MS-SQL query with PIVOT (not directly supported in SAP HANA)
        mssql_query = """
            SELECT ProductCategory, [2021], [2022], [2023]
            FROM (
                SELECT ProductCategory, Year, Sales
                FROM ProductSales
            ) AS SourceTable
            PIVOT (
                SUM(Sales)
                FOR Year IN ([2021], [2022], [2023])
            ) AS PivotTable
        """
        
        # Convert to SAP HANA
        converted_query, warnings = SQLConverter.convert_with_dialect(
            mssql_query,
            SQLDialectHandler.DB_TYPE_MSSQL,
            SQLDialectHandler.DB_TYPE_HANA
        )
        
        # Check warnings
        self.assertTrue(any("not be fully compatible" in warning for warning in warnings))
    
    @patch('sql_agent.backend.db.connectors.dialect_handler.SQLDialectHandler.convert_sql')
    def test_convert_with_dialect_exception(self, mock_convert_sql):
        """
        Test handling exceptions during query conversion.
        """
        # Set up the mock to raise an exception
        mock_convert_sql.side_effect = Exception("Test conversion error")
        
        # MS-SQL query
        mssql_query = "SELECT TOP 10 * FROM Products"
        
        # Try to convert
        converted_query, warnings = SQLConverter.convert_with_dialect(
            mssql_query,
            SQLDialectHandler.DB_TYPE_MSSQL,
            SQLDialectHandler.DB_TYPE_HANA
        )
        
        # Check that the original query is returned
        self.assertEqual(converted_query, mssql_query)
        
        # Check warnings
        self.assertTrue(any("Failed to convert query" in warning for warning in warnings))
        self.assertTrue(any("Test conversion error" in warning for warning in warnings))

if __name__ == "__main__":
    unittest.main()