"""
Unit tests for the SQL validator.
"""

import unittest
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.llm.sql_validator import SQLValidator, SQLValidationLevel
from backend.llm.base import LLMService, LLMConfig, LLMProvider

class TestSQLValidator(unittest.TestCase):
    """
    Tests for the SQL validator.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        """
        # Create a mock LLM service
        self.mock_llm_service = MagicMock(spec=LLMService)
        self.mock_llm_service.validate_and_fix_sql = AsyncMock(return_value=("OPTIMIZED SQL", True))
        
        # Create a SQL validator instance
        self.validator = SQLValidator(llm_service=self.mock_llm_service)
        
        # Sample schema for testing
        self.test_schema = {
            "schemas": [
                {
                    "name": "dbo",
                    "tables": [
                        {
                            "name": "employees",
                            "columns": [
                                {"name": "employee_id", "type": "INT", "nullable": False},
                                {"name": "first_name", "type": "VARCHAR(50)", "nullable": False},
                                {"name": "last_name", "type": "VARCHAR(50)", "nullable": False},
                                {"name": "email", "type": "VARCHAR(100)", "nullable": True},
                                {"name": "hire_date", "type": "DATE", "nullable": False},
                                {"name": "department_id", "type": "INT", "nullable": True}
                            ]
                        },
                        {
                            "name": "departments",
                            "columns": [
                                {"name": "department_id", "type": "INT", "nullable": False},
                                {"name": "department_name", "type": "VARCHAR(100)", "nullable": False},
                                {"name": "location_id", "type": "INT", "nullable": True}
                            ]
                        }
                    ]
                }
            ]
        }
    
    def test_validate_basic_syntax_valid(self):
        """
        Test basic syntax validation with valid SQL.
        """
        valid_sql = "SELECT employee_id, first_name, last_name FROM employees WHERE department_id = 10"
        is_valid, error_msg = self.validator._validate_basic_syntax(valid_sql)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_basic_syntax_invalid_empty(self):
        """
        Test basic syntax validation with empty SQL.
        """
        empty_sql = ""
        is_valid, error_msg = self.validator._validate_basic_syntax(empty_sql)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "SQL 쿼리가 비어 있습니다.")
    
    def test_validate_basic_syntax_invalid_operation(self):
        """
        Test basic syntax validation with invalid operation.
        """
        invalid_sql = "UPDATE employees SET salary = 5000 WHERE employee_id = 1"
        is_valid, error_msg = self.validator._validate_basic_syntax(invalid_sql)
        self.assertFalse(is_valid)
        self.assertIn("UPDATE", error_msg)
        self.assertIn("허용되지 않습니다", error_msg)
    
    def test_validate_basic_syntax_missing_from(self):
        """
        Test basic syntax validation with missing FROM clause.
        """
        invalid_sql = "SELECT employee_id, first_name, last_name WHERE department_id = 10"
        is_valid, error_msg = self.validator._validate_basic_syntax(invalid_sql)
        self.assertFalse(is_valid)
        self.assertIn("FROM", error_msg)
    
    def test_validate_basic_syntax_unbalanced_parentheses(self):
        """
        Test basic syntax validation with unbalanced parentheses.
        """
        invalid_sql = "SELECT employee_id, first_name, last_name FROM employees WHERE (department_id = 10"
        is_valid, error_msg = self.validator._validate_basic_syntax(invalid_sql)
        self.assertFalse(is_valid)
        self.assertIn("괄호", error_msg)
    
    def test_check_sql_injection(self):
        """
        Test SQL injection pattern detection.
        """
        # SQL with injection patterns
        sql_with_injection = "SELECT * FROM employees; DROP TABLE users"
        injection_issues = self.validator._check_sql_injection(sql_with_injection)
        self.assertTrue(len(injection_issues) > 0)
        self.assertIn("세미콜론", injection_issues[0])
        
        # SQL with UNION injection
        sql_with_union = "SELECT * FROM employees UNION SELECT username, password FROM users"
        injection_issues = self.validator._check_sql_injection(sql_with_union)
        self.assertTrue(len(injection_issues) > 0)
        self.assertIn("UNION", injection_issues[0])
        
        # SQL with no injection
        safe_sql = "SELECT * FROM employees WHERE department_id = 10"
        injection_issues = self.validator._check_sql_injection(safe_sql)
        self.assertEqual(len(injection_issues), 0)
    
    def test_validate_schema(self):
        """
        Test schema validation.
        """
        # Valid SQL with existing tables and columns
        valid_sql = "SELECT e.employee_id, e.first_name, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id"
        schema_issues = self.validator._validate_schema(valid_sql, self.test_schema)
        self.assertEqual(len(schema_issues), 0)
        
        # SQL with non-existent table
        invalid_sql = "SELECT * FROM non_existent_table"
        schema_issues = self.validator._validate_schema(invalid_sql, self.test_schema)
        self.assertTrue(len(schema_issues) > 0)
        self.assertIn("non_existent_table", schema_issues[0])
        
        # SQL with non-existent column
        invalid_sql = "SELECT salary FROM employees"
        schema_issues = self.validator._validate_schema(invalid_sql, self.test_schema)
        self.assertTrue(len(schema_issues) > 0)
        self.assertIn("salary", schema_issues[0])
    
    def test_extract_tables_from_query(self):
        """
        Test extracting table names from SQL query.
        """
        # Simple query
        sql = "SELECT * FROM employees"
        tables = self.validator._extract_tables_from_query(sql)
        self.assertEqual(tables, ["employees"])
        
        # Query with JOIN
        sql = "SELECT * FROM employees e JOIN departments d ON e.department_id = d.department_id"
        tables = self.validator._extract_tables_from_query(sql)
        self.assertEqual(set(tables), {"employees", "departments"})
        
        # Query with table alias
        sql = "SELECT * FROM employees AS e"
        tables = self.validator._extract_tables_from_query(sql)
        self.assertEqual(tables, ["employees"])
    
    def test_extract_columns_from_query(self):
        """
        Test extracting column names from SQL query.
        """
        # Simple query
        sql = "SELECT employee_id, first_name FROM employees"
        columns = self.validator._extract_columns_from_query(sql)
        self.assertEqual(set(columns), {"employee_id", "first_name"})
        
        # Query with table prefix
        sql = "SELECT e.employee_id, e.first_name FROM employees e"
        columns = self.validator._extract_columns_from_query(sql)
        self.assertEqual(set(columns), {"e.employee_id", "e.first_name"})
        
        # Query with WHERE clause
        sql = "SELECT * FROM employees WHERE department_id = 10"
        columns = self.validator._extract_columns_from_query(sql)
        self.assertEqual(columns, ["department_id"])
    
    def test_check_performance_issues(self):
        """
        Test performance issue detection.
        """
        # Query with SELECT *
        sql = "SELECT * FROM employees"
        warnings = self.validator._check_performance_issues(sql, "mssql")
        self.assertTrue(any("SELECT *" in warning for warning in warnings))
        
        # Query without WHERE clause
        sql = "SELECT employee_id FROM employees"
        warnings = self.validator._check_performance_issues(sql, "mssql")
        self.assertTrue(any("WHERE" in warning for warning in warnings))
        
        # Query with DISTINCT
        sql = "SELECT DISTINCT department_id FROM employees"
        warnings = self.validator._check_performance_issues(sql, "mssql")
        self.assertTrue(any("DISTINCT" in warning for warning in warnings))
        
        # MS-SQL specific warnings
        sql = "SELECT * FROM employees WHERE department_id = 10"
        warnings = self.validator._check_performance_issues(sql, "mssql")
        self.assertTrue(any("NOLOCK" in warning for warning in warnings))
        
        # SAP HANA specific warnings
        sql = "SELECT * FROM employees WHERE name LIKE '%John%'"
        warnings = self.validator._check_performance_issues(sql, "hana")
        self.assertTrue(any("LIKE '%" in warning for warning in warnings))
    
    def test_apply_basic_optimizations(self):
        """
        Test applying basic SQL optimizations.
        """
        # SQL with extra whitespace
        sql = "SELECT   employee_id,   first_name,   last_name  FROM   employees  WHERE   department_id = 10"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "mssql")
        self.assertIn("불필요한 공백", optimizations[0])
        self.assertEqual(optimized_sql, "SELECT employee_id, first_name, last_name FROM employees WHERE department_id = 10")
        
        # MS-SQL specific optimizations
        sql = "SELECT * FROM employees WHERE department_id = 10"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "mssql")
        self.assertIn("WITH (NOLOCK)", optimized_sql)
        self.assertTrue(any("NOLOCK" in opt for opt in optimizations))
    
    def test_validate_sql_basic_level(self):
        """
        Test SQL validation with BASIC level.
        """
        # Valid SQL
        valid_sql = "SELECT employee_id, first_name FROM employees WHERE department_id = 10"
        is_valid, errors, warnings = self.validator.validate_sql(
            valid_sql, 
            "mssql", 
            validation_level=SQLValidationLevel.BASIC
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid SQL (injection)
        invalid_sql = "SELECT * FROM employees; DROP TABLE users"
        is_valid, errors, warnings = self.validator.validate_sql(
            invalid_sql, 
            "mssql", 
            validation_level=SQLValidationLevel.BASIC
        )
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
    
    def test_validate_sql_standard_level(self):
        """
        Test SQL validation with STANDARD level.
        """
        # Valid SQL with schema
        valid_sql = "SELECT employee_id, first_name FROM employees WHERE department_id = 10"
        is_valid, errors, warnings = self.validator.validate_sql(
            valid_sql, 
            "mssql", 
            schema=self.test_schema,
            validation_level=SQLValidationLevel.STANDARD
        )
        self.assertTrue(is_valid)
        
        # SQL with schema issues
        invalid_sql = "SELECT salary FROM employees WHERE department_id = 10"
        is_valid, errors, warnings = self.validator.validate_sql(
            invalid_sql, 
            "mssql", 
            schema=self.test_schema,
            validation_level=SQLValidationLevel.STANDARD
        )
        self.assertTrue(is_valid)  # Still valid as schema issues are warnings
        self.assertTrue(len(warnings) > 0)
        self.assertIn("salary", warnings[0])
    
    def test_validate_sql_strict_level(self):
        """
        Test SQL validation with STRICT level.
        """
        # SQL with performance issues
        sql = "SELECT * FROM employees WHERE department_id = 10"
        is_valid, errors, warnings = self.validator.validate_sql(
            sql, 
            "mssql", 
            schema=self.test_schema,
            validation_level=SQLValidationLevel.STRICT
        )
        self.assertTrue(is_valid)
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("SELECT *" in warning for warning in warnings))
    
    @pytest.mark.asyncio
    async def test_optimize_sql(self):
        """
        Test SQL optimization.
        """
        # Basic SQL
        sql = "SELECT employee_id, first_name FROM employees WHERE department_id = 10"
        optimized_sql, optimizations = await self.validator.optimize_sql(sql, "mssql", self.test_schema)
        self.assertEqual(optimized_sql, "OPTIMIZED SQL")  # From mock
        self.assertTrue(len(optimizations) > 0)
        
        # Test without LLM service
        validator_without_llm = SQLValidator()
        sql = "SELECT employee_id, first_name FROM employees WHERE department_id = 10"
        optimized_sql, optimizations = await validator_without_llm.optimize_sql(sql, "mssql", self.test_schema)
        self.assertNotEqual(optimized_sql, "OPTIMIZED SQL")  # Should not be from mock
        self.assertTrue(len(optimizations) > 0)

    def test_sql_injection_detection_advanced(self):
        """
        Test advanced SQL injection pattern detection.
        """
        # Test various SQL injection patterns
        injection_patterns = [
            "SELECT * FROM employees; DROP TABLE users",
            "SELECT * FROM employees UNION SELECT username, password FROM users",
            "SELECT * FROM employees WHERE name = 'John' OR 1=1",
            "SELECT * FROM employees WHERE name = 'John' OR '1'='1'",
            "SELECT * FROM employees WHERE name = 'John'; EXEC xp_cmdshell('dir')",
            "SELECT * FROM employees WHERE name LIKE '%'; WAITFOR DELAY '0:0:5'--",
            "SELECT * FROM employees WHERE id = 1 OR EXISTS(SELECT 1 FROM users WHERE username='admin')",
            "SELECT * FROM employees WHERE id = CONVERT(INT, '1; DROP TABLE users')",
            "SELECT * FROM employees WHERE name = 'John' -- AND active=1",
            "SELECT * FROM employees WHERE name = 'John' /* comment */ OR 1=1"
        ]
        
        for pattern in injection_patterns:
            injection_issues = self.validator._check_sql_injection(pattern)
            self.assertTrue(len(injection_issues) > 0, f"Failed to detect injection in: {pattern}")
            print(f"Detected issues in '{pattern}': {injection_issues}")
    
    def test_schema_validation_advanced(self):
        """
        Test advanced schema validation.
        """
        # Test with JOIN conditions
        sql_with_join = "SELECT e.employee_id, e.first_name, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id"
        schema_issues = self.validator._validate_schema(sql_with_join, self.test_schema)
        self.assertEqual(len(schema_issues), 0)
        
        # Test with invalid JOIN conditions
        sql_with_invalid_join = "SELECT e.employee_id, e.first_name, d.department_name FROM employees e JOIN departments d ON e.employee_id = d.department_name"
        schema_issues = self.validator._validate_schema(sql_with_invalid_join, self.test_schema)
        self.assertTrue(len(schema_issues) > 0)
        self.assertTrue(any("데이터 타입이 호환되지 않을" in issue for issue in schema_issues))
        
        # Test with ambiguous column
        sql_with_ambiguous_column = "SELECT employee_id FROM employees JOIN departments ON department_id = department_id"
        schema_issues = self.validator._validate_schema(sql_with_ambiguous_column, self.test_schema)
        self.assertTrue(len(schema_issues) > 0)
        
        # Test with similar column name suggestion
        sql_with_typo = "SELECT employe_id FROM employees"
        schema_issues = self.validator._validate_schema(sql_with_typo, self.test_schema)
        self.assertTrue(len(schema_issues) > 0)
        self.assertTrue(any("employee_id" in issue for issue in schema_issues))
    
    def test_performance_issues_advanced(self):
        """
        Test advanced performance issue detection.
        """
        # Test complex query with multiple performance issues
        complex_sql = """
        SELECT * 
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN locations l ON d.location_id = l.location_id
        LEFT JOIN countries c ON l.country_id = c.country_id
        LEFT JOIN regions r ON c.region_id = r.region_id
        WHERE UPPER(e.first_name) LIKE 'J%'
        AND YEAR(e.hire_date) > 2010
        OR e.salary > 5000
        OR e.salary > 6000
        OR e.salary > 7000
        OR e.salary > 8000
        GROUP BY e.department_id, e.job_id, e.manager_id, e.first_name, e.last_name
        ORDER BY e.department_id, e.job_id, e.salary DESC, e.first_name
        """
        
        warnings = self.validator._check_performance_issues(complex_sql, "mssql")
        self.assertTrue(len(warnings) >= 5)
        
        # Check specific performance warnings
        self.assertTrue(any("SELECT *" in warning for warning in warnings))
        self.assertTrue(any("JOIN" in warning for warning in warnings))
        self.assertTrue(any("OR" in warning for warning in warnings))
        self.assertTrue(any("ORDER BY" in warning for warning in warnings))
        self.assertTrue(any("GROUP BY" in warning for warning in warnings))
        self.assertTrue(any("UPPER" in warning for warning in warnings))
        self.assertTrue(any("NOLOCK" in warning for warning in warnings))
    
    def test_optimize_sql_basic(self):
        """
        Test basic SQL optimization.
        """
        # Test basic optimization
        sql = "SELECT   employee_id,   first_name,   last_name  FROM   employees  WHERE   department_id = 10"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "mssql")
        
        # Check formatting improvements
        self.assertNotEqual(sql, optimized_sql)
        self.assertTrue("불필요한 공백" in optimizations[0])
        
        # Check MS-SQL specific optimizations
        self.assertIn("WITH (NOLOCK)", optimized_sql)
        self.assertTrue(any("NOLOCK" in opt for opt in optimizations))
    
    @pytest.mark.asyncio
    async def test_optimize_sql_advanced(self):
        """
        Test advanced SQL optimization with LLM.
        """
        # Test with mock LLM service
        sql = "SELECT * FROM employees WHERE department_id = 10"
        optimized_sql, optimizations = await self.validator.optimize_sql(sql, "mssql", self.test_schema)
        
        # Check that LLM optimization was applied
        self.assertEqual(optimized_sql, "OPTIMIZED SQL")  # From mock
        self.assertTrue(any("LLM 기반 최적화" in opt for opt in optimizations))
        
        # Test error handling
        self.mock_llm_service.validate_and_fix_sql.side_effect = Exception("API Error")
        optimized_sql, optimizations = await self.validator.optimize_sql(sql, "mssql", self.test_schema)
        
        # Check that original query is returned on error
        self.assertNotEqual(optimized_sql, "OPTIMIZED SQL")
        self.assertTrue(any("실패" in opt for opt in optimizations))
    
    def test_is_similar(self):
        """
        Test string similarity function.
        """
        # Test exact match
        self.assertTrue(self.validator._is_similar("employee", "employee"))
        
        # Test substring
        self.assertTrue(self.validator._is_similar("employee", "employees"))
        
        # Test similar strings
        self.assertTrue(self.validator._is_similar("employee", "employe"))
        
        # Test dissimilar strings
        self.assertFalse(self.validator._is_similar("employee", "department"))
        
        # Test short strings
        self.assertFalse(self.validator._is_similar("id", "di"))
    
    def test_are_types_compatible(self):
        """
        Test data type compatibility function.
        """
        # Test exact match
        self.assertTrue(self.validator._are_types_compatible("INT", "INT"))
        
        # Test numeric types
        self.assertTrue(self.validator._are_types_compatible("INT", "BIGINT"))
        self.assertTrue(self.validator._are_types_compatible("DECIMAL", "FLOAT"))
        
        # Test string types
        self.assertTrue(self.validator._are_types_compatible("VARCHAR(50)", "NVARCHAR(100)"))
        self.assertTrue(self.validator._are_types_compatible("CHAR(10)", "TEXT"))
        
        # Test date types
        self.assertTrue(self.validator._are_types_compatible("DATE", "DATETIME"))
        self.assertTrue(self.validator._are_types_compatible("TIMESTAMP", "SMALLDATETIME"))
        
        # Test incompatible types
        self.assertFalse(self.validator._are_types_compatible("INT", "VARCHAR(50)"))
        self.assertFalse(self.validator._are_types_compatible("DATE", "FLOAT"))
    
    def test_extract_join_conditions(self):
        """
        Test JOIN condition extraction.
        """
        # Test simple JOIN
        sql = "SELECT * FROM employees e JOIN departments d ON e.department_id = d.department_id"
        conditions = self.validator._extract_join_conditions(sql)
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0], ("e.department_id", "d.department_id"))
        
        # Test multiple JOINs
        sql = """
        SELECT * FROM employees e 
        JOIN departments d ON e.department_id = d.department_id
        JOIN locations l ON d.location_id = l.location_id
        """
        conditions = self.validator._extract_join_conditions(sql)
        self.assertEqual(len(conditions), 2)
    
    def test_extract_null_comparisons(self):
        """
        Test NULL comparison extraction.
        """
        # Test IS NULL
        sql = "SELECT * FROM employees WHERE manager_id IS NULL"
        comparisons = self.validator._extract_null_comparisons(sql)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0], ("manager_id", "IS"))
        
        # Test IS NOT NULL
        sql = "SELECT * FROM employees WHERE manager_id IS NOT NULL"
        comparisons = self.validator._extract_null_comparisons(sql)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0], ("manager_id", "IS NOT"))
        
        # Test incorrect NULL comparison
        sql = "SELECT * FROM employees WHERE manager_id = NULL"
        comparisons = self.validator._extract_null_comparisons(sql)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0], ("manager_id", "="))

if __name__ == "__main__":
    unittest.main()