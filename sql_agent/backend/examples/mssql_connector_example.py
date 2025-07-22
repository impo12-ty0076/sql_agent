"""
Example usage of the MS-SQL connector.
This script demonstrates how to use the MS-SQL connector to connect to a database,
execute queries, and retrieve schema information.
"""

import logging
import os
from datetime import datetime

from sql_agent.backend.models.database import Database, DBType, ConnectionConfig
from sql_agent.backend.db.connectors.init_connectors import init_db_connectors, get_connector_factory
from sql_agent.backend.db.connectors.mssql import MSSQLConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mssql_connector_example():
    """
    Example of how to use the MS-SQL connector.
    """
    # Initialize database connectors
    init_db_connectors()
    
    # Get connection parameters from environment variables or use defaults
    host = os.environ.get("MSSQL_HOST", "localhost")
    port = int(os.environ.get("MSSQL_PORT", "1433"))
    database = os.environ.get("MSSQL_DATABASE", "master")
    username = os.environ.get("MSSQL_USERNAME", "sa")
    password = os.environ.get("MSSQL_PASSWORD", "YourStrong@Passw0rd")
    
    # Create a sample database configuration
    db_config = Database(
        id="mssql-example",
        name="MS-SQL Example",
        type=DBType.MSSQL,
        host=host,
        port=port,
        default_schema=database,
        connection_config=ConnectionConfig(
            username=username,
            password_encrypted=password,  # In a real implementation, this would be encrypted
            options={
                "timeout": 30,
                "encrypt": "yes",
                "trustservercertificate": "yes"
            }
        ),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Get the connector factory
    factory = get_connector_factory()
    
    try:
        # Create a connector for the database
        connector = factory.create_connector(db_config)
        
        # Test the connection
        logger.info("Testing connection to MS-SQL database...")
        success, message = connector.test_connection(db_config)
        if success:
            logger.info(f"Connection test successful: {message}")
        else:
            logger.error(f"Connection test failed: {message}")
            return
        
        # Get the database schema
        logger.info("Retrieving database schema...")
        schema = connector.get_schema(db_config)
        logger.info(f"Retrieved schema with {len(schema.schemas)} schemas")
        
        # Print some schema information
        for schema_obj in schema.schemas:
            logger.info(f"Schema: {schema_obj.name} with {len(schema_obj.tables)} tables")
            for table in schema_obj.tables[:5]:  # Show only first 5 tables
                logger.info(f"  Table: {table.name} with {len(table.columns)} columns")
                for column in table.columns[:3]:  # Show only first 3 columns
                    logger.info(f"    Column: {column.name} ({column.type})")
        
        # Execute a sample query
        logger.info("Executing sample query...")
        query = "SELECT TOP 10 * FROM sys.objects"
        result = connector.execute_query(db_config, query, max_rows=10)
        
        # Print query results
        logger.info(f"Query returned {result.row_count} rows")
        if result.columns:
            logger.info(f"Columns: {', '.join(col.name for col in result.columns)}")
        
        if result.rows:
            for i, row in enumerate(result.rows):
                if i < 3:  # Print only first 3 rows
                    logger.info(f"Row {i+1}: {row}")
            
            if result.row_count > 3:
                logger.info(f"... and {result.row_count - 3} more rows")
        
        # Execute a query with parameters
        logger.info("Executing parameterized query...")
        param_query = "SELECT * FROM sys.objects WHERE type = :obj_type"
        param_result = connector.execute_query(
            db_config, 
            param_query, 
            params={"obj_type": "U"},  # U = User table
            max_rows=5
        )
        
        logger.info(f"Parameterized query returned {param_result.row_count} rows")
        
        # Try to cancel a long-running query
        logger.info("Executing a long-running query and then cancelling it...")
        try:
            # Start a long-running query in a separate thread
            import threading
            import time
            
            def execute_long_query():
                try:
                    connector.execute_query(
                        db_config,
                        "WAITFOR DELAY '00:00:10'; SELECT * FROM sys.objects",  # 10-second delay
                        timeout=30
                    )
                except Exception as e:
                    logger.info(f"Long query was cancelled: {str(e)}")
            
            thread = threading.Thread(target=execute_long_query)
            thread.start()
            
            # Wait a bit and then cancel the query
            time.sleep(2)
            
            # Get the running queries
            running_queries = connector.query_tracker.get_running_queries()
            if running_queries:
                query_id = list(running_queries.keys())[0]
                logger.info(f"Cancelling query {query_id}...")
                cancelled = connector.cancel_query(query_id)
                logger.info(f"Query cancellation result: {cancelled}")
            else:
                logger.info("No running queries to cancel")
            
            # Wait for the thread to finish
            thread.join()
        
        except Exception as e:
            logger.error(f"Error in query cancellation example: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in MS-SQL connector example: {str(e)}")
    finally:
        # Close all connections
        factory.close_all_connections()
        logger.info("Closed all connections")

if __name__ == "__main__":
    mssql_connector_example()