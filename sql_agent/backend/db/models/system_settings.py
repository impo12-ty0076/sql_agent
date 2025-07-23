"""
Database models for system settings and backups
"""
from sqlalchemy import Column, String, DateTime, JSON, Boolean, LargeBinary, Text
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional

from ..base_model import BaseModel

class SystemSetting(BaseModel):
    """Database model for system settings"""
    __tablename__ = "system_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemSetting {self.key}>"


class DatabaseConnection(BaseModel):
    """Database model for database connection settings"""
    __tablename__ = "database_connections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # mssql, hana, etc.
    host = Column(String(255), nullable=False)
    port = Column(String(10), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(String(500), nullable=False)
    database = Column(String(100), nullable=True)
    options = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DatabaseConnection {self.name} - {self.type}>"


class ApiKey(BaseModel):
    """Database model for API keys"""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False)  # openai, azure, etc.
    key_encrypted = Column(String(500), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ApiKey {self.name} - {self.service}>"


class SystemBackup(BaseModel):
    """Database model for system backups"""
    __tablename__ = "system_backups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    backup_type = Column(String(50), nullable=False)  # full, settings, users, queries, etc.
    file_path = Column(String(500), nullable=True)  # Path to backup file if stored on disk
    backup_data = Column(LargeBinary, nullable=True)  # Backup data if stored in DB
    backup_metadata = Column(JSON, nullable=True)  # Additional metadata about the backup
    size_bytes = Column(String(20), nullable=True)  # Size of the backup in bytes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(36), nullable=True)  # User who created the backup
    
    def __repr__(self):
        return f"<SystemBackup {self.name} - {self.backup_type}>"