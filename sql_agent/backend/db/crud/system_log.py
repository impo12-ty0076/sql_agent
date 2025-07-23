"""
CRUD operations for system logs and metrics
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from ..models.system_log import SystemLog, SystemMetric
from ...models.system import LogFilterParams, SystemLogCreate, SystemMetricCreate


def create_system_log(db: Session, log_data: SystemLogCreate) -> SystemLog:
    """
    Create a new system log entry
    
    Args:
        db: Database session
        log_data: Log data to create
        
    Returns:
        Created system log
    """
    log = SystemLog(
        level=log_data.level,
        category=log_data.category,
        message=log_data.message,
        user_id=log_data.user_id,
        details=log_data.details
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log


def get_system_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[LogFilterParams] = None
) -> List[SystemLog]:
    """
    Get system logs with optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filters: Optional filters to apply
        
    Returns:
        List of system logs
    """
    query = db.query(SystemLog)
    
    if filters:
        if filters.level:
            query = query.filter(SystemLog.level == filters.level)
        
        if filters.category:
            query = query.filter(SystemLog.category == filters.category)
        
        if filters.start_date:
            query = query.filter(SystemLog.timestamp >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(SystemLog.timestamp <= filters.end_date)
        
        if filters.user_id:
            query = query.filter(SystemLog.user_id == filters.user_id)
        
        if filters.search_term:
            search = f"%{filters.search_term}%"
            query = query.filter(
                or_(
                    SystemLog.message.ilike(search),
                    SystemLog.category.ilike(search)
                )
            )
    
    return query.order_by(desc(SystemLog.timestamp)).offset(skip).limit(limit).all()


def count_system_logs(
    db: Session,
    filters: Optional[LogFilterParams] = None
) -> int:
    """
    Count system logs with optional filtering
    
    Args:
        db: Database session
        filters: Optional filters to apply
        
    Returns:
        Count of system logs
    """
    query = db.query(func.count(SystemLog.id))
    
    if filters:
        if filters.level:
            query = query.filter(SystemLog.level == filters.level)
        
        if filters.category:
            query = query.filter(SystemLog.category == filters.category)
        
        if filters.start_date:
            query = query.filter(SystemLog.timestamp >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(SystemLog.timestamp <= filters.end_date)
        
        if filters.user_id:
            query = query.filter(SystemLog.user_id == filters.user_id)
        
        if filters.search_term:
            search = f"%{filters.search_term}%"
            query = query.filter(
                or_(
                    SystemLog.message.ilike(search),
                    SystemLog.category.ilike(search)
                )
            )
    
    return query.scalar()


def create_system_metric(db: Session, metric_data: SystemMetricCreate) -> SystemMetric:
    """
    Create a new system metric entry
    
    Args:
        db: Database session
        metric_data: Metric data to create
        
    Returns:
        Created system metric
    """
    metric = SystemMetric(
        metric_name=metric_data.metric_name,
        metric_value=metric_data.metric_value,
        details=metric_data.details
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric


def get_latest_metric(db: Session, metric_name: str) -> Optional[SystemMetric]:
    """
    Get the latest value for a specific metric
    
    Args:
        db: Database session
        metric_name: Name of the metric
        
    Returns:
        Latest system metric or None if not found
    """
    return db.query(SystemMetric).filter(
        SystemMetric.metric_name == metric_name
    ).order_by(desc(SystemMetric.timestamp)).first()


def get_metric_history(
    db: Session,
    metric_name: str,
    hours: int = 24,
    limit: int = 100
) -> List[SystemMetric]:
    """
    Get historical values for a specific metric
    
    Args:
        db: Database session
        metric_name: Name of the metric
        hours: Number of hours to look back
        limit: Maximum number of records to return
        
    Returns:
        List of system metrics
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(SystemMetric).filter(
        and_(
            SystemMetric.metric_name == metric_name,
            SystemMetric.timestamp >= start_time
        )
    ).order_by(desc(SystemMetric.timestamp)).limit(limit).all()


def count_errors_by_period(db: Session, hours: int = 24) -> int:
    """
    Count error and critical logs within a time period
    
    Args:
        db: Database session
        hours: Number of hours to look back
        
    Returns:
        Count of error and critical logs
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(func.count(SystemLog.id)).filter(
        and_(
            SystemLog.level.in_(["error", "critical"]),
            SystemLog.timestamp >= start_time
        )
    ).scalar()