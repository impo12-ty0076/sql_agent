"""
CRUD operations for shared query models
"""
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timedelta
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update, delete as sql_delete, and_, or_

from ...db.session import get_session
from ...db.models.query import SharedQueryDB

def generate_access_token() -> str:
    """
    Generate a secure random access token for shared queries
    
    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(32)

async def create_shared_query(
    query_id: str, 
    shared_by: str, 
    allowed_users: List[str] = None, 
    expires_in_days: Optional[int] = 7
) -> SharedQueryDB:
    """
    Create a new shared query
    
    Args:
        query_id: Query ID to share
        shared_by: User ID of the user sharing the query
        allowed_users: List of user IDs allowed to access the shared query (empty list for public access)
        expires_in_days: Number of days until the shared query expires (None for no expiration)
        
    Returns:
        Created shared query
    """
    async with get_session() as session:
        # Generate access token
        access_token = generate_access_token()
        
        # Calculate expiration date if provided
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create shared query object
        shared_query = SharedQueryDB(
            id=str(uuid.uuid4()),
            query_id=query_id,
            shared_by=shared_by,
            access_token=access_token,
            expires_at=expires_at,
            allowed_users=allowed_users or []
        )
        
        # Add to session and commit
        session.add(shared_query)
        await session.commit()
        await session.refresh(shared_query)
        
        return shared_query

async def get_shared_query_by_id(shared_id: str) -> Optional[SharedQueryDB]:
    """
    Get shared query by ID
    
    Args:
        shared_id: Shared query ID
        
    Returns:
        Shared query if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(SharedQueryDB).where(SharedQueryDB.id == shared_id)
        )
        return result.scalars().first()

async def get_shared_query_by_token(access_token: str) -> Optional[SharedQueryDB]:
    """
    Get shared query by access token
    
    Args:
        access_token: Access token
        
    Returns:
        Shared query if found, None otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            select(SharedQueryDB).where(SharedQueryDB.access_token == access_token)
        )
        return result.scalars().first()

async def get_shared_queries_by_query_id(query_id: str) -> List[SharedQueryDB]:
    """
    Get all shared queries for a specific query
    
    Args:
        query_id: Query ID
        
    Returns:
        List of shared queries
    """
    async with get_session() as session:
        result = await session.execute(
            select(SharedQueryDB).where(SharedQueryDB.query_id == query_id)
        )
        return result.scalars().all()

async def get_shared_queries_by_user(user_id: str, include_expired: bool = False) -> List[SharedQueryDB]:
    """
    Get all queries shared by a specific user
    
    Args:
        user_id: User ID
        include_expired: Whether to include expired shared queries
        
    Returns:
        List of shared queries
    """
    async with get_session() as session:
        query = select(SharedQueryDB).where(SharedQueryDB.shared_by == user_id)
        
        if not include_expired:
            # Exclude expired shared queries
            query = query.where(
                or_(
                    SharedQueryDB.expires_at.is_(None),
                    SharedQueryDB.expires_at > datetime.utcnow()
                )
            )
        
        result = await session.execute(query)
        return result.scalars().all()

async def update_shared_query(
    shared_id: str, 
    allowed_users: Optional[List[str]] = None, 
    expires_in_days: Optional[int] = None
) -> Optional[SharedQueryDB]:
    """
    Update shared query
    
    Args:
        shared_id: Shared query ID
        allowed_users: List of user IDs allowed to access the shared query
        expires_in_days: Number of days until the shared query expires (None for no change)
        
    Returns:
        Updated shared query if found, None otherwise
    """
    async with get_session() as session:
        # Build update data
        update_data = {}
        if allowed_users is not None:
            update_data["allowed_users"] = allowed_users
        
        if expires_in_days is not None:
            if expires_in_days < 0:
                # Negative value means no expiration
                update_data["expires_at"] = None
            else:
                update_data["expires_at"] = datetime.utcnow() + timedelta(days=expires_in_days)
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update shared query
            await session.execute(
                sql_update(SharedQueryDB)
                .where(SharedQueryDB.id == shared_id)
                .values(**update_data)
            )
            
            await session.commit()
        
        # Get updated shared query
        result = await session.execute(
            select(SharedQueryDB).where(SharedQueryDB.id == shared_id)
        )
        return result.scalars().first()

async def refresh_shared_query_token(shared_id: str) -> Optional[SharedQueryDB]:
    """
    Generate a new access token for a shared query
    
    Args:
        shared_id: Shared query ID
        
    Returns:
        Updated shared query if found, None otherwise
    """
    async with get_session() as session:
        # Generate new access token
        access_token = generate_access_token()
        
        # Update shared query
        await session.execute(
            sql_update(SharedQueryDB)
            .where(SharedQueryDB.id == shared_id)
            .values(
                access_token=access_token,
                updated_at=datetime.utcnow()
            )
        )
        
        await session.commit()
        
        # Get updated shared query
        result = await session.execute(
            select(SharedQueryDB).where(SharedQueryDB.id == shared_id)
        )
        return result.scalars().first()

async def delete_shared_query(shared_id: str) -> bool:
    """
    Delete shared query
    
    Args:
        shared_id: Shared query ID
        
    Returns:
        True if shared query was deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(SharedQueryDB).where(SharedQueryDB.id == shared_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0

async def delete_shared_queries_by_query_id(query_id: str) -> bool:
    """
    Delete all shared queries for a specific query
    
    Args:
        query_id: Query ID
        
    Returns:
        True if any shared queries were deleted, False otherwise
    """
    async with get_session() as session:
        result = await session.execute(
            sql_delete(SharedQueryDB).where(SharedQueryDB.query_id == query_id)
        )
        
        await session.commit()
        
        return result.rowcount > 0