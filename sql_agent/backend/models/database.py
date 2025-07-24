from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum

class DBType(str, Enum):
    MSSQL = "mssql"
    HANA = "hana"

class ConnectionConfig(BaseModel):
    """
    Configuration for database connection including credentials and options.
    """
    username: str
    password_encrypted: str
    options: Dict[str, Any] = {}
    
    @validator('options')
    def validate_options(cls, v):
        # Ensure common connection options have valid values
        if 'timeout' in v and (not isinstance(v['timeout'], int) or v['timeout'] <= 0):
            raise ValueError("Connection timeout must be a positive integer")
        if 'encrypt' in v and not isinstance(v['encrypt'], bool):
            raise ValueError("Encrypt option must be a boolean")
        return v

class Column(BaseModel):
    """
    Database column definition with type information and constraints.
    """
    name: str
    type: str
    nullable: bool
    default_value: Optional[Any] = None
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Column type cannot be empty")
        return v

class ForeignKey(BaseModel):
    """
    Foreign key relationship between tables.
    """
    columns: List[str]
    reference_table: str
    reference_columns: List[str]
    
    @validator('columns', 'reference_columns')
    def validate_columns(cls, v):
        if not v:
            raise ValueError("Column list cannot be empty")
        return v
    
    @validator('reference_table')
    def validate_reference_table(cls, v):
        if not v or not v.strip():
            raise ValueError("Reference table cannot be empty")
        return v

class Table(BaseModel):
    """
    Database table definition with columns, keys, and relationships.
    """
    name: str
    columns: List[Column]
    primary_key: List[str] = []
    foreign_keys: List[ForeignKey] = []
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Table name cannot be empty")
        return v
    
    @validator('columns')
    def validate_columns(cls, v):
        if not v:
            raise ValueError("Table must have at least one column")
        return v
    
    @validator('primary_key')
    def validate_primary_key(cls, v, values):
        if v:
            # Ensure all primary key columns exist in the columns list
            if 'columns' in values:
                column_names = {col.name for col in values['columns']}
                for pk_col in v:
                    if pk_col not in column_names:
                        raise ValueError(f"Primary key column '{pk_col}' not found in table columns")
        return v

class Schema(BaseModel):
    """
    Database schema containing tables.
    """
    name: str
    tables: List[Table] = []
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Schema name cannot be empty")
        return v

class DatabaseSchema(BaseModel):
    """
    Complete database schema information including all schemas and tables.
    """
    db_id: str
    schemas: List[Schema] = []
    last_updated: datetime
    
    @validator('db_id')
    def validate_db_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Database ID cannot be empty")
        return v
    
    def get_table(self, schema_name: str, table_name: str) -> Optional[Table]:
        """
        Get a table by schema and table name.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            
        Returns:
            Table object if found, None otherwise
        """
        for schema in self.schemas:
            if schema.name == schema_name:
                for table in schema.tables:
                    if table.name == table_name:
                        return table
        return None
    
    def get_all_tables(self) -> List[Dict[str, Any]]:
        """
        Get all tables across all schemas with their schema information.
        
        Returns:
            List of dictionaries with schema_name, table_name, and table object
        """
        result = []
        for schema in self.schemas:
            for table in schema.tables:
                result.append({
                    "schema_name": schema.name,
                    "table_name": table.name,
                    "table": table
                })
        return result

class Database(BaseModel):
    """
    Database connection information and metadata.
    """
    id: str
    name: str
    type: DBType
    host: str
    port: int = Field(..., gt=0, lt=65536)  # Valid port range
    default_schema: str
    connection_config: ConnectionConfig
    created_at: datetime
    updated_at: datetime
    
    @validator('id', 'name', 'default_schema')
    def validate_string_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v
    
    @validator('host')
    def validate_host(cls, v):
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        # Could add more validation for hostname format if needed
        return v
    
    def get_connection_string(self) -> str:
        """
        Generate a connection string based on the database type.
        
        Returns:
            Connection string for the database
        """
        if self.type == DBType.MSSQL:
            return f"Server={self.host},{self.port};Database={self.default_schema};User Id={self.connection_config.username};Password=<encrypted>"
        elif self.type == DBType.HANA:
            return f"hdbcli://{self.host}:{self.port}?databaseName={self.default_schema}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")

    class Config:
        from_attributes = True