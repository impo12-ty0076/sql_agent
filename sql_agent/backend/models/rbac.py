from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from datetime import datetime

class Permission(str, Enum):
    """System permissions"""
    # Database access permissions
    DB_CONNECT = "db:connect"
    DB_LIST = "db:list"
    DB_SCHEMA_VIEW = "db:schema:view"
    
    # Query permissions
    QUERY_EXECUTE = "query:execute"
    QUERY_CANCEL = "query:cancel"
    QUERY_HISTORY_VIEW = "query:history:view"
    QUERY_HISTORY_DELETE = "query:history:delete"
    
    # Report permissions
    REPORT_GENERATE = "report:generate"
    REPORT_SHARE = "report:share"
    REPORT_DOWNLOAD = "report:download"
    
    # Admin permissions
    ADMIN_USER_MANAGE = "admin:user:manage"
    ADMIN_POLICY_MANAGE = "admin:policy:manage"
    ADMIN_SYSTEM_MONITOR = "admin:system:monitor"
    ADMIN_LOG_VIEW = "admin:log:view"
    ADMIN_BACKUP = "admin:backup"

class ResourceType(str, Enum):
    """Types of resources that can have permissions"""
    DATABASE = "database"
    SCHEMA = "schema"
    TABLE = "table"
    QUERY = "query"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"

class PolicyEffect(str, Enum):
    """Policy effect types"""
    ALLOW = "allow"
    DENY = "deny"

class ResourcePolicy(BaseModel):
    """Policy for a specific resource"""
    resource_type: ResourceType
    resource_id: str
    permissions: List[Permission]
    effect: PolicyEffect = PolicyEffect.ALLOW
    conditions: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True

class Role(BaseModel):
    """Role definition with associated permissions"""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[Permission]
    resource_policies: List[ResourcePolicy] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True

class UserRole(BaseModel):
    """Association between a user and a role"""
    user_id: str
    role_id: str
    assigned_at: datetime
    assigned_by: str

class AccessControlList(BaseModel):
    """Access control list for a specific resource"""
    resource_type: ResourceType
    resource_id: str
    user_permissions: Dict[str, List[Permission]]  # user_id -> permissions
    role_permissions: Dict[str, List[Permission]]  # role_id -> permissions
    
    class Config:
        use_enum_values = True

class PermissionCheck(BaseModel):
    """Model for permission check requests"""
    user_id: str
    resource_type: ResourceType
    resource_id: str
    permission: Permission
    
    class Config:
        use_enum_values = True