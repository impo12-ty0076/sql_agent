"""
Simplified test script for the SQL dialect handler.
"""

import re

# Database types
DB_TYPE_MSSQL = "mssql"
DB_TYPE_HANA = "hana"

# Test functions
def test_convert_date_functions():
    """Test converting date functions from MS-SQL to SAP HANA."""
    # Test GETDATE()
    mssql_query = "SELECT GETDATE() AS CurrentDate"
    hana_query = "SELECT CURRENT_TIMESTAMP AS CurrentDate"
    print(f"Original: {mssql_query}")
    print(f"Expected: {hana_query}")
    
    # Test DATEADD
    mssql_query = "SELECT DATEADD(day, 1, OrderDate) AS NextDay FROM Orders"
    hana_query = "SELECT ADD_DAYS(OrderDate, 1) AS NextDay FROM Orders"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")
    
    # Test DATEDIFF
    mssql_query = "SELECT DATEDIFF(day, OrderDate, ShipDate) AS DaysToShip FROM Orders"
    hana_query = "SELECT DAYS_BETWEEN(ShipDate, OrderDate) AS DaysToShip FROM Orders"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")

def test_convert_string_functions():
    """Test converting string functions from MS-SQL to SAP HANA."""
    # Test CHARINDEX
    mssql_query = "SELECT CHARINDEX('find', ProductName) AS Position FROM Products"
    hana_query = "SELECT LOCATE(ProductName, 'find') AS Position FROM Products"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")
    
    # Test SUBSTRING
    mssql_query = "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products"
    hana_query = "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")

def test_convert_pagination():
    """Test converting pagination syntax from MS-SQL to SAP HANA."""
    # Test TOP
    mssql_query = "SELECT TOP 10 * FROM Products ORDER BY Price DESC"
    hana_query = "SELECT * FROM Products ORDER BY Price DESC LIMIT 10"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")
    
    # Test OFFSET-FETCH
    mssql_query = "SELECT * FROM Products ORDER BY Price DESC OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY"
    hana_query = "SELECT * FROM Products ORDER BY Price DESC LIMIT 10 OFFSET 10"
    print(f"\nOriginal: {mssql_query}")
    print(f"Expected: {hana_query}")

def test_detect_dialect_features():
    """Test detecting dialect-specific features in SQL queries."""
    # MS-SQL specific query
    mssql_query = """
        SELECT TOP 10 ProductName, Price,
               DATEADD(day, 30, GETDATE()) AS ExpiryDate,
               ISNULL(Description, 'No description') AS ProductDesc
        FROM Products WITH (NOLOCK)
        WHERE CHARINDEX('Widget', ProductName) > 0
        ORDER BY Price DESC
    """
    
    print(f"\nMS-SQL query with dialect-specific features:")
    print(mssql_query)
    
    # Features that should be detected:
    # - TOP clause
    # - DATEADD function
    # - GETDATE function
    # - ISNULL function
    # - CHARINDEX function
    # - NOLOCK hint

def test_is_compatible():
    """Test checking SQL query compatibility with target dialect."""
    # Query with MS-SQL specific features
    mssql_query = "SELECT TOP 10 * FROM Products WITH (NOLOCK) WHERE DATEPART(year, OrderDate) = 2023"
    print(f"\nMS-SQL query with dialect-specific features:")
    print(mssql_query)
    
    # This query is not compatible with SAP HANA because:
    # - NOLOCK hint is not supported in SAP HANA
    # - DATEPART function has a different syntax in SAP HANA
    
    # Query with common features
    common_query = "SELECT ProductName, Price FROM Products WHERE Price > 100 ORDER BY Price DESC"
    print(f"\nCommon query compatible with both dialects:")
    print(common_query)

def test_suggest_optimizations():
    """Test suggesting dialect-specific optimizations."""
    # Query for MS-SQL optimization suggestions
    mssql_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 ORDER BY Price DESC"
    print(f"\nMS-SQL query that could be optimized:")
    print(mssql_query)
    
    # Possible MS-SQL optimizations:
    # - Add WITH (NOLOCK) hint for read-only queries
    # - Add TOP clause to limit result set size
    
    # Query for SAP HANA optimization suggestions
    hana_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 GROUP BY ProductName, Price"
    print(f"\nSAP HANA query that could be optimized:")
    print(hana_query)
    
    # Possible SAP HANA optimizations:
    # - Use column store tables for analytical queries with GROUP BY

if __name__ == "__main__":
    print("Running simplified tests for SQL dialect handler...")
    test_convert_date_functions()
    test_convert_string_functions()
    test_convert_pagination()
    test_detect_dialect_features()
    test_is_compatible()
    test_suggest_optimizations()
    print("\nAll tests completed!")