"""
CRUD operations for query history models
"""
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete, and_, or_

from ...db.session import get_session
from ...models.query import QueryHistory

async def create_query_history(user_id: str, query_id: str, favorite: bool = False, tags: List[str] = None, notes: Optional[str] = None) -> QueryHistory:
    """
    Create a new query history record
    
    Args:
        user_id: User ID
        query_id: Query ID
        favorite: Whether the query is favorited
        tags: List of tags for the query
        notes: Additional notes for the query
        
    Returns:
        Created query history
    """
    async with get_session() as session:
        # Create query history object
        query_history = QueryHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            query_id=query_id,
            favorite=favorite,
            tags=tags or [],
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to session and commit
        session.add(query_history)
        await session.commit()
        await session.refresh(query_history)
        
        return query_history

async def get_query_history_by_id(history_id: str) -> Optional[QueryHistory]:
    """
    Get query history by ID
    
    Args:
        history_id: Query history ID
        
    Returns:
        Query history if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(QueryHistory).where(QueryHistory.id == history_id)
        )
        return result.scalars().first()

async def get_query_history_by_query_id(query_id: str) -> Optional[QueryHistory]:
    """
    Get query history by query ID
    
    Args:
        query_id: Query ID
        
    Returns:
        Query history if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(QueryHistory).where(QueryHistory.query_id == query_id)
        )
        return result.scalars().first()

async def get_query_history_by_user(
    user_id: str, 
    limit: int = 100, 
    offset: int = 0,
    favorite_only: bool = False,
    tags: List[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[QueryHistory]:
    """
    Get query history by user ID with optional filters
    
    Args:
        user_id: User ID
        limit: Maximum number of history items to return
        offset: Offset for pagination
        favorite_only: If True, return only favorited queries
        tags: Filter by tags (any match)
        start_date: Filter by created_at >= start_date
        end_date: Filter by created_at <= end_date
        
    Returns:
        List of query history items
    """
    async with get_session() as session:
        # Build query with filters
        query = select(QueryHistory).where(QueryHistory.user_id == user_id)
        
        if favorite_only:
            query = query.where(QueryHistory.favorite == True)
            
        if tags:
            # Filter for any tag match (using array overlap)
            # Note: This implementation depends on the database backend
            # For PostgreSQL, you might use the overlap operator: QueryHistory.tags.overlap(tags)
            # For SQLite or other DBs without array operators, you might need a different approach
            # This is a simplified version that might need adjustment based on your DB
            tag_filters = []
            for tag in tags:
                tag_filters.append(QueryHistory.tags.contains([tag]))
            query = query.where(or_(*tag_filters))
            
        if start_date:
            query = query.where(QueryHistory.created_at >= start_date)
            
        if end_date:
            query = query.where(QueryHistory.created_at <= end_date)
        
        # Add ordering and pagination
        query = query.order_by(QueryHistory.created_at.desc()).limit(limit).offset(offset)
        
        # Execute query
        result = await session.execute(query)
        return result.scalars().all()

async def update_query_history(history_id: str, favorite: Optional[bool] = None, tags: Optional[List[str]] = None, notes: Optional[str] = None) -> Optional[QueryHistory]:
    """
    Update query history
    
    Args:
        history_id: Query history ID
        favorite: Whether the query is favorited
        tags: List of tags for the query
        notes: Additional notes for the query
        
    Returns:
        Updated query history if found, None otherwise
    """
    async with get_session() as session:
        # Build update data
        update_data = {}
        if favorite is not None:
            update_data["favorite"] = favorite
        if tags is not None:
            update_data["tags"] = tags
        if notes is not None:
            update_data["notes"] = notes
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update query history
            await session.execute(
                sql_update(QueryHistory)
                .where(QueryHistory.id == history_id)
                .values(**update_data)
            )
            
            await session.commit()
        
        # Get updated query history
        result = await session.execute(
            select(QueryHistory).where(QueryHistory.id == history_id)
        )
        return result.scalars().first()

async def delete_query_history(history_id: str) -> bool:
    """
    Delete query history
    
    Args:
        history_id: Query history ID
        
    Returns:
        True if query history was deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(QueryHistory).where(QueryHistory.id == history_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0

async def get_query_histories(limit: int = 100, offset: int = 0) -> List[QueryHistory]:
    """
    Get all query histories
    
    Args:
        limit: Maximum number of history items to return
        offset: Offset for pagination
        
    Returns:
        List of query history items
    """
    async with get_session() as session:
        result = await session.execute(
            select(QueryHistory)
            .order_by(QueryHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

async def delete_query_history_by_query_id(query_id: str) -> bool:
    """
    Delete query history by query ID
    
    Args:
        query_id: Query ID
        
    Returns:
        True if query history was deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(QueryHistory).where(QueryHistory.query_id == query_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0