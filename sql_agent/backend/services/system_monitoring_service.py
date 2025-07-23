"""
System monitoring service for collecting system statistics and metrics
"""
import logging
import platform
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..db.crud.system_log import (
    create_system_log, 
    get_system_logs, 
    count_system_logs,
    create_system_metric,
    get_latest_metric,
    count_errors_by_period
)
from ..db.crud.user import get_users
from ..db.crud.query_stats import get_query_count, get_recent_queries, get_avg_query_time, get_query_error_count
from ..db.models.user import User
from ..db.models.query import QueryDB
from ..models.system import (
    SystemLogCreate, 
    LogLevel, 
    LogCategory,
    SystemMetricCreate,
    SystemStatsResponse,
    LogFilterParams,
    PaginatedSystemLogs,
    UserActivityStats,
    UserActivityStatsResponse
)

logger = logging.getLogger(__name__)

# Global variable to store the system start time
SYSTEM_START_TIME = time.time()


class SystemMonitoringService:
    """Service for system monitoring and statistics"""
    
    @staticmethod
    def log_system_event(
        db: Session,
        level: LogLevel,
        category: LogCategory,
        message: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a system event
        
        Args:
            db: Database session
            level: Log level
            category: Log category
            message: Log message
            user_id: Optional user ID
            details: Optional additional details
        """
        log_data = SystemLogCreate(
            level=level,
            category=category,
            message=message,
            user_id=user_id,
            details=details
        )
        
        create_system_log(db, log_data)
        
        # Also log to the application logger
        log_method = getattr(logger, level.value)
        log_method(f"[{category.value}] {message}")
    
    @staticmethod
    def record_metric(
        db: Session,
        metric_name: str,
        metric_value: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a system metric
        
        Args:
            db: Database session
            metric_name: Name of the metric
            metric_value: Value of the metric
            details: Optional additional details
        """
        metric_data = SystemMetricCreate(
            metric_name=metric_name,
            metric_value=metric_value,
            details=details
        )
        
        create_system_metric(db, metric_data)
    
    @staticmethod
    def get_system_stats(db: Session) -> SystemStatsResponse:
        """
        Get system statistics
        
        Args:
            db: Database session
            
        Returns:
            System statistics
        """
        # Get user counts
        user_count = db.query(func.count(User.id)).scalar() or 0
        
        # Get active users in the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_users_24h = db.query(func.count(User.id)).filter(
            User.last_login >= yesterday
        ).scalar() or 0
        
        # Get query counts
        query_count_total = db.query(func.count(QueryDB.id)).scalar() or 0
        
        query_count_24h = db.query(func.count(QueryDB.id)).filter(
            QueryDB.start_time >= yesterday
        ).scalar() or 0
        
        # Calculate average query time
        avg_query_time_ms = 0
        query_times = db.query(
            func.avg(func.datediff(func.millisecond, QueryDB.start_time, QueryDB.end_time))
        ).filter(
            QueryDB.end_time.isnot(None)
        ).scalar()
        
        if query_times:
            avg_query_time_ms = float(query_times)
        
        # Get error count in the last 24 hours
        error_count_24h = count_errors_by_period(db, hours=24)
        
        # Get system metrics
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get active connections (this is a placeholder, actual implementation would depend on DB connector)
            active_connections = 0
            try:
                # This is just an example, actual implementation would depend on the DB connector
                active_connections = db.execute("SELECT COUNT(*) FROM sys.dm_exec_connections").scalar() or 0
            except Exception as e:
                logger.warning(f"Failed to get active connections: {str(e)}")
                active_connections = 0
            
            # Calculate system uptime
            system_uptime_seconds = int(time.time() - SYSTEM_START_TIME)
            
            return SystemStatsResponse(
                status="operational",
                user_count=user_count,
                active_users_24h=active_users_24h,
                query_count_total=query_count_total,
                query_count_24h=query_count_24h,
                avg_query_time_ms=avg_query_time_ms,
                error_count_24h=error_count_24h,
                active_connections=active_connections,
                system_uptime_seconds=system_uptime_seconds,
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory.percent,
                storage_usage_percent=disk.percent
            )
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            # Return basic stats if system metrics fail
            return SystemStatsResponse(
                status="degraded",
                user_count=user_count,
                active_users_24h=active_users_24h,
                query_count_total=query_count_total,
                query_count_24h=query_count_24h,
                avg_query_time_ms=avg_query_time_ms,
                error_count_24h=error_count_24h,
                active_connections=0,
                system_uptime_seconds=int(time.time() - SYSTEM_START_TIME),
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                storage_usage_percent=0.0
            )
    
    @staticmethod
    def get_paginated_logs(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[LogFilterParams] = None
    ) -> PaginatedSystemLogs:
        """
        Get paginated system logs
        
        Args:
            db: Database session
            page: Page number
            page_size: Number of items per page
            filters: Optional filters
            
        Returns:
            Paginated system logs
        """
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Get logs
        logs = get_system_logs(db, skip=skip, limit=page_size, filters=filters)
        
        # Count total logs
        total = count_system_logs(db, filters=filters)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedSystemLogs(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    @staticmethod
    def get_user_activity_stats(
        db: Session,
        days: int = 7,
        limit: int = 100,
        offset: int = 0
    ) -> UserActivityStatsResponse:
        """
        Get user activity statistics
        
        Args:
            db: Database session
            days: Number of days to look back
            limit: Maximum number of users to return
            offset: Offset for pagination
            
        Returns:
            User activity statistics
        """
        # Get users with basic info
        users = get_users(db, skip=offset, limit=limit)
        
        # Start date for filtering
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Collect stats for each user
        user_stats = []
        for user in users:
            # Count queries by this user in the period
            query_count = db.query(func.count(QueryDB.id)).filter(
                QueryDB.user_id == user.id,
                QueryDB.start_time >= start_date
            ).scalar() or 0
            
            # Get last activity time
            last_active = user.last_login or user.created_at
            
            # Calculate average query time
            avg_query_time = db.query(
                func.avg(func.datediff(func.millisecond, QueryDB.start_time, QueryDB.end_time))
            ).filter(
                QueryDB.user_id == user.id,
                QueryDB.end_time.isnot(None),
                QueryDB.start_time >= start_date
            ).scalar() or 0
            
            # Count errors for this user
            error_count = db.query(func.count(SystemLog.id)).filter(
                SystemLog.user_id == user.id,
                SystemLog.level.in_(["error", "critical"]),
                SystemLog.timestamp >= start_date
            ).scalar() or 0
            
            user_stats.append(UserActivityStats(
                user_id=user.id,
                username=user.username,
                email=user.email,
                query_count=query_count,
                last_active=last_active,
                avg_query_time_ms=float(avg_query_time),
                error_count=error_count
            ))
        
        # Count total users
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        return UserActivityStatsResponse(
            users=user_stats,
            total=total_users
        )