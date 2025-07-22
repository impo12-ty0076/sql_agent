"""
Simple test script for database API.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

# Simple test class
class DatabaseService:
    @staticmethod
    async def get_user_databases(user_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": "db1",
                "name": "Sample MS-SQL DB",
                "type": "mssql",
                "host": "localhost",
                "port": 1433,
            },
            {
                "id": "db2",
                "name": "Sample SAP HANA DB",
                "type": "hana",
                "host": "localhost",
                "port": 30015,
            }
        ]
    
    @staticmethod
    async def connect_database(db_id: str, user_id: str) -> Dict[str, Any]:
        if db_id not in ["db1", "db2"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database with ID {db_id} not found"
            )
        
        return {
            "status": "connected",
            "db_id": db_id,
            "connection_id": f"conn_{user_id}_{db_id}",
        }
    
    @staticmethod
    async def get_database_schema(db_id: str, user_id: str) -> Dict[str, Any]:
        if db_id not in ["db1", "db2"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database with ID {db_id} not found"
            )
        
        return {
            "db_id": db_id,
            "schemas": [
                {
                    "name": "sales",
                    "tables": [
                        {
                            "name": "customers",
                            "columns": [
                                {"name": "customer_id", "type": "int", "nullable": False},
                                {"name": "name", "type": "varchar(100)", "nullable": False},
                            ],
                            "primary_key": ["customer_id"],
                        }
                    ]
                }
            ]
        }

async def test_database_service():
    print("Testing DatabaseService...")
    
    # Test get_user_databases
    dbs = await DatabaseService.get_user_databases("test_user_id")
    print(f"Found {len(dbs)} databases")
    
    # Test connect_database
    try:
        conn = await DatabaseService.connect_database("db1", "test_user_id")
        print(f"Connected to database: {conn['db_id']}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test get_database_schema
    try:
        schema = await DatabaseService.get_database_schema("db1", "test_user_id")
        print(f"Got schema for database: {schema['db_id']}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_database_service())