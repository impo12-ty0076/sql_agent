"""
Connection pool manager implementation for database connectors.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from threading import Lock
from datetime import datetime, timedelta

from sql_agent.backend.models.database import Database
from sql_agent.backend.db.connectors.base import ConnectionPoolManager

logger = logging.getLogger(__name__)

class PooledConnection:
    """
    Wrapper for a database connection with metadata for pool management.
    """
    def __init__(self, connection: Any, db_id: str):
        self.connection = connection
        self.db_id = db_id
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self.in_use = False
        self.use_count = 0

class DefaultConnectionPoolManager(ConnectionPoolManager):
    """
    Default implementation of the connection pool manager.
    
    Features:
    - Connection pooling with configurable pool size
    - Connection reuse and timeout
    - Connection health check
    - Pool statistics
    """
    
    def __init__(self, max_pool_size: int = 10, connection_timeout: int = 600, 
                 max_connection_age: int = 3600):
        """
        Initialize the connection pool manager.
        
        Args:
            max_pool_size: Maximum number of connections per database
            connection_timeout: Connection idle timeout in seconds
            max_connection_age: Maximum connection age in seconds
        """
        self.pools: Dict[str, List[PooledConnection]] = {}  # db_id -> list of connections
        self.max_pool_size = max_pool_size
        self.connection_timeout = connection_timeout
        self.max_connection_age = max_connection_age
        self.lock = Lock()
        self.connection_creators: Dict[str, callable] = {}  # db_type -> connection creator function
        self.connection_validators: Dict[str, callable] = {}  # db_type -> connection validator function
    
    def register_connection_creator(self, db_type: str, creator_func: callable) -> None:
        """
        Register a connection creator function for a database type.
        
        Args:
            db_type: Database type (e.g., 'mssql', 'hana')
            creator_func: Function that creates a new connection
        """
        self.connection_creators[db_type] = creator_func
    
    def register_connection_validator(self, db_type: str, validator_func: callable) -> None:
        """
        Register a connection validator function for a database type.
        
        Args:
            db_type: Database type (e.g., 'mssql', 'hana')
            validator_func: Function that validates a connection is still valid
        """
        self.connection_validators[db_type] = validator_func
    
    def _create_new_connection(self, db_config: Database) -> Any:
        """
        Create a new database connection.
        
        Args:
            db_config: Database configuration
            
        Returns:
            New database connection
            
        Raises:
            ValueError: If no connection creator is registered for the database type
        """
        db_type = db_config.type.value
        if db_type not in self.connection_creators:
            raise ValueError(f"No connection creator registered for database type: {db_type}")
        
        creator_func = self.connection_creators[db_type]
        return creator_func(db_config)
    
    def _is_connection_valid(self, connection: Any, db_config: Database) -> bool:
        """
        Check if a connection is still valid.
        
        Args:
            connection: Database connection
            db_config: Database configuration
            
        Returns:
            True if the connection is valid, False otherwise
        """
        db_type = db_config.type.value
        if db_type not in self.connection_validators:
            # If no validator is registered, assume the connection is valid
            return True
        
        validator_func = self.connection_validators[db_type]
        try:
            return validator_func(connection)
        except Exception as e:
            logger.warning(f"Connection validation failed: {str(e)}")
            return False
    
    def get_connection(self, db_config: Database) -> Any:
        """
        Get a connection from the pool or create a new one if needed.
        
        Args:
            db_config: Database configuration
            
        Returns:
            Database connection object
        """
        db_id = db_config.id
        
        with self.lock:
            # Initialize pool for this database if it doesn't exist
            if db_id not in self.pools:
                self.pools[db_id] = []
            
            # Clean up expired connections
            self._cleanup_expired_connections(db_id)
            
            # Try to find an available connection in the pool
            for pooled_conn in self.pools[db_id]:
                if not pooled_conn.in_use:
                    # Check if the connection is still valid
                    if self._is_connection_valid(pooled_conn.connection, db_config):
                        pooled_conn.in_use = True
                        pooled_conn.last_used_at = datetime.now()
                        pooled_conn.use_count += 1
                        return pooled_conn.connection
                    else:
                        # Remove invalid connection from the pool
                        self.pools[db_id].remove(pooled_conn)
            
            # If we reach here, no available connection was found
            # Check if we can create a new connection
            if len(self.pools[db_id]) < self.max_pool_size:
                # Create a new connection
                try:
                    new_connection = self._create_new_connection(db_config)
                    pooled_conn = PooledConnection(new_connection, db_id)
                    pooled_conn.in_use = True
                    pooled_conn.use_count = 1
                    self.pools[db_id].append(pooled_conn)
                    return new_connection
                except Exception as e:
                    logger.error(f"Failed to create new connection for database {db_id}: {str(e)}")
                    raise
            else:
                # Pool is full, wait for a connection to become available
                logger.warning(f"Connection pool for database {db_id} is full")
                raise RuntimeError(f"Connection pool for database {db_id} is full")
    
    def release_connection(self, connection: Any, db_id: str) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: Database connection object
            db_id: Database identifier
        """
        with self.lock:
            if db_id not in self.pools:
                logger.warning(f"Attempted to release connection for unknown database: {db_id}")
                return
            
            for pooled_conn in self.pools[db_id]:
                if pooled_conn.connection == connection:
                    pooled_conn.in_use = False
                    pooled_conn.last_used_at = datetime.now()
                    return
            
            logger.warning(f"Attempted to release unknown connection for database: {db_id}")
    
    def close_all_connections(self, db_id: Optional[str] = None) -> None:
        """
        Close all connections in the pool for a specific database or all databases.
        
        Args:
            db_id: Optional database identifier. If None, close all connections.
        """
        with self.lock:
            if db_id is not None:
                # Close connections for a specific database
                if db_id in self.pools:
                    for pooled_conn in self.pools[db_id]:
                        try:
                            pooled_conn.connection.close()
                        except Exception as e:
                            logger.warning(f"Error closing connection: {str(e)}")
                    self.pools[db_id] = []
            else:
                # Close all connections for all databases
                for db_id, connections in self.pools.items():
                    for pooled_conn in connections:
                        try:
                            pooled_conn.connection.close()
                        except Exception as e:
                            logger.warning(f"Error closing connection: {str(e)}")
                self.pools = {}
    
    def get_pool_stats(self, db_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the connection pool.
        
        Args:
            db_id: Optional database identifier. If None, get stats for all pools.
            
        Returns:
            Dictionary with pool statistics
        """
        with self.lock:
            stats = {}
            
            if db_id is not None:
                # Get stats for a specific database
                if db_id in self.pools:
                    total_connections = len(self.pools[db_id])
                    active_connections = sum(1 for conn in self.pools[db_id] if conn.in_use)
                    idle_connections = total_connections - active_connections
                    
                    stats[db_id] = {
                        "total_connections": total_connections,
                        "active_connections": active_connections,
                        "idle_connections": idle_connections,
                        "pool_utilization": active_connections / self.max_pool_size if self.max_pool_size > 0 else 0
                    }
            else:
                # Get stats for all databases
                for db_id, connections in self.pools.items():
                    total_connections = len(connections)
                    active_connections = sum(1 for conn in connections if conn.in_use)
                    idle_connections = total_connections - active_connections
                    
                    stats[db_id] = {
                        "total_connections": total_connections,
                        "active_connections": active_connections,
                        "idle_connections": idle_connections,
                        "pool_utilization": active_connections / self.max_pool_size if self.max_pool_size > 0 else 0
                    }
            
            return stats
    
    def _cleanup_expired_connections(self, db_id: str) -> None:
        """
        Clean up expired connections for a database.
        
        Args:
            db_id: Database identifier
        """
        now = datetime.now()
        timeout_threshold = now - timedelta(seconds=self.connection_timeout)
        age_threshold = now - timedelta(seconds=self.max_connection_age)
        
        # Filter out expired connections
        active_connections = []
        for pooled_conn in self.pools[db_id]:
            if pooled_conn.in_use:
                # Keep active connections
                active_connections.append(pooled_conn)
            elif (pooled_conn.last_used_at < timeout_threshold or 
                  pooled_conn.created_at < age_threshold):
                # Close expired connections
                try:
                    pooled_conn.connection.close()
                except Exception as e:
                    logger.warning(f"Error closing expired connection: {str(e)}")
            else:
                # Keep valid idle connections
                active_connections.append(pooled_conn)
        
        self.pools[db_id] = active_connections