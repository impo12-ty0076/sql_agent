"""
Initialize and register database connectors.
"""

import logging
from typing import Dict, Any, Optional

from sql_agent.backend.models.database import DBType
from sql_agent.backend.db.connectors.factory import connector_factory
from sql_agent.backend.db.connectors.pool import DefaultConnectionPoolManager

# Import connector implementations
# In a real implementation, you would import all available connector implementations
try:
    from sql_agent.backend.db.connectors.mssql import MSSQLConnector
    MSSQL_AVAILABLE = True
except ImportError:
    MSSQL_AVAILABLE = False

try:
    # This is a placeholder - in a real implementation, you would import the actual SAP HANA connector
    from sql_agent.backend.db.connectors.hana import HANAConnector
    HANA_AVAILABLE = True
except ImportError:
    HANA_AVAILABLE = False

logger = logging.getLogger(__name__)

def init_db_connectors(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize and register database connectors.
    
    Args:
        config: Optional configuration dictionary
    """
    # Create connection pool manager
    pool_size = config.get("connection_pool_size", 10) if config else 10
    connection_timeout = config.get("connection_timeout", 600) if config else 600
    max_connection_age = config.get("max_connection_age", 3600) if config else 3600
    
    pool_manager = DefaultConnectionPoolManager(
        max_pool_size=pool_size,
        connection_timeout=connection_timeout,
        max_connection_age=max_connection_age
    )
    
    # Set the connection pool manager
    connector_factory.set_connection_pool_manager(pool_manager)
    
    # Register available connectors
    if MSSQL_AVAILABLE:
        connector_factory.register_connector(DBType.MSSQL.value, MSSQLConnector)
        logger.info("Registered MS-SQL connector")
    else:
        logger.warning("MS-SQL connector not available")
    
    if HANA_AVAILABLE:
        connector_factory.register_connector(DBType.HANA.value, HANAConnector)
        logger.info("Registered SAP HANA connector")
    else:
        logger.warning("SAP HANA connector not available")
    
    logger.info("Database connectors initialized")

def get_connector_factory():
    """
    Get the global connector factory instance.
    
    Returns:
        DBConnectorFactory instance
    """
    return connector_factory