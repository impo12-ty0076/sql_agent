"""
Database models for system logs and monitoring
"""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional

from ..base_model import BaseModel

class SystemLog(BaseModel):
    """Database model for system logs"""
    __tablename__ = "system_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    level = Column(String(20), nullable=False, index=True)  # info, warning, error, critical
    category = Column(String(50), nullable=False, index=True)  # auth, query, system, security
    message = Column(String(500), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    details = Column(JSON, nullable=True)
    
    # Create indexes for efficient querying
    __table_args__ = (
        Index('ix_system_logs_timestamp', timestamp.desc()),
        Index('ix_system_logs_level_category', level, category),
    )
    
    def __repr__(self):
        return f"<SystemLog {self.id} - {self.level} - {self.category}>"


class SystemMetric(BaseModel):
    """Database model for system metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    
    # Create indexes for efficient querying
    __table_args__ = (
        Index('ix_system_metrics_timestamp', timestamp.desc()),
        Index('ix_system_metrics_name', metric_name),
    )
    
    def __repr__(self):
        return f"<SystemMetric {self.id} - {self.metric_name}: {self.metric_value}>"