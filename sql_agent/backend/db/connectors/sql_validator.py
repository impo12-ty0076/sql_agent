"""
SQL query validation utilities for database connectors.
"""

import re
import logging
from typing import Tuple, Optional, List, Set

logger = logging.getLogger(__name__)

class SQLValidator:
    """
    Validates SQL queries for safety and correctness.
    """
    
    # SQL keywords that modify data
    _MODIFY_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 
        'RENAME', 'REPLACE', 'MERGE', 'UPSERT', 'GRANT', 'REVOKE', 'EXEC', 
        'EXECUTE', 'CALL', 'WITH'
    }
    
    # SQL keywords for read-only operations
    _READ_KEYWORDS = {
        'SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'HELP'
    }
    
    @classmethod
    def is_read_only_query(cls, query: str) -> bool:
        """
        Check if a query is read-only (SELECT, SHOW, DESCRIBE, etc.).
        
        Args:
            query: SQL query string
            
        Returns:
            True if the query is read-only, False otherwise
        """
        # Remove comments and normalize whitespace
        clean_query = cls._remove_comments(query).strip()
        
        # Empty query is not valid
        if not clean_query:
            return False
        
        # Get the first keyword
        first_word = clean_query.split(None, 1)[0].upper()
        
        # Check if it's a read-only keyword
        if first_word in cls._READ_KEYWORDS:
            # Special case for WITH which could be a CTE (Common Table Expression)
            if first_word == 'WITH':
                # Check if it's a WITH followed by a read-only operation
                # This is a simplified check and might not catch all cases
                cte_pattern = r'WITH\s+.+?\s+AS\s+\(.+?\)\s+(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)'
                if re.search(cte_pattern, clean_query, re.IGNORECASE | re.DOTALL):
                    return True
                return False
            return True
        
        # Check if it's a modifying keyword
        if first_word in cls._MODIFY_KEYWORDS:
            return False
        
        # If we can't determine, assume it's not read-only for safety
        return False
    
    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for basic syntax and safety.
        
        Args:
            query: SQL query string
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Check if query is empty
        if not query or not query.strip():
            return False, "Query is empty"
        
        # Remove comments and normalize whitespace
        clean_query = cls._remove_comments(query).strip()
        
        # Check for semicolon-separated multiple statements
        if ';' in clean_query[:-1]:  # Allow trailing semicolon
            statements = [stmt.strip() for stmt in clean_query.split(';') if stmt.strip()]
            if len(statements) > 1:
                return False, "Multiple SQL statements are not allowed"
        
        # Check if query is read-only
        if not cls.is_read_only_query(clean_query):
            return False, "Only read-only queries are allowed"
        
        # Check for common SQL injection patterns
        if cls._contains_injection_patterns(clean_query):
            return False, "Query contains potential SQL injection patterns"
        
        return True, None
    
    @staticmethod
    def _remove_comments(query: str) -> str:
        """
        Remove SQL comments from a query.
        
        Args:
            query: SQL query string
            
        Returns:
            Query string with comments removed
        """
        # Remove /* ... */ comments
        query = re.sub(r'/\*.*?\*/', ' ', query, flags=re.DOTALL)
        
        # Remove -- comments
        query = re.sub(r'--.*?(\n|$)', ' ', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    @staticmethod
    def _contains_injection_patterns(query: str) -> bool:
        """
        Check for common SQL injection patterns.
        
        Args:
            query: SQL query string
            
        Returns:
            True if potential injection patterns are found, False otherwise
        """
        # This is a simplified check and not comprehensive
        patterns = [
            r';\s*--',  # SQL comment after semicolon
            r';\s*\/\*',  # SQL comment after semicolon
            r'UNION\s+ALL\s+SELECT',  # UNION-based injection
            r'OR\s+1\s*=\s*1',  # OR 1=1 injection
            r'OR\s+\'1\'\s*=\s*\'1\'',  # OR '1'='1' injection
            r'DROP\s+TABLE',  # DROP TABLE
            r'DELETE\s+FROM',  # DELETE FROM
            r'INSERT\s+INTO',  # INSERT INTO
            r'EXEC\s*\(',  # EXEC() function
            r'EXECUTE\s*\(',  # EXECUTE() function
            r'xp_cmdshell',  # xp_cmdshell (SQL Server)
            r'sp_execute',  # sp_execute (SQL Server)
        ]
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False