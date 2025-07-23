"""
Service for policy management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..db.crud.policy import (
    create_policy,
    get_policy,
    get_policies,
    count_policies,
    update_policy,
    delete_policy,
    get_active_policies_by_type,
    get_effective_policy_settings
)
from ..models.policy import (
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
    PaginatedPolicies,
    PolicyType,
    PolicyStatus,
    PolicyFilterParams,
    UserPermissionPolicySettings,
    QueryLimitPolicySettings,
    SecurityPolicySettings
)
from ..services.system_monitoring_service import SystemMonitoringService
from ..models.system import LogLevel, LogCategory


class PolicyService:
    """Service for policy management"""
    
    @staticmethod
    async def create_policy(
        db: AsyncSession,
        policy_data: PolicyCreate,
        created_by: str
    ) -> PolicyResponse:
        """
        Create a new policy
        
        Args:
            db: Database session
            policy_data: Policy data
            created_by: User ID of the creator
            
        Returns:
            Created policy
        """
        # Validate policy settings based on type
        PolicyService._validate_policy_settings(policy_data.policy_type, policy_data.settings)
        
        # Create policy
        policy = await create_policy(db, policy_data, created_by)
        
        # Log the event
        await SystemMonitoringService.log_system_event(
            db=db,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message=f"Policy '{policy.name}' created",
            user_id=created_by,
            details={"policy_id": policy.id, "policy_type": policy.policy_type}
        )
        
        return PolicyResponse.from_orm(policy)
    
    @staticmethod
    async def get_policy(
        db: AsyncSession,
        policy_id: str
    ) -> Optional[PolicyResponse]:
        """
        Get a policy by ID
        
        Args:
            db: Database session
            policy_id: Policy ID
            
        Returns:
            Policy if found, None otherwise
        """
        policy = await get_policy(db, policy_id)
        if not policy:
            return None
        
        return PolicyResponse.from_orm(policy)
    
    @staticmethod
    async def get_paginated_policies(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[PolicyFilterParams] = None
    ) -> PaginatedPolicies:
        """
        Get paginated policies
        
        Args:
            db: Database session
            page: Page number
            page_size: Number of items per page
            filters: Optional filters
            
        Returns:
            Paginated policies
        """
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Get policies
        policies = await get_policies(db, skip=skip, limit=page_size, filters=filters)
        
        # Count total policies
        total = await count_policies(db, filters=filters)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedPolicies(
            policies=[PolicyResponse.from_orm(p) for p in policies],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    @staticmethod
    async def update_policy(
        db: AsyncSession,
        policy_id: str,
        policy_data: PolicyUpdate,
        user_id: str
    ) -> Optional[PolicyResponse]:
        """
        Update a policy
        
        Args:
            db: Database session
            policy_id: Policy ID
            policy_data: Policy data to update
            user_id: User ID performing the update
            
        Returns:
            Updated policy if found, None otherwise
        """
        # Get the current policy
        current_policy = await get_policy(db, policy_id)
        if not current_policy:
            return None
        
        # Validate policy settings if provided
        if policy_data.settings:
            PolicyService._validate_policy_settings(current_policy.policy_type, policy_data.settings)
        
        # Update policy
        updated_policy = await update_policy(db, policy_id, policy_data)
        if not updated_policy:
            return None
        
        # Log the event
        await SystemMonitoringService.log_system_event(
            db=db,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message=f"Policy '{updated_policy.name}' updated",
            user_id=user_id,
            details={"policy_id": policy_id, "policy_type": updated_policy.policy_type}
        )
        
        return PolicyResponse.from_orm(updated_policy)
    
    @staticmethod
    async def delete_policy(
        db: AsyncSession,
        policy_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a policy
        
        Args:
            db: Database session
            policy_id: Policy ID
            user_id: User ID performing the deletion
            
        Returns:
            True if deleted, False if not found
        """
        # Get the policy to log details
        policy = await get_policy(db, policy_id)
        if not policy:
            return False
        
        # Delete policy
        result = await delete_policy(db, policy_id)
        if not result:
            return False
        
        # Log the event
        await SystemMonitoringService.log_system_event(
            db=db,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message=f"Policy '{policy.name}' deleted",
            user_id=user_id,
            details={"policy_id": policy_id, "policy_type": policy.policy_type}
        )
        
        return True
    
    @staticmethod
    async def get_effective_user_permission_settings(
        db: AsyncSession,
        role: str
    ) -> UserPermissionPolicySettings:
        """
        Get effective user permission settings for a role
        
        Args:
            db: Database session
            role: User role
            
        Returns:
            Effective user permission settings
        """
        settings_dict = await get_effective_policy_settings(
            db, 
            PolicyType.USER_PERMISSION, 
            role
        )
        
        # Convert to pydantic model with defaults
        return UserPermissionPolicySettings(**settings_dict)
    
    @staticmethod
    async def get_effective_query_limit_settings(
        db: AsyncSession,
        role: str
    ) -> QueryLimitPolicySettings:
        """
        Get effective query limit settings for a role
        
        Args:
            db: Database session
            role: User role
            
        Returns:
            Effective query limit settings
        """
        settings_dict = await get_effective_policy_settings(
            db, 
            PolicyType.QUERY_LIMIT, 
            role
        )
        
        # Convert to pydantic model with defaults
        return QueryLimitPolicySettings(**settings_dict)
    
    @staticmethod
    async def get_effective_security_settings(
        db: AsyncSession,
        role: str
    ) -> SecurityPolicySettings:
        """
        Get effective security settings for a role
        
        Args:
            db: Database session
            role: User role
            
        Returns:
            Effective security settings
        """
        settings_dict = await get_effective_policy_settings(
            db, 
            PolicyType.SECURITY, 
            role
        )
        
        # Convert to pydantic model with defaults
        return SecurityPolicySettings(**settings_dict)
    
    @staticmethod
    def _validate_policy_settings(policy_type: str, settings: Dict[str, Any]) -> None:
        """
        Validate policy settings based on policy type
        
        Args:
            policy_type: Policy type
            settings: Policy settings
            
        Raises:
            ValueError: If settings are invalid
        """
        try:
            if policy_type == PolicyType.USER_PERMISSION:
                UserPermissionPolicySettings(**settings)
            elif policy_type == PolicyType.QUERY_LIMIT:
                QueryLimitPolicySettings(**settings)
            elif policy_type == PolicyType.SECURITY:
                SecurityPolicySettings(**settings)
            else:
                raise ValueError(f"Unknown policy type: {policy_type}")
        except Exception as e:
            raise ValueError(f"Invalid policy settings: {str(e)}")