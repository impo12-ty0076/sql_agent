"""
CRUD operations for query result models
"""
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete

from ...db.session import get_session
from ...models.query import QueryResult, QueryResultCreate

async def create_query_result(result_data: QueryResultCreate) -> QueryResult:
    """
    Create a new query result record
    
    Args:
        result_data: Query result data to create
        
    Returns:
        Created query result
    """
    async with get_session() as session:
        # Create query result object
        result = QueryResult(
            id=str(uuid.uuid4()),
            query_id=result_data.query_id,
            columns=result_data.columns,
            rows=result_data.rows,
            row_count=result_data.row_count,
            truncated=result_data.truncated,
            total_row_count=result_data.total_row_count,
            summary=result_data.summary,
            created_at=datetime.utcnow()
        )
        
        # Add to session and commit
        session.add(result)
        await session.commit()
        await session.refresh(result)
        
        return result

async def get_query_result_by_id(result_id: str) -> Optional[QueryResult]:
    """
    Get query result by ID
    
    Args:
        result_id: Query result ID
        
    Returns:
        Query result if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(QueryResult).where(QueryResult.id == result_id)
        )
        return result.scalars().first()

async def get_query_result_by_query_id(query_id: str) -> Optional[QueryResult]:
    """
    Get query result by query ID
    
    Args:
        query_id: Query ID
        
    Returns:
        Query result if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(QueryResult).where(QueryResult.query_id == query_id)
        )
        return result.scalars().first()

async def update_query_result_summary(result_id: str, summary: str) -> Optional[QueryResult]:
    """
    Update query result summary
    
    Args:
        result_id: Query result ID
        summary: Summary text
        
    Returns:
        Updated query result if found, None otherwise
    """
    async with get_session() as session:
        # Update query result
        await session.execute(
            sql_update(QueryResult)
            .where(QueryResult.id == result_id)
            .values(summary=summary)
        )
        
        await session.commit()
        
        # Get updated query result
        result = await session.execute(
            select(QueryResult).where(QueryResult.id == result_id)
        )
        return result.scalars().first()

async def delete_query_result(result_id: str) -> bool:
    """
    Delete query result
    
    Args:
        result_id: Query result ID
        
    Returns:
        True if query result was deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(QueryResult).where(QueryResult.id == result_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0