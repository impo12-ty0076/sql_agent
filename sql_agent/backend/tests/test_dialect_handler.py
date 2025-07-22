"""
Unit tests for the SQL dialect handler.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.db.connectors.dialect_handler import SQLDialectHandler

class TestSQLDialectHandler(unittest.TestCase):
    """
    Tests for the SQL dialect handler.
    """
    
    def test_convert_date_functions_mssql_to_hana(self):
        """
        Test converting date functions from MS-SQL to SAP HANA.
        """
        # Test GETDATE()
        mssql_query = "SELECT GETDATE() AS CurrentDate"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT CURRENT_TIMESTAMP AS CurrentDate")
        
        # Test DATEADD
        mssql_query = "SELECT DATEADD(day, 1, OrderDate) AS NextDay FROM Orders"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertIn("ADD_SECONDS(ADD_DAYS(ADD_MONTHS(OrderDate", hana_query)
        self.assertIn("CASE WHEN 'day' IN ('day', 'dd', 'd') THEN 1", hana_query)
        
        # Test DATEDIFF
        mssql_query = "SELECT DATEDIFF(day, OrderDate, ShipDate) AS DaysToShip FROM Orders"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertIn("CASE WHEN 'day' IN ('day', 'dd', 'd') THEN DAYS_BETWEEN(ShipDate, OrderDate)", hana_query)
    
    def test_convert_string_functions_mssql_to_hana(self):
        """
        Test converting string functions from MS-SQL to SAP HANA.
        """
        # Test CHARINDEX
        mssql_query = "SELECT CHARINDEX('find', ProductName) AS Position FROM Products"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT LOCATE(ProductName, 'find') AS Position FROM Products")
        
        # Test SUBSTRING
        mssql_query = "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products")
        
        # Test STUFF
        mssql_query = "SELECT STUFF(EmailAddress, 2, 3, '***') AS MaskedEmail FROM Customers"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertIn("CONCAT(SUBSTRING(EmailAddress, 1, 2-1), '***', SUBSTRING(EmailAddress, 2+3, LENGTH(EmailAddress)))", hana_query)
    
    def test_convert_system_functions_mssql_to_hana(self):
        """
        Test converting system functions from MS-SQL to SAP HANA.
        """
        # Test ISNULL
        mssql_query = "SELECT ISNULL(Region, 'N/A') AS RegionName FROM Customers"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT IFNULL(Region, 'N/A') AS RegionName FROM Customers")
        
        # Test COALESCE
        mssql_query = "SELECT COALESCE(HomePhone, WorkPhone, MobilePhone) AS ContactNumber FROM Customers"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT COALESCE(HomePhone, WorkPhone, MobilePhone) AS ContactNumber FROM Customers")
    
    def test_convert_pagination_mssql_to_hana(self):
        """
        Test converting pagination syntax from MS-SQL to SAP HANA.
        """
        # Test TOP
        mssql_query = "SELECT TOP 10 * FROM Products ORDER BY Price DESC"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT * FROM Products ORDER BY Price DESC LIMIT 10")
        
        # Test OFFSET-FETCH
        mssql_query = "SELECT * FROM Products ORDER BY Price DESC OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY"
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query, 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertEqual(hana_query, "SELECT * FROM Products ORDER BY Price DESC LIMIT 10 OFFSET 10")
        
        # Test ROW_NUMBER pagination
        mssql_query = """
            SELECT * FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY Price DESC) AS RowNum, ProductName, Price
                FROM Products
            ) AS Temp
            WHERE RowNum BETWEEN 11 AND 20
        """
        hana_query = SQLDialectHandler.convert_sql(
            mssql_query.strip(), 
            SQLDialectHandler.DB_TYPE_MSSQL, 
            SQLDialectHandler.DB_TYPE_HANA
        )
        self.assertIn("SELECT ProductName, Price FROM Products ORDER BY Price DESC LIMIT 20 OFFSET 11", hana_query)
    
    def test_detect_dialect_features(self):
        """
        Test detecting dialect-specific features in SQL queries.
        """
        # MS-SQL specific query
        mssql_query = """
            SELECT TOP 10 ProductName, Price,
                   DATEADD(day, 30, GETDATE()) AS ExpiryDate,
                   ISNULL(Description, 'No description') AS ProductDesc
            FROM Products WITH (NOLOCK)
            WHERE CHARINDEX('Widget', ProductName) > 0
            ORDER BY Price DESC
        """
        
        features = SQLDialectHandler.detect_dialect_features(mssql_query)
        self.assertIn("TOP", features[SQLDialectHandler.DB_TYPE_MSSQL])
        self.assertIn("DATEADD", features[SQLDialectHandler.DB_TYPE_MSSQL])
        self.assertIn("GETDATE()", features[SQLDialectHandler.DB_TYPE_MSSQL])
        self.assertIn("ISNULL", features[SQLDialectHandler.DB_TYPE_MSSQL])
        self.assertIn("CHARINDEX", features[SQLDialectHandler.DB_TYPE_MSSQL])
        self.assertIn("NOLOCK", features[SQLDialectHandler.DB_TYPE_MSSQL])
        
        # SAP HANA specific query
        hana_query = """
            SELECT ProductName, Price,
                   ADD_DAYS(CURRENT_TIMESTAMP, 30) AS ExpiryDate,
                   IFNULL(Description, 'No description') AS ProductDesc
            FROM Products
            WHERE LOCATE(ProductName, 'Widget') > 0
            ORDER BY Price DESC
            LIMIT 10
        """
        
        features = SQLDialectHandler.detect_dialect_features(hana_query)
        self.assertIn("GETDATE()", features[SQLDialectHandler.DB_TYPE_HANA])  # CURRENT_TIMESTAMP matches GETDATE pattern
        self.assertIn("ISNULL", features[SQLDialectHandler.DB_TYPE_HANA])     # IFNULL matches ISNULL pattern
        self.assertIn("CHARINDEX", features[SQLDialectHandler.DB_TYPE_HANA])  # LOCATE matches CHARINDEX pattern
    
    def test_is_compatible(self):
        """
        Test checking SQL query compatibility with target dialect.
        """
        # Query with MS-SQL specific features
        mssql_query = "SELECT TOP 10 * FROM Products WITH (NOLOCK) WHERE DATEPART(year, OrderDate) = 2023"
        
        # Check compatibility with SAP HANA
        is_compatible, reason = SQLDialectHandler.is_compatible(mssql_query, SQLDialectHandler.DB_TYPE_HANA)
        self.assertFalse(is_compatible)
        self.assertIn("NOLOCK", reason)
        
        # Query with common features
        common_query = "SELECT ProductName, Price FROM Products WHERE Price > 100 ORDER BY Price DESC"
        
        # Check compatibility with both dialects
        is_compatible_mssql, _ = SQLDialectHandler.is_compatible(common_query, SQLDialectHandler.DB_TYPE_MSSQL)
        is_compatible_hana, _ = SQLDialectHandler.is_compatible(common_query, SQLDialectHandler.DB_TYPE_HANA)
        
        self.assertTrue(is_compatible_mssql)
        self.assertTrue(is_compatible_hana)
    
    def test_suggest_optimizations(self):
        """
        Test suggesting dialect-specific optimizations.
        """
        # Query for MS-SQL optimization suggestions
        mssql_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 ORDER BY Price DESC"
        
        mssql_suggestions = SQLDialectHandler.suggest_optimizations(mssql_query, SQLDialectHandler.DB_TYPE_MSSQL)
        self.assertTrue(any("NOLOCK" in suggestion for suggestion in mssql_suggestions))
        self.assertTrue(any("TOP" in suggestion for suggestion in mssql_suggestions))
        
        # Query for SAP HANA optimization suggestions
        hana_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 GROUP BY ProductName, Price"
        
        hana_suggestions = SQLDialectHandler.suggest_optimizations(hana_query, SQLDialectHandler.DB_TYPE_HANA)
        self.assertTrue(any("column store" in suggestion for suggestion in hana_suggestions))

if __name__ == "__main__":
    unittest.main()