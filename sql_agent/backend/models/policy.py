"""
Pydantic models for policy management
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum


class PolicyType(str, Enum):
    """Policy type enum"""
    USER_PERMISSION = "user_permission"
    QUERY_LIMIT = "query_limit"
    SECURITY = "security"


class PolicyStatus(str, Enum):
    """Policy status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class UserPermissionPolicySettings(BaseModel):
    """Settings for user permission policies"""
    allowed_roles: List[str] = Field(default=["user"], description="Allowed user roles")
    allowed_db_types: List[str] = Field(default=["mssql", "hana"], description="Allowed database types")
    default_schemas_access: List[str] = Field(default=[], description="Default schemas that users can access")
    default_tables_access: List[str] = Field(default=[], description="Default tables that users can access")
    allow_schema_listing: bool = Field(default=True, description="Whether users can list schemas")
    allow_table_listing: bool = Field(default=True, description="Whether users can list tables")


class QueryLimitPolicySettings(BaseModel):
    """Settings for query limit policies"""
    max_queries_per_day: int = Field(default=100, ge=1, description="Maximum number of queries per day")
    max_query_execution_time: int = Field(default=60, ge=1, description="Maximum query execution time in seconds")
    max_result_size: int = Field(default=10000, ge=1, description="Maximum number of rows in query results")
    allowed_query_types: Set[str] = Field(default={"SELECT"}, description="Allowed query types")
    blocked_keywords: Set[str] = Field(default={"DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE"}, 
                                      description="Blocked SQL keywords")


class SecurityPolicySettings(BaseModel):
    """Settings for security policies"""
    require_mfa: bool = Field(default=False, description="Whether MFA is required")
    password_expiry_days: int = Field(default=90, ge=0, description="Password expiry in days (0 for never)")
    min_password_length: int = Field(default=8, ge=6, description="Minimum password length")
    require_password_complexity: bool = Field(default=True, description="Whether password complexity is required")
    session_timeout_minutes: int = Field(default=60, ge=5, description="Session timeout in minutes")
    failed_login_attempts_before_lockout: int = Field(default=5, ge=1, description="Failed login attempts before account lockout")
    account_lockout_duration_minutes: int = Field(default=30, ge=1, description="Account lockout duration in minutes")
    ip_whitelist: List[str] = Field(default=[], description="Whitelisted IP addresses")


class PolicySettingsUnion(BaseModel):
    """Union of all policy settings types"""
    user_permission: Optional[UserPermissionPolicySettings] = None
    query_limit: Optional[QueryLimitPolicySettings] = None
    security: Optional[SecurityPolicySettings] = None


class PolicyBase(BaseModel):
    """Base policy model with common fields"""
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    policy_type: PolicyType = Field(..., description="Policy type")
    status: PolicyStatus = Field(default=PolicyStatus.DRAFT, description="Policy status")
    applies_to_roles: List[str] = Field(default=["user"], description="Roles this policy applies to")
    priority: int = Field(default=0, description="Policy priority (higher number = higher priority)")


class PolicyCreate(PolicyBase):
    """Model for creating a new policy"""
    settings: Dict[str, Any] = Field(..., description="Policy settings")


class PolicyUpdate(BaseModel):
    """Model for updating a policy"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PolicyStatus] = None
    applies_to_roles: Optional[List[str]] = None
    priority: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class PolicyResponse(PolicyBase):
    """Policy model for API responses"""
    id: str
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class PolicyFilterParams(BaseModel):
    """Model for policy filter parameters"""
    policy_type: Optional[PolicyType] = None
    status: Optional[PolicyStatus] = None
    role: Optional[str] = None
    search_term: Optional[str] = None
    created_by: Optional[str] = None


class PaginatedPolicies(BaseModel):
    """Model for paginated policies response"""
    policies: List[PolicyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int