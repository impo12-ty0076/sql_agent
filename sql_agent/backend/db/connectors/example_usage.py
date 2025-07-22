"""
Example usage of the database connector interface.
This is for demonstration purposes only and not part of the actual implementation.
"""

import logging
from datetime import datetime

from sql_agent.backend.models.database import Database, DBType, ConnectionConfig
from sql_agent.backend.db.connectors.init_connectors import init_db_connectors, get_connector_factory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_usage():
    """
    Example of how to use the database connector interface.
    """
    # Initialize database connectors
    init_db_connectors()
    
    # Create a sample database configuration
    db_config = Database(
        id="sample-db",
        name="Sample Database",
        type=DBType.MSSQL,
        host="localhost",
        port=1433,
        default_schema="master",
        connection_config=ConnectionConfig(
            username="sa",
            password_encrypted="encrypted_password",  # In a real implementation, this would be encrypted
            options={"timeout": 30, "encrypt": True}
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
        success, message = connector.test_connection(db_config)
        if success:
            logger.info(f"Connection test successful: {message}")
        else:
            logger.error(f"Connection test failed: {message}")
            return
        
        # Get the database schema
        schema = connector.get_schema(db_config)
        logger.info(f"Retrieved schema with {len(schema.schemas)} schemas")
        
        # Print some schema information
        for schema_obj in schema.schemas:
            logger.info(f"Schema: {schema_obj.name} with {len(schema_obj.tables)} tables")
            for table in schema_obj.tables:
                logger.info(f"  Table: {table.name} with {len(table.columns)} columns")
        
        # Execute a sample query
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
    
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
    finally:
        # Close all connections
        factory.close_all_connections()
        logger.info("Closed all connections")

if __name__ == "__main__":
    example_usage()