class DatabaseError(Exception):
    """Base class for all database-related exceptions."""
    pass

class ConnectionError(DatabaseError):
    """Exception raised when a database connection fails."""
    def __init__(self, db_id: str, message: str):
        self.db_id = db_id
        self.message = message
        super().__init__(f"Failed to connect to database {db_id}: {message}")

class QueryError(DatabaseError):
    """Exception raised when a database query fails."""
    def __init__(self, query: str, message: str):
        self.query = query
        self.message = message
        super().__init__(f"Query failed: {message}")

class SchemaError(DatabaseError):
    """Exception raised when there's an issue with the database schema."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Schema error: {message}")

class UnsupportedDatabaseTypeError(DatabaseError):
    """Exception raised when an unsupported database type is used."""
    def __init__(self, db_type: str):
        self.db_type = db_type
        super().__init__(f"Unsupported database type: {db_type}")

class DatabasePermissionError(DatabaseError):
    """Exception raised when a user doesn't have permission to access a database resource."""
    def __init__(self, user_id: str, resource: str, action: str):
        self.user_id = user_id
        self.resource = resource
        self.action = action
        super().__init__(f"User {user_id} does not have permission to {action} on {resource}")