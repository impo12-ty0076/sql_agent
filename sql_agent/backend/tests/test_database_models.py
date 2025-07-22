import pytest
from datetime import datetime
from pydantic import ValidationError

from sql_agent.backend.models.database import (
    Database, ConnectionConfig, DatabaseSchema,
    Schema, Table, Column, ForeignKey
)

def test_connection_config():
    # Valid connection config
    config = ConnectionConfig(
        username="dbuser",
        password_encrypted="encrypted_password",
        options={"timeout": 30, "encrypt": True}
    )
    assert config.username == "dbuser"
    assert config.password_encrypted == "encrypted_password"
    assert config.options["timeout"] == 30
    assert config.options["encrypt"] is True

def test_column():
    # Valid column
    column = Column(
        name="user_id",
        type="int",
        nullable=False,
        default_value=None,
        description="Primary key for users table"
    )
    assert column.name == "user_id"
    assert column.type == "int"
    assert column.nullable is False
    assert column.description == "Primary key for users table"

def test_foreign_key():
    # Valid foreign key
    fk = ForeignKey(
        columns=["order_id"],
        reference_table="orders",
        reference_columns=["id"]
    )
    assert fk.columns == ["order_id"]
    assert fk.reference_table == "orders"
    assert fk.reference_columns == ["id"]

def test_table():
    # Valid table
    table = Table(
        name="users",
        columns=[
            Column(name="id", type="int", nullable=False),
            Column(name="username", type="varchar", nullable=False),
            Column(name="email", type="varchar", nullable=True)
        ],
        primary_key=["id"],
        foreign_keys=[
            ForeignKey(
                columns=["role_id"],
                reference_table="roles",
                reference_columns=["id"]
            )
        ],
        description="Users table"
    )
    assert table.name == "users"
    assert len(table.columns) == 3
    assert table.primary_key == ["id"]
    assert len(table.foreign_keys) == 1
    assert table.description == "Users table"

def test_schema():
    # Valid schema
    schema = Schema(
        name="dbo",
        tables=[
            Table(
                name="users",
                columns=[Column(name="id", type="int", nullable=False)]
            ),
            Table(
                name="products",
                columns=[Column(name="id", type="int", nullable=False)]
            )
        ]
    )
    assert schema.name == "dbo"
    assert len(schema.tables) == 2
    assert schema.tables[0].name == "users"
    assert schema.tables[1].name == "products"

def test_database_schema():
    # Valid database schema
    now = datetime.now()
    db_schema = DatabaseSchema(
        db_id="db123",
        schemas=[
            Schema(
                name="dbo",
                tables=[
                    Table(
                        name="users",
                        columns=[Column(name="id", type="int", nullable=False)]
                    )
                ]
            )
        ],
        last_updated=now
    )
    assert db_schema.db_id == "db123"
    assert len(db_schema.schemas) == 1
    assert db_schema.schemas[0].name == "dbo"
    assert db_schema.last_updated == now

def test_database():
    # Valid database
    now = datetime.now()
    db = Database(
        id="db123",
        name="Production DB",
        type="mssql",
        host="db.example.com",
        port=1433,
        default_schema="dbo",
        connection_config=ConnectionConfig(
            username="dbuser",
            password_encrypted="encrypted_password"
        ),
        created_at=now,
        updated_at=now
    )
    assert db.id == "db123"
    assert db.name == "Production DB"
    assert db.type == "mssql"
    assert db.host == "db.example.com"
    assert db.port == 1433
    assert db.default_schema == "dbo"
    assert db.connection_config.username == "dbuser"
    assert db.created_at == now
    assert db.updated_at == now

    # Test with invalid port
    with pytest.raises(ValidationError):
        Database(
            id="db123",
            name="Production DB",
            type="mssql",
            host="db.example.com",
            port=-1,  # Invalid port
            default_schema="dbo",
            connection_config=ConnectionConfig(
                username="dbuser",
                password_encrypted="encrypted_password"
            ),
            created_at=now,
            updated_at=now
        )