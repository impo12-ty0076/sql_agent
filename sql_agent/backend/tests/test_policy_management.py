"""
Unit tests for policy management functionality
"""
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime

from ..models.policy import PolicyType, PolicyStatus
from ..db.models.policy import Policy


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test creating a new policy"""
    # Prepare test data
    policy_data = {
        "name": "Test User Permission Policy",
        "description": "A test policy for user permissions",
        "policy_type": PolicyType.USER_PERMISSION,
        "status": PolicyStatus.ACTIVE,
        "applies_to_roles": ["user"],
        "priority": 10,
        "settings": {
            "allowed_roles": ["user"],
            "allowed_db_types": ["mssql", "hana"],
            "default_schemas_access": ["public"],
            "default_tables_access": [],
            "allow_schema_listing": True,
            "allow_table_listing": True
        }
    }
    
    # Send request
    response = await client.post(
        "/api/admin/policies/",
        headers=admin_token_headers,
        json=policy_data
    )
    
    # Check response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == policy_data["name"]
    assert data["policy_type"] == policy_data["policy_type"]
    assert data["status"] == policy_data["status"]
    assert data["settings"] == policy_data["settings"]
    
    # Check database
    policy = await test_db.get(Policy, data["id"])
    assert policy is not None
    assert policy.name == policy_data["name"]


@pytest.mark.asyncio
async def test_get_policies(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test getting policies with pagination and filtering"""
    # Create test policies
    policies = []
    for i in range(5):
        policy = Policy(
            name=f"Test Policy {i}",
            description=f"Description for test policy {i}",
            policy_type=PolicyType.USER_PERMISSION if i % 2 == 0 else PolicyType.QUERY_LIMIT,
            status=PolicyStatus.ACTIVE if i % 3 == 0 else PolicyStatus.DRAFT,
            applies_to_roles=["user"],
            priority=i,
            settings={},
            created_by="test-admin-id"
        )
        test_db.add(policy)
        policies.append(policy)
    
    await test_db.commit()
    
    # Test getting all policies
    response = await client.get(
        "/api/admin/policies/",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 5
    assert len(data["policies"]) > 0
    
    # Test filtering by policy type
    response = await client.get(
        "/api/admin/policies/?policy_type=user_permission",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(p["policy_type"] == "user_permission" for p in data["policies"])
    
    # Test filtering by status
    response = await client.get(
        "/api/admin/policies/?status=active",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(p["status"] == "active" for p in data["policies"])


@pytest.mark.asyncio
async def test_get_policy_by_id(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test getting a policy by ID"""
    # Create test policy
    policy = Policy(
        name="Test Policy",
        description="Test policy description",
        policy_type=PolicyType.SECURITY,
        status=PolicyStatus.ACTIVE,
        applies_to_roles=["user", "admin"],
        priority=100,
        settings={
            "require_mfa": True,
            "password_expiry_days": 30
        },
        created_by="test-admin-id"
    )
    test_db.add(policy)
    await test_db.commit()
    await test_db.refresh(policy)
    
    # Get policy by ID
    response = await client.get(
        f"/api/admin/policies/{policy.id}",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == policy.id
    assert data["name"] == policy.name
    assert data["policy_type"] == policy.policy_type
    assert data["settings"] == policy.settings


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test updating a policy"""
    # Create test policy
    policy = Policy(
        name="Original Policy Name",
        description="Original description",
        policy_type=PolicyType.QUERY_LIMIT,
        status=PolicyStatus.DRAFT,
        applies_to_roles=["user"],
        priority=5,
        settings={
            "max_queries_per_day": 100,
            "max_query_execution_time": 30
        },
        created_by="test-admin-id"
    )
    test_db.add(policy)
    await test_db.commit()
    await test_db.refresh(policy)
    
    # Update data
    update_data = {
        "name": "Updated Policy Name",
        "description": "Updated description",
        "status": PolicyStatus.ACTIVE,
        "priority": 10,
        "settings": {
            "max_queries_per_day": 200,
            "max_query_execution_time": 60,
            "max_result_size": 5000
        }
    }
    
    # Update policy
    response = await client.put(
        f"/api/admin/policies/{policy.id}",
        headers=admin_token_headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["status"] == update_data["status"]
    assert data["priority"] == update_data["priority"]
    assert data["settings"] == update_data["settings"]
    
    # Check database
    updated_policy = await test_db.get(Policy, policy.id)
    assert updated_policy.name == update_data["name"]
    assert updated_policy.settings == update_data["settings"]


@pytest.mark.asyncio
async def test_delete_policy(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test deleting a policy"""
    # Create test policy
    policy = Policy(
        name="Policy to Delete",
        description="This policy will be deleted",
        policy_type=PolicyType.SECURITY,
        status=PolicyStatus.ACTIVE,
        applies_to_roles=["user"],
        priority=1,
        settings={},
        created_by="test-admin-id"
    )
    test_db.add(policy)
    await test_db.commit()
    await test_db.refresh(policy)
    
    # Delete policy
    response = await client.delete(
        f"/api/admin/policies/{policy.id}",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Check database
    deleted_policy = await test_db.get(Policy, policy.id)
    assert deleted_policy is None


@pytest.mark.asyncio
async def test_get_effective_policy_settings(client: AsyncClient, admin_token_headers: dict, test_db: AsyncSession):
    """Test getting effective policy settings"""
    # Create multiple policies with different priorities
    policies = [
        Policy(
            name="Low Priority User Permission Policy",
            description="Low priority policy",
            policy_type=PolicyType.USER_PERMISSION,
            status=PolicyStatus.ACTIVE,
            applies_to_roles=["user"],
            priority=1,
            settings={
                "allowed_roles": ["user"],
                "allowed_db_types": ["mssql"],
                "default_schemas_access": ["public"],
                "allow_schema_listing": True
            },
            created_by="test-admin-id"
        ),
        Policy(
            name="High Priority User Permission Policy",
            description="High priority policy",
            policy_type=PolicyType.USER_PERMISSION,
            status=PolicyStatus.ACTIVE,
            applies_to_roles=["user"],
            priority=10,
            settings={
                "allowed_db_types": ["mssql", "hana"],
                "default_tables_access": ["users", "products"]
            },
            created_by="test-admin-id"
        ),
        Policy(
            name="Inactive User Permission Policy",
            description="Inactive policy",
            policy_type=PolicyType.USER_PERMISSION,
            status=PolicyStatus.INACTIVE,
            applies_to_roles=["user"],
            priority=100,
            settings={
                "allowed_db_types": ["oracle"],
                "allow_schema_listing": False
            },
            created_by="test-admin-id"
        )
    ]
    
    for policy in policies:
        test_db.add(policy)
    
    await test_db.commit()
    
    # Get effective user permission settings
    response = await client.get(
        "/api/admin/policies/effective/user-permission?role=user",
        headers=admin_token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # High priority settings should override low priority settings
    assert "mssql" in data["allowed_db_types"]
    assert "hana" in data["allowed_db_types"]
    assert "users" in data["default_tables_access"]
    assert "products" in data["default_tables_access"]
    assert "public" in data["default_schemas_access"]
    assert data["allow_schema_listing"] is True
    
    # Inactive policy settings should not be included
    assert "oracle" not in data["allowed_db_types"]