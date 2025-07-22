from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Set
import re

# Define the models directly in this file for testing
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

# Utility functions
def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize a database identifier (table name, column name, etc.) to prevent SQL injection.
    
    Args:
        identifier: The identifier to sanitize
        
    Returns:
        Sanitized identifier
    """
    # Remove any characters that aren't alphanumeric, underscore, or period
    return re.sub(r'[^\w\.]', '', identifier)

def get_db_dialect(db_type: DBType) -> str:
    """
    Get the SQL dialect for a database type.
    
    Args:
        db_type: The database type
        
    Returns:
        SQL dialect name
    """
    if db_type == DBType.MSSQL:
        return "tsql"
    elif db_type == DBType.HANA:
        return "hana"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def convert_query_between_dialects(query: str, source_dialect: str, target_dialect: str) -> str:
    """
    Convert a SQL query from one dialect to another.
    
    Args:
        query: The SQL query to convert
        source_dialect: Source SQL dialect
        target_dialect: Target SQL dialect
        
    Returns:
        Converted SQL query
    """
    # This is a simplified implementation that handles some common differences
    # between MS-SQL and SAP HANA
    
    if source_dialect == "tsql" and target_dialect == "hana":
        # Convert TOP to LIMIT
        query = re.sub(r'TOP\s+(\d+)', r'LIMIT \1', query, flags=re.IGNORECASE)
        
        # Convert GETDATE() to CURRENT_TIMESTAMP
        query = re.sub(r'GETDATE\(\)', 'CURRENT_TIMESTAMP', query, flags=re.IGNORECASE)
        
        # Convert ISNULL to IFNULL
        query = re.sub(r'ISNULL\(', 'IFNULL(', query, flags=re.IGNORECASE)
        
    elif source_dialect == "hana" and target_dialect == "tsql":
        # Convert LIMIT to TOP
        query = re.sub(r'LIMIT\s+(\d+)', r'TOP \1', query, flags=re.IGNORECASE)
        
        # Convert CURRENT_TIMESTAMP to GETDATE()
        query = re.sub(r'CURRENT_TIMESTAMP', 'GETDATE()', query, flags=re.IGNORECASE)
        
        # Convert IFNULL to ISNULL
        query = re.sub(r'IFNULL\(', 'ISNULL(', query, flags=re.IGNORECASE)
        
    return query

def create_sample_database_schema(db_id: str) -> DatabaseSchema:
    """
    Create a sample database schema for testing purposes.
    
    Args:
        db_id: Database ID
        
    Returns:
        Sample DatabaseSchema object
    """
    # Create a sample schema with some tables
    customers_table = Table(
        name="customers",
        columns=[
            Column(name="customer_id", type="int", nullable=False),
            Column(name="name", type="varchar(100)", nullable=False),
            Column(name="email", type="varchar(100)", nullable=True),
            Column(name="created_at", type="datetime", nullable=False)
        ],
        primary_key=["customer_id"],
        description="Customer information"
    )
    
    orders_table = Table(
        name="orders",
        columns=[
            Column(name="order_id", type="int", nullable=False),
            Column(name="customer_id", type="int", nullable=False),
            Column(name="order_date", type="datetime", nullable=False),
            Column(name="total_amount", type="decimal(10,2)", nullable=False)
        ],
        primary_key=["order_id"],
        foreign_keys=[
            ForeignKey(
                columns=["customer_id"],
                reference_table="customers",
                reference_columns=["customer_id"]
            )
        ],
        description="Customer orders"
    )
    
    # Create schema and add tables
    sales_schema = Schema(
        name="sales",
        tables=[customers_table, orders_table]
    )
    
    # Create database schema
    return DatabaseSchema(
        db_id=db_id,
        schemas=[sales_schema],
        last_updated=datetime.now()
    )

def test_database_models():
    print("Testing database models...")
    
    try:
        # Test ConnectionConfig
        config = ConnectionConfig(
            username="dbuser",
            password_encrypted="encrypted_password",
            options={"timeout": 30, "encrypt": True}
        )
        print(f"ConnectionConfig created successfully")
        
        # Test invalid options
        try:
            invalid_config = ConnectionConfig(
                username="dbuser",
                password_encrypted="encrypted_password",
                options={"timeout": -1}  # Invalid timeout
            )
            print("ERROR: Should have raised validation error for negative timeout")
        except ValueError as e:
            print(f"Correctly caught validation error: {e}")
        
        # Test Column
        column = Column(
            name="user_id",
            type="int",
            nullable=False,
            description="Primary key for users table"
        )
        print(f"Column created successfully")
        
        # Test ForeignKey
        fk = ForeignKey(
            columns=["order_id"],
            reference_table="orders",
            reference_columns=["id"]
        )
        print(f"ForeignKey created successfully")
        
        # Test Table
        table = Table(
            name="users",
            columns=[
                Column(name="id", type="int", nullable=False),
                Column(name="username", type="varchar", nullable=False),
                Column(name="email", type="varchar", nullable=True)
            ],
            primary_key=["id"],
            description="Users table"
        )
        print(f"Table created successfully")
        
        # Test invalid primary key
        try:
            invalid_table = Table(
                name="users",
                columns=[
                    Column(name="id", type="int", nullable=False),
                ],
                primary_key=["non_existent_column"],  # Column doesn't exist
            )
            print("ERROR: Should have raised validation error for non-existent primary key column")
        except ValueError as e:
            print(f"Correctly caught validation error: {e}")
        
        # Test Schema
        schema = Schema(
            name="dbo",
            tables=[table]
        )
        print(f"Schema created successfully")
        
        # Test DatabaseSchema
        now = datetime.now()
        db_schema = DatabaseSchema(
            db_id="db123",
            schemas=[schema],
            last_updated=now
        )
        print(f"DatabaseSchema created successfully")
        
        # Test get_table method
        found_table = db_schema.get_table("dbo", "users")
        if found_table is not None:
            print(f"get_table method works correctly")
        else:
            print(f"ERROR: get_table method failed to find the table")
        
        # Test get_all_tables method
        all_tables = db_schema.get_all_tables()
        if len(all_tables) == 1 and all_tables[0]["table_name"] == "users":
            print(f"get_all_tables method works correctly")
        else:
            print(f"ERROR: get_all_tables method returned incorrect results")
        
        # Test Database
        db = Database(
            id="db123",
            name="Production DB",
            type=DBType.MSSQL,
            host="db.example.com",
            port=1433,
            default_schema="dbo",
            connection_config=config,
            created_at=now,
            updated_at=now
        )
        print(f"Database created successfully")
        
        # Test invalid port
        try:
            invalid_db = Database(
                id="db123",
                name="Production DB",
                type=DBType.MSSQL,
                host="db.example.com",
                port=70000,  # Invalid port
                default_schema="dbo",
                connection_config=config,
                created_at=now,
                updated_at=now
            )
            print("ERROR: Should have raised validation error for invalid port")
        except ValueError as e:
            print(f"Correctly caught validation error for invalid port")
        
        # Test get_connection_string method
        conn_str = db.get_connection_string()
        if "Server=db.example.com,1433" in conn_str:
            print(f"get_connection_string method works correctly for MSSQL")
        else:
            print(f"ERROR: get_connection_string method returned incorrect string for MSSQL")
        
        # Test HANA connection string
        hana_db = Database(
            id="hana123",
            name="HANA DB",
            type=DBType.HANA,
            host="hana.example.com",
            port=30015,
            default_schema="SYSTEM",
            connection_config=config,
            created_at=now,
            updated_at=now
        )
        hana_conn_str = hana_db.get_connection_string()
        if "hdbcli://hana.example.com:30015" in hana_conn_str:
            print(f"get_connection_string method works correctly for HANA")
        else:
            print(f"ERROR: get_connection_string method returned incorrect string for HANA")
        
        # Test utility functions
        sanitized = sanitize_identifier("my-table;drop")
        if sanitized == "mytabledrop":
            print(f"sanitize_identifier works correctly")
        else:
            print(f"ERROR: sanitize_identifier returned incorrect result: {sanitized}")
        
        dialect = get_db_dialect(DBType.MSSQL)
        if dialect == "tsql":
            print(f"get_db_dialect works correctly")
        else:
            print(f"ERROR: get_db_dialect returned incorrect result: {dialect}")
        
        # Test query conversion
        mssql_query = "SELECT TOP 10 * FROM users WHERE created_date > GETDATE()"
        hana_query = convert_query_between_dialects(mssql_query, "tsql", "hana")
        if "LIMIT 10" in hana_query and "CURRENT_TIMESTAMP" in hana_query:
            print(f"convert_query_between_dialects works correctly")
        else:
            print(f"ERROR: convert_query_between_dialects returned incorrect result: {hana_query}")
        
        # Test sample schema creation
        sample_schema = create_sample_database_schema("sample_db")
        if len(sample_schema.schemas) > 0 and len(sample_schema.schemas[0].tables) > 0:
            print(f"create_sample_database_schema works correctly")
        else:
            print(f"ERROR: create_sample_database_schema failed to create tables")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")

if __name__ == "__main__":
    test_database_models()