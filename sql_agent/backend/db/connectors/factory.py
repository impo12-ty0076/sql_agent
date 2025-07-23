"""
Factory for creating database connectors based on database type.
"""

import logging
from typing import Dict, Type, Optional

from ...models.database import Database, DBType
from .base import DBConnector, ConnectionPoolManager
from .pool import DefaultConnectionPoolManager
from .query_executor import QueryExecutionTracker

logger = logging.getLogger(__name__)

class DBConnectorFactory:
    """
    Factory for creating database connectors based on database type.
    """
    
    def __init__(self):
        """
        Initialize the database connector factory.
        """
        self._connector_classes: Dict[str, Type[DBConnector]] = {}
        self._connection_pool_manager: Optional[ConnectionPoolManager] = None
        self._query_tracker = QueryExecutionTracker()
    
    def register_connector(self, db_type: str, connector_class: Type[DBConnector]) -> None:
        """
        Register a connector class for a database type.
        
        Args:
            db_type: Database type (e.g., 'mssql', 'hana')
            connector_class: DBConnector class for the database type
        """
        self._connector_classes[db_type] = connector_class
        logger.info(f"Registered connector class for database type: {db_type}")
    
    def set_connection_pool_manager(self, pool_manager: ConnectionPoolManager) -> None:
        """
        Set the connection pool manager to use for all connectors.
        
        Args:
            pool_manager: Connection pool manager instance
        """
        self._connection_pool_manager = pool_manager
        logger.info(f"Set connection pool manager: {pool_manager.__class__.__name__}")
    
    def get_connection_pool_manager(self) -> ConnectionPoolManager:
        """
        Get the connection pool manager.
        
        Returns:
            Connection pool manager instance
        """
        if self._connection_pool_manager is None:
            # Create default connection pool manager if none is set
            self._connection_pool_manager = DefaultConnectionPoolManager()
            logger.info("Created default connection pool manager")
        
        return self._connection_pool_manager
    
    def get_query_tracker(self) -> QueryExecutionTracker:
        """
        Get the query execution tracker.
        
        Returns:
            QueryExecutionTracker instance
        """
        return self._query_tracker
    
    def create_connector(self, db_config: Database) -> DBConnector:
        """
        Create a database connector for the specified database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            DBConnector instance
            
        Raises:
            ValueError: If no connector is registered for the database type
        """
        db_type = db_config.type.value
        
        if db_type not in self._connector_classes:
            raise ValueError(f"No connector registered for database type: {db_type}")
        
        connector_class = self._connector_classes[db_type]
        pool_manager = self.get_connection_pool_manager()
        
        connector = connector_class(pool_manager)
        logger.info(f"Created connector for database: {db_config.name} (type: {db_type})")
        
        return connector
    
    def close_all_connections(self) -> None:
        """
        Close all database connections.
        """
        if self._connection_pool_manager:
            self._connection_pool_manager.close_all_connections()
            logger.info("Closed all database connections")

# Global instance of the connector factory
connector_factory = DBConnectorFactory()