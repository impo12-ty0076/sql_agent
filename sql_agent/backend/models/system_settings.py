"""
Pydantic models for system settings and backups
"""
from pydantic import BaseModel, Field, validator, SecretStr
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class BackupType(str, Enum):
    """Backup type enum"""
    FULL = "full"
    SETTINGS = "settings"
    USERS = "users"
    QUERIES = "queries"
    HISTORY = "history"


class DatabaseType(str, Enum):
    """Database type enum"""
    MSSQL = "mssql"
    HANA = "hana"


class ApiServiceType(str, Enum):
    """API service type enum"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    OTHER = "other"


class SystemSettingCreate(BaseModel):
    """Model for creating a system setting"""
    key: str
    value: Any
    description: Optional[str] = None


class SystemSettingUpdate(BaseModel):
    """Model for updating a system setting"""
    value: Any
    description: Optional[str] = None


class SystemSettingResponse(BaseModel):
    """Model for system setting response"""
    id: str
    key: str
    value: Any
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DatabaseConnectionCreate(BaseModel):
    """Model for creating a database connection"""
    name: str
    type: DatabaseType
    host: str
    port: str
    username: str
    password: SecretStr
    database: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    is_active: bool = True


class DatabaseConnectionUpdate(BaseModel):
    """Model for updating a database connection"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[str] = None
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    database: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DatabaseConnectionResponse(BaseModel):
    """Model for database connection response"""
    id: str
    name: str
    type: str
    host: str
    port: str
    username: str
    database: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    """Model for creating an API key"""
    name: str
    service: ApiServiceType
    key: SecretStr
    is_active: bool = True


class ApiKeyUpdate(BaseModel):
    """Model for updating an API key"""
    name: Optional[str] = None
    key: Optional[SecretStr] = None
    is_active: Optional[bool] = None


class ApiKeyResponse(BaseModel):
    """Model for API key response"""
    id: str
    name: str
    service: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SystemBackupCreate(BaseModel):
    """Model for creating a system backup"""
    name: str
    description: Optional[str] = None
    backup_type: BackupType


class SystemBackupResponse(BaseModel):
    """Model for system backup response"""
    id: str
    name: str
    description: Optional[str] = None
    backup_type: str
    size_bytes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class SystemRestoreRequest(BaseModel):
    """Model for system restore request"""
    backup_id: str
    restore_options: Optional[Dict[str, Any]] = None