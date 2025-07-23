"""
CRUD operations for query statistics
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from ..models.query import QueryDB


def get_query_count(db: Session, user_id: Optional[str] = None, days: Optional[int] = None) -> int:
    """
    Get query count with optional filtering
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        days: Optional number of days to look back
        
    Returns:
        Query count
    """
    query = db.query(func.count(QueryDB.id))
    
    if user_id:
        query = query.filter(QueryDB.user_id == user_id)
    
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(QueryDB.start_time >= start_date)
    
    return query.scalar() or 0


def get_recent_queries(db: Session, limit: int = 100, user_id: Optional[str] = None) -> List[QueryDB]:
    """
    Get recent queries
    
    Args:
        db: Database session
        limit: Maximum number of queries to return
        user_id: Optional user ID to filter by
        
    Returns:
        List of recent queries
    """
    query = db.query(QueryDB)
    
    if user_id:
        query = query.filter(QueryDB.user_id == user_id)
    
    return query.order_by(desc(QueryDB.start_time)).limit(limit).all()


def get_avg_query_time(db: Session, user_id: Optional[str] = None, days: Optional[int] = None) -> float:
    """
    Get average query execution time in milliseconds
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        days: Optional number of days to look back
        
    Returns:
        Average query time in milliseconds
    """
    query = db.query(
        func.avg(func.datediff(func.millisecond, QueryDB.start_time, QueryDB.end_time))
    ).filter(QueryDB.end_time.isnot(None))
    
    if user_id:
        query = query.filter(QueryDB.user_id == user_id)
    
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(QueryDB.start_time >= start_date)
    
    result = query.scalar()
    return float(result) if result else 0.0


def get_query_error_count(db: Session, user_id: Optional[str] = None, days: Optional[int] = None) -> int:
    """
    Get count of queries with errors
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        days: Optional number of days to look back
        
    Returns:
        Count of queries with errors
    """
    query = db.query(func.count(QueryDB.id)).filter(QueryDB.error.isnot(None))
    
    if user_id:
        query = query.filter(QueryDB.user_id == user_id)
    
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(QueryDB.start_time >= start_date)
    
    return query.scalar() or 0