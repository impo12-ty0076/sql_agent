"""
CRUD operations for policy management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from ..models.policy import Policy
from ...models.policy import PolicyCreate, PolicyUpdate, PolicyStatus, PolicyType, PolicyFilterParams


async def create_policy(
    db: AsyncSession,
    policy_data: PolicyCreate,
    created_by: str
) -> Policy:
    """
    Create a new policy
    
    Args:
        db: Database session
        policy_data: Policy data
        created_by: User ID of the creator
        
    Returns:
        Created policy
    """
    policy = Policy(
        name=policy_data.name,
        description=policy_data.description,
        policy_type=policy_data.policy_type,
        status=policy_data.status,
        applies_to_roles=policy_data.applies_to_roles,
        priority=policy_data.priority,
        settings=policy_data.settings,
        created_by=created_by
    )
    
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


async def get_policy(
    db: AsyncSession,
    policy_id: str
) -> Optional[Policy]:
    """
    Get a policy by ID
    
    Args:
        db: Database session
        policy_id: Policy ID
        
    Returns:
        Policy if found, None otherwise
    """
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    return result.scalars().first()


async def get_policies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[PolicyFilterParams] = None
) -> List[Policy]:
    """
    Get policies with optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filters: Optional filters
        
    Returns:
        List of policies
    """
    query = select(Policy)
    
    if filters:
        if filters.policy_type:
            query = query.where(Policy.policy_type == filters.policy_type)
        
        if filters.status:
            query = query.where(Policy.status == filters.status)
        
        if filters.search_term:
            search = f"%{filters.search_term}%"
            query = query.where(
                (Policy.name.ilike(search)) | 
                (Policy.description.ilike(search))
            )
        
        if filters.created_by:
            query = query.where(Policy.created_by == filters.created_by)
        
        if filters.role:
            # This assumes applies_to_roles is stored as a JSON array
            # The exact implementation depends on your database and how you store the array
            query = query.where(Policy.applies_to_roles.contains([filters.role]))
    
    query = query.order_by(Policy.priority.desc(), Policy.updated_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def count_policies(
    db: AsyncSession,
    filters: Optional[PolicyFilterParams] = None
) -> int:
    """
    Count policies with optional filtering
    
    Args:
        db: Database session
        filters: Optional filters
        
    Returns:
        Number of policies
    """
    query = select(func.count(Policy.id))
    
    if filters:
        if filters.policy_type:
            query = query.where(Policy.policy_type == filters.policy_type)
        
        if filters.status:
            query = query.where(Policy.status == filters.status)
        
        if filters.search_term:
            search = f"%{filters.search_term}%"
            query = query.where(
                (Policy.name.ilike(search)) | 
                (Policy.description.ilike(search))
            )
        
        if filters.created_by:
            query = query.where(Policy.created_by == filters.created_by)
        
        if filters.role:
            query = query.where(Policy.applies_to_roles.contains([filters.role]))
    
    result = await db.execute(query)
    return result.scalar() or 0


async def update_policy(
    db: AsyncSession,
    policy_id: str,
    policy_data: PolicyUpdate
) -> Optional[Policy]:
    """
    Update a policy
    
    Args:
        db: Database session
        policy_id: Policy ID
        policy_data: Policy data to update
        
    Returns:
        Updated policy if found, None otherwise
    """
    # Get the policy
    policy = await get_policy(db, policy_id)
    if not policy:
        return None
    
    # Update fields
    update_data = policy_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)
    
    # Update the updated_at timestamp
    policy.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(policy)
    return policy


async def delete_policy(
    db: AsyncSession,
    policy_id: str
) -> bool:
    """
    Delete a policy
    
    Args:
        db: Database session
        policy_id: Policy ID
        
    Returns:
        True if deleted, False if not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        return False
    
    await db.delete(policy)
    await db.commit()
    return True


async def get_active_policies_by_type(
    db: AsyncSession,
    policy_type: PolicyType,
    role: Optional[str] = None
) -> List[Policy]:
    """
    Get active policies by type and optionally filtered by role
    
    Args:
        db: Database session
        policy_type: Policy type
        role: Optional role to filter by
        
    Returns:
        List of active policies
    """
    query = select(Policy).where(
        (Policy.policy_type == policy_type) &
        (Policy.status == PolicyStatus.ACTIVE)
    )
    
    if role:
        # This assumes applies_to_roles is stored as a JSON array
        query = query.where(Policy.applies_to_roles.contains([role]))
    
    query = query.order_by(Policy.priority.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_effective_policy_settings(
    db: AsyncSession,
    policy_type: PolicyType,
    role: str
) -> Dict[str, Any]:
    """
    Get effective policy settings by merging all applicable policies
    based on priority
    
    Args:
        db: Database session
        policy_type: Policy type
        role: User role
        
    Returns:
        Merged policy settings
    """
    policies = await get_active_policies_by_type(db, policy_type, role)
    
    # Start with empty settings
    effective_settings = {}
    
    # Apply policies in order of priority (highest first)
    for policy in policies:
        # Merge settings
        if policy.settings:
            effective_settings.update(policy.settings)
    
    return effective_settings