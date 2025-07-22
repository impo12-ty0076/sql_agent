"""
Manual test script for the SQL dialect handler.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Import the dialect handler directly
from backend.db.connectors.dialect_handler import SQLDialectHandler

def test_convert_date_functions():
    """Test converting date functions from MS-SQL to SAP HANA."""
    # Test GETDATE()
    mssql_query = "SELECT GETDATE() AS CurrentDate"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"Original: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert hana_query == "SELECT CURRENT_TIMESTAMP AS CurrentDate"
    
    # Test DATEADD
    mssql_query = "SELECT DATEADD(day, 1, OrderDate) AS NextDay FROM Orders"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert "ADD_SECONDS(ADD_DAYS(ADD_MONTHS(OrderDate" in hana_query
    
    # Test DATEDIFF
    mssql_query = "SELECT DATEDIFF(day, OrderDate, ShipDate) AS DaysToShip FROM Orders"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert "CASE WHEN 'day' IN ('day', 'dd', 'd') THEN DAYS_BETWEEN(ShipDate, OrderDate)" in hana_query

def test_convert_string_functions():
    """Test converting string functions from MS-SQL to SAP HANA."""
    # Test CHARINDEX
    mssql_query = "SELECT CHARINDEX('find', ProductName) AS Position FROM Products"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert hana_query == "SELECT LOCATE(ProductName, 'find') AS Position FROM Products"
    
    # Test SUBSTRING
    mssql_query = "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert hana_query == "SELECT SUBSTRING(ProductName, 1, 10) AS ShortName FROM Products"

def test_convert_pagination():
    """Test converting pagination syntax from MS-SQL to SAP HANA."""
    # Test TOP
    mssql_query = "SELECT TOP 10 * FROM Products ORDER BY Price DESC"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert "LIMIT 10" in hana_query
    
    # Test OFFSET-FETCH
    mssql_query = "SELECT * FROM Products ORDER BY Price DESC OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY"
    hana_query = SQLDialectHandler.convert_sql(
        mssql_query, 
        SQLDialectHandler.DB_TYPE_MSSQL, 
        SQLDialectHandler.DB_TYPE_HANA
    )
    print(f"\nOriginal: {mssql_query}")
    print(f"Converted: {hana_query}")
    assert "LIMIT 10 OFFSET 10" in hana_query

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
    
    features = SQLDialectHandler.detect_dialect_features(mssql_query)
    print(f"\nMS-SQL features detected: {features[SQLDialectHandler.DB_TYPE_MSSQL]}")
    print(f"SAP HANA features detected: {features[SQLDialectHandler.DB_TYPE_HANA]}")
    assert "TOP" in features[SQLDialectHandler.DB_TYPE_MSSQL]
    assert "DATEADD" in features[SQLDialectHandler.DB_TYPE_MSSQL]
    assert "GETDATE()" in features[SQLDialectHandler.DB_TYPE_MSSQL]
    assert "ISNULL" in features[SQLDialectHandler.DB_TYPE_MSSQL]
    assert "CHARINDEX" in features[SQLDialectHandler.DB_TYPE_MSSQL]
    assert "NOLOCK" in features[SQLDialectHandler.DB_TYPE_MSSQL]

def test_is_compatible():
    """Test checking SQL query compatibility with target dialect."""
    # Query with MS-SQL specific features
    mssql_query = "SELECT TOP 10 * FROM Products WITH (NOLOCK) WHERE DATEPART(year, OrderDate) = 2023"
    
    # Check compatibility with SAP HANA
    is_compatible, reason = SQLDialectHandler.is_compatible(mssql_query, SQLDialectHandler.DB_TYPE_HANA)
    print(f"\nCompatibility with SAP HANA: {is_compatible}")
    if not is_compatible:
        print(f"Reason: {reason}")
    assert not is_compatible
    assert "NOLOCK" in reason
    
    # Query with common features
    common_query = "SELECT ProductName, Price FROM Products WHERE Price > 100 ORDER BY Price DESC"
    
    # Check compatibility with both dialects
    is_compatible_mssql, _ = SQLDialectHandler.is_compatible(common_query, SQLDialectHandler.DB_TYPE_MSSQL)
    is_compatible_hana, _ = SQLDialectHandler.is_compatible(common_query, SQLDialectHandler.DB_TYPE_HANA)
    
    print(f"\nCommon query compatibility with MS-SQL: {is_compatible_mssql}")
    print(f"Common query compatibility with SAP HANA: {is_compatible_hana}")
    assert is_compatible_mssql
    assert is_compatible_hana

def test_suggest_optimizations():
    """Test suggesting dialect-specific optimizations."""
    # Query for MS-SQL optimization suggestions
    mssql_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 ORDER BY Price DESC"
    
    mssql_suggestions = SQLDialectHandler.suggest_optimizations(mssql_query, SQLDialectHandler.DB_TYPE_MSSQL)
    print(f"\nMS-SQL optimization suggestions: {mssql_suggestions}")
    assert any("NOLOCK" in suggestion for suggestion in mssql_suggestions)
    assert any("TOP" in suggestion for suggestion in mssql_suggestions)
    
    # Query for SAP HANA optimization suggestions
    hana_query = "SELECT ProductName, Price FROM Products WHERE CategoryID = 5 GROUP BY ProductName, Price"
    
    hana_suggestions = SQLDialectHandler.suggest_optimizations(hana_query, SQLDialectHandler.DB_TYPE_HANA)
    print(f"\nSAP HANA optimization suggestions: {hana_suggestions}")
    assert any("column store" in suggestion for suggestion in hana_suggestions)

if __name__ == "__main__":
    print("Running manual tests for SQL dialect handler...")
    test_convert_date_functions()
    test_convert_string_functions()
    test_convert_pagination()
    test_detect_dialect_features()
    test_is_compatible()
    test_suggest_optimizations()
    print("\nAll tests passed!")