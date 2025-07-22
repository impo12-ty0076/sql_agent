import pytest
from datetime import datetime
from pydantic import ValidationError

from sql_agent.backend.models.user import (
    User, UserCreate, UserPreferences, UserPermissions, 
    DatabasePermission, UserRole, ThemeType, DBType
)
from sql_agent.backend.models.auth import (
    LoginRequest, LoginResponse, SessionInfo
)
from sql_agent.backend.models.rbac import (
    Permission, ResourceType, PolicyEffect, ResourcePolicy
)

def test_user_preferences_validation():
    # Valid preferences
    prefs = UserPreferences(theme=ThemeType.LIGHT, results_per_page=50)
    assert prefs.theme == "light"
    assert prefs.results_per_page == 50
    
    # Invalid results_per_page (too small)
    with pytest.raises(ValidationError):
        UserPreferences(results_per_page=5)
    
    # Invalid results_per_page (too large)
    with pytest.raises(ValidationError):
        UserPreferences(results_per_page=1500)

def test_database_permission():
    # Valid permission
    perm = DatabasePermission(
        db_id="db123",
        db_type=DBType.MSSQL,
        allowed_schemas=["dbo", "sales"],
        allowed_tables=["users", "products"]
    )
    assert perm.db_id == "db123"
    assert perm.db_type == "mssql"
    assert "dbo" in perm.allowed_schemas
    assert "users" in perm.allowed_tables

def test_user_model():
    # Create valid user
    now = datetime.now()
    user = User(
        id="user123",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.USER,
        last_login=now,
        created_at=now,
        updated_at=now,
        preferences=UserPreferences(),
        permissions=UserPermissions(
            allowed_databases=[
                DatabasePermission(
                    db_id="db123",
                    db_type=DBType.MSSQL,
                    allowed_schemas=["dbo"],
                    allowed_tables=[]
                )
            ]
        )
    )
    
    assert user.id == "user123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == "user"
    assert len(user.permissions.allowed_databases) == 1
    assert user.permissions.allowed_databases[0].db_type == "mssql"

def test_login_request():
    # Valid login request
    login = LoginRequest(username="testuser", password="password123")
    assert login.username == "testuser"
    assert login.password == "password123"
    assert login.remember_me is False

def test_resource_policy():
    # Valid resource policy
    policy = ResourcePolicy(
        resource_type=ResourceType.DATABASE,
        resource_id="db123",
        permissions=[Permission.DB_CONNECT, Permission.DB_SCHEMA_VIEW],
        effect=PolicyEffect.ALLOW
    )
    
    assert policy.resource_type == "database"
    assert policy.resource_id == "db123"
    assert Permission.DB_CONNECT.value in policy.permissions
    assert policy.effect == "allow"