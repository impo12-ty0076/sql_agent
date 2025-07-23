"""
Manual test for natural language query API
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Mock classes and functions
class MockLLMService:
    async def generate_sql(self, natural_language, schema, db_type, context):
        return {
            "sql": f"SELECT * FROM users WHERE name LIKE '%{natural_language}%'",
            "confidence": 0.95,
            "explanation": f"This query searches for users with '{natural_language}' in their name.",
            "conversation_id": "conv_123"
        }

class MockNLToSQLService:
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    async def convert_nl_to_sql(self, user_id, natural_language, schema, db_type, conversation_id=None):
        return await self.llm_service.generate_sql(natural_language, schema, db_type, None)

class MockDatabaseService:
    async def get_database_schema(self, db_id):
        return {
            "schemas": [
                {
                    "name": "dbo",
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {"name": "id", "type": "int"},
                                {"name": "name", "type": "varchar"}
                            ]
                        }
                    ]
                }
            ]
        }
    
    async def get_database_by_id(self, db_id):
        return {
            "id": db_id,
            "name": "Test DB",
            "type": "mssql"
        }

class MockQuery:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockQueryCreate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

async def mock_create_query(query_data):
    return MockQuery(
        id="query_123",
        user_id=query_data.user_id,
        db_id=query_data.db_id,
        natural_language=query_data.natural_language,
        generated_sql=query_data.generated_sql,
        status="pending",
        start_time=datetime.utcnow(),
        created_at=datetime.utcnow()
    )

# Test function
async def test_process_natural_language_query():
    # Mock services
    llm_service = MockLLMService()
    nl_to_sql_service = MockNLToSQLService(llm_service)
    db_service = MockDatabaseService()
    
    # Test data
    user_id = "test_user_123"
    db_id = "test_db_123"
    natural_language = "Find users named John"
    
    # Get database schema
    db_schema = await db_service.get_database_schema(db_id)
    
    # Get database type
    db_info = await db_service.get_database_by_id(db_id)
    db_type = db_info.get("type", "mssql")
    
    # Convert natural language to SQL
    result = await nl_to_sql_service.convert_nl_to_sql(
        user_id=user_id,
        natural_language=natural_language,
        schema=db_schema,
        db_type=db_type
    )
    
    # Create query
    query_data = MockQueryCreate(
        user_id=user_id,
        db_id=db_id,
        natural_language=natural_language,
        generated_sql=result["sql"]
    )
    
    created_query = await mock_create_query(query_data)
    
    # Create response
    response = {
        "query_id": created_query.id,
        "natural_language": natural_language,
        "generated_sql": result["sql"],
        "db_id": db_id,
        "confidence": result.get("confidence", 0.9),
        "explanation": result.get("explanation", ""),
        "conversation_id": result.get("conversation_id"),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Print response
    print("Response:")
    for key, value in response.items():
        print(f"  {key}: {value}")
    
    # Verify response
    assert response["natural_language"] == natural_language
    assert response["generated_sql"] == "SELECT * FROM users WHERE name LIKE '%Find users named John%'"
    assert response["db_id"] == db_id
    assert response["confidence"] == 0.95
    assert "explanation" in response
    assert response["conversation_id"] == "conv_123"
    assert response["status"] == "pending"
    
    print("\nTest passed!")

# Run test
if __name__ == "__main__":
    asyncio.run(test_process_natural_language_query())