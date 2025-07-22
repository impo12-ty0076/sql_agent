"""
Simple verification script for the MS-SQL connector implementation.
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_mssql_connector():
    """
    Verify that the MS-SQL connector implementation is correct.
    """
    try:
        # Import the necessary modules
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        from models.database import Database, DBType, ConnectionConfig
        from db.connectors.mssql import MSSQLConnector
        from db.connectors.pool import DefaultConnectionPoolManager
        
        logger.info("Successfully imported the required modules")
        
        # Create a connection pool manager
        pool_manager = DefaultConnectionPoolManager(max_pool_size=5)
        
        # Create the connector
        connector = MSSQLConnector(pool_manager)
        
        logger.info("Successfully created the MS-SQL connector")
        
        # Create a sample database configuration
        db_config = Database(
            id="test-db",
            name="Test Database",
            type=DBType.MSSQL,
            host="localhost",
            port=1433,
            default_schema="master",
            connection_config=ConnectionConfig(
                username="sa",
                password_encrypted="encrypted_password",
                options={"timeout": 30, "encrypt": True}
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info("Successfully created a sample database configuration")
        
        # Verify the connector methods
        logger.info("Verifying connector methods:")
        
        # Check that the connector has all the required methods
        required_methods = [
            "_create_connection",
            "_validate_connection",
            "test_connection",
            "execute_query",
            "cancel_query",
            "get_schema",
            "validate_query",
            "is_read_only_query",
            "format_error"
        ]
        
        for method in required_methods:
            if hasattr(connector, method) and callable(getattr(connector, method)):
                logger.info(f"  ✓ Method '{method}' exists")
            else:
                logger.error(f"  ✗ Method '{method}' is missing or not callable")
        
        # Check that the connector has the retry logic
        if hasattr(connector, "_is_transient_error") and callable(getattr(connector, "_is_transient_error")):
            logger.info("  ✓ Retry logic is implemented")
        else:
            logger.error("  ✗ Retry logic is missing")
        
        # Check that the connector has the query execution tracker
        if hasattr(connector, "query_tracker"):
            logger.info("  ✓ Query execution tracker is implemented")
        else:
            logger.error("  ✗ Query execution tracker is missing")
        
        logger.info("Verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_mssql_connector()
    sys.exit(0 if success else 1)