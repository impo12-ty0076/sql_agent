"""
Unit tests for the SQL validator implementation.
"""

import unittest
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.llm.sql_validator import SQLValidator, SQLValidationLevel
from backend.llm.base import LLMService, LLMConfig, LLMProvider

class TestSQLValidatorImplementation(unittest.TestCase):
    """
    Tests for the SQL validator implementation.
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
    
    def test_apply_basic_optimizations_mssql(self):
        """
        Test basic SQL optimizations for MS-SQL.
        """
        # Test with MS-SQL
        sql = "SELECT   employee_id,   first_name,   last_name  FROM   employees  WHERE   department_id = 10"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "mssql")
        
        # Check formatting improvements
        self.assertNotEqual(sql, optimized_sql)
        self.assertTrue(any("불필요한 공백" in opt for opt in optimizations))
        
        # Check MS-SQL specific optimizations
        self.assertIn("WITH (NOLOCK)", optimized_sql)
        self.assertTrue(any("NOLOCK" in opt for opt in optimizations))
    
    def test_apply_basic_optimizations_hana(self):
        """
        Test basic SQL optimizations for SAP HANA.
        """
        # Test with SAP HANA
        sql = "SELECT employee_id, first_name FROM employees WHERE name LIKE '%John%'"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "hana")
        
        # Check SAP HANA specific optimizations
        self.assertIn("CONTAINS", optimized_sql)
        self.assertTrue(any("CONTAINS" in opt for opt in optimizations))
        
        # Check LIMIT addition
        self.assertIn("LIMIT 1000", optimized_sql)
        self.assertTrue(any("LIMIT" in opt for opt in optimizations))
        
        # Test with GROUP BY for PARALLEL hint
        sql = "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id"
        optimized_sql, optimizations = self.validator._apply_basic_optimizations(sql, "hana")
        
        # Check PARALLEL hint
        self.assertIn("/*+ PARALLEL", optimized_sql)
        self.assertTrue(any("PARALLEL" in opt for opt in optimizations))
    
    def test_check_performance_issues_mssql(self):
        """
        Test performance issue detection for MS-SQL.
        """
        # Test complex query with multiple performance issues
        complex_sql = """
        SELECT * 
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE UPPER(e.first_name) LIKE 'J%'
        AND e.salary > 5000
        OR e.salary > 6000
        GROUP BY e.department_id, e.job_id
        ORDER BY e.department_id, e.salary DESC
        """
        
        warnings = self.validator._check_performance_issues(complex_sql, "mssql")
        
        # Check specific performance warnings for MS-SQL
        self.assertTrue(any("SELECT *" in warning for warning in warnings))
        self.assertTrue(any("NOLOCK" in warning for warning in warnings))
        self.assertTrue(any("UPPER" in warning for warning in warnings))
        self.assertTrue(any("OR" in warning for warning in warnings))
    
    def test_check_performance_issues_hana(self):
        """
        Test performance issue detection for SAP HANA.
        """
        # Test complex query with multiple performance issues
        complex_sql = """
        SELECT e.employee_id, LOWER(e.first_name) as name, e.salary * 1.1 as new_salary
        FROM employees e
        WHERE e.first_name LIKE '%John%'
        ORDER BY new_salary DESC
        """
        
        warnings = self.validator._check_performance_issues(complex_sql, "hana")
        
        # Check specific performance warnings for SAP HANA
        self.assertTrue(any("LIKE '%" in warning for warning in warnings))
        self.assertTrue(any("LOWER" in warning for warning in warnings))
        self.assertTrue(any("계산 컬럼" in warning for warning in warnings))
    
    @pytest.mark.asyncio
    async def test_optimize_sql_with_llm(self):
        """
        Test SQL optimization with LLM service.
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
    
    @pytest.mark.asyncio
    async def test_optimize_sql_without_llm(self):
        """
        Test SQL optimization without LLM service.
        """
        # Create validator without LLM service
        validator_without_llm = SQLValidator()
        
        # Test basic optimization
        sql = "SELECT employee_id, first_name FROM employees WHERE department_id = 10"
        optimized_sql, optimizations = await validator_without_llm.optimize_sql(sql, "mssql", self.test_schema)
        
        # Check that basic optimizations were applied
        self.assertNotEqual(sql, optimized_sql)
        self.assertTrue(len(optimizations) > 0)
        self.assertIn("WITH (NOLOCK)", optimized_sql)

if __name__ == "__main__":
    unittest.main()