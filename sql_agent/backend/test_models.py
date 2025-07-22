from datetime import datetime
from models.database import (
    Database, ConnectionConfig, DatabaseSchema,
    Schema, Table, Column, ForeignKey, DBType
)
from models.database_utils import (
    sanitize_identifier,
    get_db_dialect,
    convert_query_between_dialects,
    create_sample_database_schema
)

def test_database_models():
    print("Testing database models...")
    
    # Test ConnectionConfig
    config = ConnectionConfig(
        username="dbuser",
        password_encrypted="encrypted_password",
        options={"timeout": 30, "encrypt": True}
    )
    print(f"ConnectionConfig: {config}")
    
    # Test Column
    column = Column(
        name="user_id",
        type="int",
        nullable=False,
        description="Primary key for users table"
    )
    print(f"Column: {column}")
    
    # Test ForeignKey
    fk = ForeignKey(
        columns=["order_id"],
        reference_table="orders",
        reference_columns=["id"]
    )
    print(f"ForeignKey: {fk}")
    
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
    print(f"Table: {table}")
    
    # Test Schema
    schema = Schema(
        name="dbo",
        tables=[table]
    )
    print(f"Schema: {schema}")
    
    # Test DatabaseSchema
    now = datetime.now()
    db_schema = DatabaseSchema(
        db_id="db123",
        schemas=[schema],
        last_updated=now
    )
    print(f"DatabaseSchema: {db_schema}")
    
    # Test get_table method
    found_table = db_schema.get_table("dbo", "users")
    print(f"Found table: {found_table is not None}")
    
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
    print(f"Database: {db}")
    
    # Test get_connection_string method
    conn_str = db.get_connection_string()
    print(f"Connection string: {conn_str}")
    
    # Test utility functions
    print(f"Sanitized identifier: {sanitize_identifier('my-table;drop')}")
    print(f"DB dialect: {get_db_dialect(DBType.MSSQL)}")
    
    # Test query conversion
    mssql_query = "SELECT TOP 10 * FROM users WHERE created_date > GETDATE()"
    hana_query = convert_query_between_dialects(mssql_query, "tsql", "hana")
    print(f"Converted query: {hana_query}")
    
    # Test sample schema creation
    sample_schema = create_sample_database_schema("sample_db")
    print(f"Sample schema tables: {len(sample_schema.get_all_tables())}")
    
    print("All tests passed!")

if __name__ == "__main__":
    test_database_models()