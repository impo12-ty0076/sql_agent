"""
Standalone test script for the SQL dialect handler.
This script contains both the implementation and tests in a single file.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple, Union, Callable

# SQLDialectHandler implementation
class SQLDialectHandler:
    """
    Handles SQL dialect differences between different database systems.
    
    This class provides functionality to:
    - Detect SQL dialect features
    - Convert SQL queries between different dialects
    - Apply database-specific optimizations
    """
    
    # Database types
    DB_TYPE_MSSQL = "mssql"
    DB_TYPE_HANA = "hana"
    
    # Mapping of dialect features between MS-SQL and SAP HANA
    DIALECT_FEATURES = {
        # Date/Time Functions
        "GETDATE()": {
            DB_TYPE_MSSQL: "GETDATE()",
            DB_TYPE_HANA: "CURRENT_TIMESTAMP"
        },
        "DATEADD": {
            DB_TYPE_MSSQL: r"DATEADD\(\s*(\w+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"ADD_SECONDS(ADD_DAYS(ADD_MONTHS(\3, CASE WHEN '\1' IN ('year', 'yy', 'yyyy') THEN \2*12 WHEN '\1' IN ('quarter', 'qq', 'q') THEN \2*3 WHEN '\1' IN ('month', 'mm', 'm') THEN \2 ELSE 0 END), CASE WHEN '\1' IN ('day', 'dd', 'd') THEN \2 WHEN '\1' IN ('week', 'wk', 'ww') THEN \2*7 ELSE 0 END), CASE WHEN '\1' IN ('hour', 'hh') THEN \2*3600 WHEN '\1' IN ('minute', 'mi', 'n') THEN \2*60 WHEN '\1' IN ('second', 'ss', 's') THEN \2 WHEN '\1' IN ('millisecond', 'ms') THEN \2/1000 ELSE 0 END)"
        },
        "DATEDIFF": {
            DB_TYPE_MSSQL: r"DATEDIFF\(\s*(\w+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"CASE WHEN '\1' IN ('year', 'yy', 'yyyy') THEN MONTHS_BETWEEN(\3, \2)/12 WHEN '\1' IN ('quarter', 'qq', 'q') THEN MONTHS_BETWEEN(\3, \2)/3 WHEN '\1' IN ('month', 'mm', 'm') THEN MONTHS_BETWEEN(\3, \2) WHEN '\1' IN ('day', 'dd', 'd') THEN DAYS_BETWEEN(\3, \2) WHEN '\1' IN ('week', 'wk', 'ww') THEN DAYS_BETWEEN(\3, \2)/7 WHEN '\1' IN ('hour', 'hh') THEN SECONDS_BETWEEN(\3, \2)/3600 WHEN '\1' IN ('minute', 'mi', 'n') THEN SECONDS_BETWEEN(\3, \2)/60 WHEN '\1' IN ('second', 'ss', 's') THEN SECONDS_BETWEEN(\3, \2) WHEN '\1' IN ('millisecond', 'ms') THEN SECONDS_BETWEEN(\3, \2)*1000 ELSE 0 END"
        },
        "CONVERT_DATETIME": {
            DB_TYPE_MSSQL: r"CONVERT\(\s*DATETIME\s*,\s*([^,)]+)(?:\s*,\s*(\d+))?\s*\)",
            DB_TYPE_HANA: r"TO_TIMESTAMP(\1, CASE WHEN '\2' = '101' THEN 'MM/DD/YYYY' WHEN '\2' = '103' THEN 'DD/MM/YYYY' WHEN '\2' = '120' THEN 'YYYY-MM-DD HH24:MI:SS' WHEN '\2' = '121' THEN 'YYYY-MM-DD HH24:MI:SS.FF' ELSE 'YYYY-MM-DD' END)"
        },
        
        # String Functions
        "CHARINDEX": {
            DB_TYPE_MSSQL: r"CHARINDEX\(\s*([^,]+)\s*,\s*([^,)]+)(?:\s*,\s*([^)]+))?\s*\)",
            DB_TYPE_HANA: r"LOCATE(\2, \1\3)"
        },
        "PATINDEX": {
            DB_TYPE_MSSQL: r"PATINDEX\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"LOCATE_REGEXPR(\1, \2)"
        },
        "SUBSTRING": {
            DB_TYPE_MSSQL: r"SUBSTRING\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"SUBSTRING(\1, \2, \3)"
        },
        "LEFT": {
            DB_TYPE_MSSQL: r"LEFT\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"LEFT(\1, \2)"
        },
        "RIGHT": {
            DB_TYPE_MSSQL: r"RIGHT\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"RIGHT(\1, \2)"
        },
        "LTRIM": {
            DB_TYPE_MSSQL: r"LTRIM\(\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"LTRIM(\1)"
        },
        "RTRIM": {
            DB_TYPE_MSSQL: r"RTRIM\(\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"RTRIM(\1)"
        },
        "REPLACE": {
            DB_TYPE_MSSQL: r"REPLACE\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"REPLACE(\1, \2, \3)"
        },
        "STUFF": {
            DB_TYPE_MSSQL: r"STUFF\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"CONCAT(SUBSTRING(\1, 1, \2-1), \4, SUBSTRING(\1, \2+\3, LENGTH(\1)))"
        },
        
        # Aggregate Functions
        "STRING_AGG": {
            DB_TYPE_MSSQL: r"STRING_AGG\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"STRING_AGG(\1, \2)"
        },
        
        # System Functions
        "ISNULL": {
            DB_TYPE_MSSQL: r"ISNULL\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"IFNULL(\1, \2)"
        },
        "COALESCE": {
            DB_TYPE_MSSQL: r"COALESCE\(\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"COALESCE(\1)"
        },
        "NULLIF": {
            DB_TYPE_MSSQL: r"NULLIF\(\s*([^,]+)\s*,\s*([^)]+)\s*\)",
            DB_TYPE_HANA: r"NULLIF(\1, \2)"
        },
        
        # Top/Limit Clause
        "TOP": {
            DB_TYPE_MSSQL: r"SELECT\s+TOP\s+(\d+|\([^)]+\))\s+",
            DB_TYPE_HANA: r"SELECT "
        },
        
        # Common Table Expressions (CTE)
        "CTE_WITH": {
            DB_TYPE_MSSQL: r"WITH\s+(\w+)(?:\s*\([^)]*\))?\s+AS\s+\(([^)]+)\)",
            DB_TYPE_HANA: r"WITH \1 AS (\2)"
        },
        
        # Pagination
        "OFFSET_FETCH": {
            DB_TYPE_MSSQL: r"OFFSET\s+(\d+|\([^)]+\))\s+ROWS\s+FETCH\s+NEXT\s+(\d+|\([^)]+\))\s+ROWS\s+ONLY",
            DB_TYPE_HANA: r"LIMIT \2 OFFSET \1"
        },
        
        # Data Type Conversion
        "CAST": {
            DB_TYPE_MSSQL: r"CAST\(\s*([^)]+)\s+AS\s+([^)]+)\s*\)",
            DB_TYPE_HANA: r"CAST(\1 AS \2)"
        },
        
        # Temporary Tables
        "TEMP_TABLE": {
            DB_TYPE_MSSQL: r"#(\w+)",
            DB_TYPE_HANA: r"#\1"  # SAP HANA uses the same syntax for local temporary tables
        },
        
        # Identity/Auto-increment
        "IDENTITY": {
            DB_TYPE_MSSQL: r"IDENTITY\(\s*(\d+)\s*,\s*(\d+)\s*\)",
            DB_TYPE_HANA: r"GENERATED BY DEFAULT AS IDENTITY (START WITH \1 INCREMENT BY \2)"
        },
        
        # Pivot/Unpivot
        "PIVOT": {
            DB_TYPE_MSSQL: r"PIVOT\s*\(([^)]+)\s+FOR\s+([^)]+)\s+IN\s+\(([^)]+)\)\s*\)\s+AS\s+(\w+)",
            DB_TYPE_HANA: None  # SAP HANA doesn't support PIVOT directly, requires rewrite
        },
        
        # Row Number
        "ROW_NUMBER": {
            DB_TYPE_MSSQL: r"ROW_NUMBER\(\)\s+OVER\s*\(([^)]*)\)",
            DB_TYPE_HANA: r"ROW_NUMBER() OVER (\1)"
        },
        
        # Recursive CTE
        "RECURSIVE_CTE": {
            DB_TYPE_MSSQL: r"WITH\s+RECURSIVE\s+(\w+)(?:\s*\([^)]*\))?\s+AS\s+\(([^)]+)\)",
            DB_TYPE_HANA: r"WITH RECURSIVE \1 AS (\2)"
        },
        
        # Merge Statement
        "MERGE": {
            DB_TYPE_MSSQL: r"MERGE\s+INTO\s+([^\s]+)\s+AS\s+(\w+)\s+USING\s+([^\s]+)\s+AS\s+(\w+)\s+ON\s+([^)]+)",
            DB_TYPE_HANA: r"MERGE INTO \1 AS \2 USING \3 AS \4 ON \5"
        },
        
        # Sequence
        "NEXT_VAL": {
            DB_TYPE_MSSQL: r"NEXT\s+VALUE\s+FOR\s+([^\s]+)",
            DB_TYPE_HANA: r"\1.NEXTVAL"
        },
        
        # Hints
        "NOLOCK": {
            DB_TYPE_MSSQL: r"WITH\s*\(\s*NOLOCK\s*\)",
            DB_TYPE_HANA: ""  # SAP HANA doesn't support NOLOCK hint
        },
        
        # Pagination with ROW_NUMBER
        "ROW_NUMBER_PAGINATION": {
            DB_TYPE_MSSQL: r"SELECT\s+.*\s+FROM\s+\(\s*SELECT\s+ROW_NUMBER\(\)\s+OVER\s*\(([^)]*)\)\s+AS\s+RowNum,\s*(.*)\s+FROM\s+(.*)\s*\)\s+AS\s+\w+\s+WHERE\s+RowNum\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)",
            DB_TYPE_HANA: r"SELECT \2 FROM \3 ORDER BY \1 LIMIT \5 OFFSET \4"
        }
    }
    
    @classmethod
    def convert_sql(cls, query: str, source_dialect: str, target_dialect: str) -> str:
        """
        Convert a SQL query from one dialect to another.
        
        Args:
            query: SQL query string
            source_dialect: Source dialect (e.g., 'mssql', 'hana')
            target_dialect: Target dialect (e.g., 'mssql', 'hana')
            
        Returns:
            Converted SQL query string
        """
        if source_dialect == target_dialect:
            return query
        
        # Make a copy of the original query
        converted_query = query
        
        # Apply dialect-specific conversions
        for feature, dialects in cls.DIALECT_FEATURES.items():
            source_pattern = dialects.get(source_dialect)
            target_pattern = dialects.get(target_dialect)
            
            # Skip if either pattern is missing
            if not source_pattern or not target_pattern:
                continue
            
            # Handle special cases
            if feature == "TOP":
                # For TOP clause, we need to add LIMIT at the end
                if source_dialect == cls.DB_TYPE_MSSQL and target_dialect == cls.DB_TYPE_HANA:
                    match = re.search(source_pattern, converted_query, re.IGNORECASE)
                    if match:
                        limit_value = match.group(1)
                        converted_query = re.sub(source_pattern, target_pattern, converted_query, flags=re.IGNORECASE)
                        # Add LIMIT clause at the end, before any ORDER BY
                        order_by_match = re.search(r"ORDER\s+BY\s+", converted_query, re.IGNORECASE)
                        if order_by_match:
                            order_by_pos = order_by_match.start()
                            converted_query = f"{converted_query[:order_by_pos]}LIMIT {limit_value} {converted_query[order_by_pos:]}"
                        else:
                            converted_query = f"{converted_query} LIMIT {limit_value}"
            else:
                # Regular pattern replacement
                converted_query = re.sub(source_pattern, target_pattern, converted_query, flags=re.IGNORECASE)
        
        # Handle special cases that require more complex transformations
        if source_dialect == cls.DB_TYPE_MSSQL and target_dialect == cls.DB_TYPE_HANA:
            # Handle PIVOT transformation (simplified example)
            pivot_match = re.search(cls.DIALECT_FEATURES["PIVOT"][cls.DB_TYPE_MSSQL], converted_query, re.IGNORECASE)
            if pivot_match:
                # This is a simplified approach - a real implementation would need to parse and rewrite the query
                print("PIVOT operation detected. SAP HANA requires manual rewrite of PIVOT queries.")
                converted_query = f"/* PIVOT operation needs manual rewrite for SAP HANA: {converted_query} */"
        
        return converted_query
    
    @classmethod
    def detect_dialect_features(cls, query: str) -> Dict[str, List[str]]:
        """
        Detect dialect-specific features in a SQL query.
        
        Args:
            query: SQL query string
            
        Returns:
            Dictionary mapping dialect types to lists of detected features
        """
        features = {
            cls.DB_TYPE_MSSQL: [],
            cls.DB_TYPE_HANA: []
        }
        
        # Check for dialect-specific features
        for feature, dialects in cls.DIALECT_FEATURES.items():
            for dialect, pattern in dialects.items():
                if pattern and re.search(pattern, query, re.IGNORECASE):
                    features[dialect].append(feature)
        
        return features
    
    @classmethod
    def is_compatible(cls, query: str, target_dialect: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a SQL query is compatible with a target dialect.
        
        Args:
            query: SQL query string
            target_dialect: Target dialect (e.g., 'mssql', 'hana')
            
        Returns:
            Tuple of (is_compatible: bool, incompatibility_reason: Optional[str])
        """
        # Detect dialect features
        detected_features = cls.detect_dialect_features(query)
        
        # Check for features that are specific to other dialects
        incompatible_features = []
        for dialect, features in detected_features.items():
            if dialect != target_dialect and features:
                for feature in features:
                    # Check if the feature has a corresponding pattern in the target dialect
                    if not cls.DIALECT_FEATURES[feature].get(target_dialect):
                        incompatible_features.append(feature)
        
        if incompatible_features:
            return False, f"Query contains features not supported in {target_dialect}: {', '.join(incompatible_features)}"
        
        return True, None
    
    @classmethod
    def suggest_optimizations(cls, query: str, target_dialect: str) -> List[str]:
        """
        Suggest dialect-specific optimizations for a SQL query.
        
        Args:
            query: SQL query string
            target_dialect: Target dialect (e.g., 'mssql', 'hana')
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # MS-SQL specific optimizations
        if target_dialect == cls.DB_TYPE_MSSQL:
            # Check for missing indexes hint
            if "SELECT" in query.upper() and "FROM" in query.upper() and "WHERE" in query.upper():
                if "WITH (NOLOCK)" not in query.upper():
                    suggestions.append("Consider adding WITH (NOLOCK) hint for read-only queries to improve concurrency")
            
            # Check for missing TOP clause in large result sets
            if "SELECT" in query.upper() and "TOP" not in query.upper() and "ORDER BY" in query.upper():
                suggestions.append("Consider adding TOP clause to limit result set size when using ORDER BY")
        
        # SAP HANA specific optimizations
        elif target_dialect == cls.DB_TYPE_HANA:
            # Check for missing LIMIT clause
            if "SELECT" in query.upper() and "LIMIT" not in query.upper() and "ORDER BY" in query.upper():
                suggestions.append("Consider adding LIMIT clause to restrict result set size when using ORDER BY")
            
            # Check for potential use of column store tables
            if "FROM" in query.upper() and "WHERE" in query.upper() and "GROUP BY" in query.upper():
                suggestions.append("Consider using column store tables for analytical queries with GROUP BY")
        
        return suggestions

# Test functions
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
    assert "CURRENT_TIMESTAMP" in hana_query
    
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
    assert "DAYS_BETWEEN(ShipDate, OrderDate)" in hana_query

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
    assert "ORDER BY Price DESC" in hana_query
    
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
    print("Running standalone tests for SQL dialect handler...")
    test_convert_date_functions()
    test_convert_string_functions()
    test_convert_pagination()
    test_detect_dialect_features()
    test_is_compatible()
    test_suggest_optimizations()
    print("\nAll tests passed!")