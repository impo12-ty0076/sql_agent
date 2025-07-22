from typing import Dict, Any, List, Optional
from .database import Database, DBType, Schema, Table, Column, ForeignKey, DatabaseSchema
from datetime import datetime
import re

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
    
    products_table = Table(
        name="products",
        columns=[
            Column(name="product_id", type="int", nullable=False),
            Column(name="name", type="varchar(100)", nullable=False),
            Column(name="price", type="decimal(10,2)", nullable=False),
            Column(name="stock", type="int", nullable=False)
        ],
        primary_key=["product_id"],
        description="Product catalog"
    )
    
    order_items_table = Table(
        name="order_items",
        columns=[
            Column(name="order_id", type="int", nullable=False),
            Column(name="product_id", type="int", nullable=False),
            Column(name="quantity", type="int", nullable=False),
            Column(name="unit_price", type="decimal(10,2)", nullable=False)
        ],
        primary_key=["order_id", "product_id"],
        foreign_keys=[
            ForeignKey(
                columns=["order_id"],
                reference_table="orders",
                reference_columns=["order_id"]
            ),
            ForeignKey(
                columns=["product_id"],
                reference_table="products",
                reference_columns=["product_id"]
            )
        ],
        description="Items in each order"
    )
    
    # Create schema and add tables
    sales_schema = Schema(
        name="sales",
        tables=[customers_table, orders_table, products_table, order_items_table]
    )
    
    # Create database schema
    return DatabaseSchema(
        db_id=db_id,
        schemas=[sales_schema],
        last_updated=datetime.now()
    )