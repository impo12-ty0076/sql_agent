"""
CRUD operations for query models
"""
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete

from ...db.session import get_session
from ...models.query import QueryCreate, QueryUpdate, Query, QueryStatus

async def create_query(query_data: QueryCreate) -> Query:
    """
    Create a new query record
    
    Args:
        query_data: Query data to create
        
    Returns:
        Created query
    """
    async with get_session() as session:
        # Create query object
        query = Query(
            id=str(uuid.uuid4()),
            user_id=query_data.user_id,
            db_id=query_data.db_id,
            natural_language=query_data.natural_language,
            generated_sql=query_data.generated_sql,
            executed_sql=query_data.executed_sql,
            status=QueryStatus.PENDING,
            start_time=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        # Add to session and commit
        session.add(query)
        await session.commit()
        await session.refresh(query)
        
        return query

async def get_query_by_id(query_id: str) -> Optional[Query]:
    """
    Get query by ID
    
    Args:
        query_id: Query ID
        
    Returns:
        Query if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(Query).where(Query.id == query_id)
        )
        return result.scalars().first()

async def get_queries_by_user(user_id: str, limit: int = 100, offset: int = 0) -> List[Query]:
    """
    Get queries by user ID
    
    Args:
        user_id: User ID
        limit: Maximum number of queries to return
        offset: Offset for pagination
        
    Returns:
        List of queries
    """
    async with get_session() as session:
        result = await session.execute(
            select(Query)
            .where(Query.user_id == user_id)
            .order_by(Query.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

async def update_query(query_id: str, query_update: QueryUpdate) -> Optional[Query]:
    """
    Update query
    
    Args:
        query_id: Query ID
        query_update: Query update data
        
    Returns:
        Updated query if found, None otherwise
    """
    async with get_session() as session:
        # Convert to dict and remove None values
        update_data = query_update.dict(exclude_unset=True)
        
        # Update query
        await session.execute(
            sql_update(Query)
            .where(Query.id == query_id)
            .values(**update_data)
        )
        
        await session.commit()
        
        # Get updated query
        result = await session.execute(
            select(Query).where(Query.id == query_id)
        )
        return result.scalars().first()

async def get_queries(limit: int = 100, offset: int = 0) -> List[Query]:
    """
    Get all queries
    
    Args:
        limit: Maximum number of queries to return
        offset: Offset for pagination
        
    Returns:
        List of queries
    """
    async with get_session() as session:
        result = await session.execute(
            select(Query)
            .order_by(Query.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

async def delete_query(query_id: str) -> bool:
    """
    Delete query
    
    Args:
        query_id: Query ID
        
    Returns:
        True if query was deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(Query).where(Query.id == query_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0