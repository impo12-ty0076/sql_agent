"""
Unit tests for system settings functionality
"""
import pytest
import os
import json
import tempfile
import zipfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from ..main import app
from ..db.models.system_settings import SystemSetting, DatabaseConnection, ApiKey, SystemBackup
from ..models.system_settings import (
    SystemSettingCreate, 
    SystemSettingUpdate, 
    DatabaseConnectionCreate,
    ApiKeyCreate,
    SystemBackupCreate,
    BackupType
)
from ..services.system_settings_service import (
    SystemSettingsService,
    DatabaseConnectionService,
    ApiKeyService,
    BackupService
)
from ..utils.encryption import encrypt_data, decrypt_data
from ..core.dependencies import get_current_admin_user, get_db


# Mock dependencies
@pytest.fixture
def mock_admin_user():
    return {
        "id": "test-admin-id",
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True
    }


@pytest.fixture
def client(mock_admin_user):
    # Override the dependencies
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user
    
    # Create test client
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides = {}


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = MagicMock()
    return db


# System Settings Tests

def test_get_system_settings(client):
    """Test getting system settings"""
    response = client.get("/api/admin/settings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_system_setting(client):
    """Test getting a specific system setting"""
    # First create a setting
    setting_data = {
        "key": "test_setting",
        "value": "test_value",
        "description": "Test setting description"
    }
    create_response = client.post("/api/admin/settings", json=setting_data)
    assert create_response.status_code == 200
    
    # Then get the setting
    response = client.get(f"/api/admin/settings/{setting_data['key']}")
    assert response.status_code == 200
    assert response.json()["key"] == setting_data["key"]
    assert response.json()["value"] == setting_data["value"]
    assert response.json()["description"] == setting_data["description"]


def test_create_system_setting(client):
    """Test creating a system setting"""
    setting_data = {
        "key": "new_setting",
        "value": "new_value",
        "description": "New setting description"
    }
    response = client.post("/api/admin/settings", json=setting_data)
    assert response.status_code == 200
    assert response.json()["key"] == setting_data["key"]
    assert response.json()["value"] == setting_data["value"]
    assert response.json()["description"] == setting_data["description"]


def test_update_system_setting(client):
    """Test updating a system setting"""
    # First create a setting
    setting_data = {
        "key": "update_setting",
        "value": "original_value",
        "description": "Original description"
    }
    create_response = client.post("/api/admin/settings", json=setting_data)
    assert create_response.status_code == 200
    
    # Then update the setting
    update_data = {
        "value": "updated_value",
        "description": "Updated description"
    }
    response = client.put(f"/api/admin/settings/{setting_data['key']}", json=update_data)
    assert response.status_code == 200
    assert response.json()["key"] == setting_data["key"]
    assert response.json()["value"] == update_data["value"]
    assert response.json()["description"] == update_data["description"]


def test_delete_system_setting(client):
    """Test deleting a system setting"""
    # First create a setting
    setting_data = {
        "key": "delete_setting",
        "value": "delete_value",
        "description": "Setting to delete"
    }
    create_response = client.post("/api/admin/settings", json=setting_data)
    assert create_response.status_code == 200
    
    # Then delete the setting
    response = client.delete(f"/api/admin/settings/{setting_data['key']}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify it's deleted
    get_response = client.get(f"/api/admin/settings/{setting_data['key']}")
    assert get_response.status_code == 404


# Database Connection Tests

def test_get_database_connections(client):
    """Test getting database connections"""
    response = client.get("/api/admin/connections")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_database_connection(client):
    """Test creating a database connection"""
    connection_data = {
        "name": "Test DB",
        "type": "mssql",
        "host": "localhost",
        "port": "1433",
        "username": "sa",
        "password": "Password123!",
        "database": "testdb",
        "options": {"encrypt": True},
        "is_active": True
    }
    response = client.post("/api/admin/connections", json=connection_data)
    assert response.status_code == 200
    assert response.json()["name"] == connection_data["name"]
    assert response.json()["type"] == connection_data["type"]
    assert response.json()["host"] == connection_data["host"]
    assert response.json()["port"] == connection_data["port"]
    assert response.json()["username"] == connection_data["username"]
    assert response.json()["database"] == connection_data["database"]
    assert response.json()["is_active"] == connection_data["is_active"]
    
    # Password should not be returned
    assert "password" not in response.json()


def test_update_database_connection(client):
    """Test updating a database connection"""
    # First create a connection
    connection_data = {
        "name": "Update DB",
        "type": "mssql",
        "host": "localhost",
        "port": "1433",
        "username": "sa",
        "password": "Password123!",
        "database": "updatedb",
        "options": {"encrypt": True},
        "is_active": True
    }
    create_response = client.post("/api/admin/connections", json=connection_data)
    assert create_response.status_code == 200
    connection_id = create_response.json()["id"]
    
    # Then update the connection
    update_data = {
        "name": "Updated DB",
        "host": "newhost",
        "port": "1434",
        "username": "newuser",
        "password": "NewPassword123!",
        "database": "newdb",
        "options": {"encrypt": False},
        "is_active": False
    }
    response = client.put(f"/api/admin/connections/{connection_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]
    assert response.json()["host"] == update_data["host"]
    assert response.json()["port"] == update_data["port"]
    assert response.json()["username"] == update_data["username"]
    assert response.json()["database"] == update_data["database"]
    assert response.json()["is_active"] == update_data["is_active"]


def test_delete_database_connection(client):
    """Test deleting a database connection"""
    # First create a connection
    connection_data = {
        "name": "Delete DB",
        "type": "mssql",
        "host": "localhost",
        "port": "1433",
        "username": "sa",
        "password": "Password123!",
        "database": "deletedb",
        "is_active": True
    }
    create_response = client.post("/api/admin/connections", json=connection_data)
    assert create_response.status_code == 200
    connection_id = create_response.json()["id"]
    
    # Then delete the connection
    response = client.delete(f"/api/admin/connections/{connection_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify it's deleted
    get_response = client.get(f"/api/admin/connections/{connection_id}")
    assert get_response.status_code == 404


def test_test_database_connection(client):
    """Test testing a database connection"""
    # First create a connection
    connection_data = {
        "name": "Test Connection",
        "type": "mssql",
        "host": "localhost",
        "port": "1433",
        "username": "sa",
        "password": "Password123!",
        "database": "testdb",
        "is_active": True
    }
    create_response = client.post("/api/admin/connections", json=connection_data)
    assert create_response.status_code == 200
    connection_id = create_response.json()["id"]
    
    # Mock the test_connection method to return success
    with patch('app.services.system_settings_service.DatabaseConnectionService.test_connection', 
               return_value={"success": True, "message": "Connection successful"}):
        response = client.post(f"/api/admin/connections/{connection_id}/test")
        assert response.status_code == 200
        assert response.json()["success"] is True


# API Key Tests

def test_get_api_keys(client):
    """Test getting API keys"""
    response = client.get("/api/admin/api-keys")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_api_key(client):
    """Test creating an API key"""
    api_key_data = {
        "name": "Test API Key",
        "service": "openai",
        "key": "sk-test123456789",
        "is_active": True
    }
    response = client.post("/api/admin/api-keys", json=api_key_data)
    assert response.status_code == 200
    assert response.json()["name"] == api_key_data["name"]
    assert response.json()["service"] == api_key_data["service"]
    assert response.json()["is_active"] == api_key_data["is_active"]
    
    # Key should not be returned
    assert "key" not in response.json()


def test_update_api_key(client):
    """Test updating an API key"""
    # First create an API key
    api_key_data = {
        "name": "Update API Key",
        "service": "openai",
        "key": "sk-update123456789",
        "is_active": True
    }
    create_response = client.post("/api/admin/api-keys", json=api_key_data)
    assert create_response.status_code == 200
    key_id = create_response.json()["id"]
    
    # Then update the API key
    update_data = {
        "name": "Updated API Key",
        "key": "sk-updated987654321",
        "is_active": False
    }
    response = client.put(f"/api/admin/api-keys/{key_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]
    assert response.json()["is_active"] == update_data["is_active"]


def test_delete_api_key(client):
    """Test deleting an API key"""
    # First create an API key
    api_key_data = {
        "name": "Delete API Key",
        "service": "openai",
        "key": "sk-delete123456789",
        "is_active": True
    }
    create_response = client.post("/api/admin/api-keys", json=api_key_data)
    assert create_response.status_code == 200
    key_id = create_response.json()["id"]
    
    # Then delete the API key
    response = client.delete(f"/api/admin/api-keys/{key_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify it's deleted
    get_response = client.get(f"/api/admin/api-keys/{key_id}")
    assert get_response.status_code == 404


def test_test_api_key(client):
    """Test testing an API key"""
    # First create an API key
    api_key_data = {
        "name": "Test API Key",
        "service": "openai",
        "key": "sk-test123456789",
        "is_active": True
    }
    create_response = client.post("/api/admin/api-keys", json=api_key_data)
    assert create_response.status_code == 200
    key_id = create_response.json()["id"]
    
    # Mock the test_api_key method to return success
    with patch('app.services.system_settings_service.ApiKeyService.test_api_key', 
               return_value={"success": True, "message": "API key is valid"}):
        response = client.post(f"/api/admin/api-keys/{key_id}/test")
        assert response.status_code == 200
        assert response.json()["success"] is True


# Backup Tests

def test_get_backups(client):
    """Test getting backups"""
    response = client.get("/api/admin/backups")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch('app.services.system_settings_service.BackupService.create_backup')
def test_create_backup(mock_create_backup, client):
    """Test creating a backup"""
    # Mock the create_backup method
    mock_backup = {
        "id": "test-backup-id",
        "name": "Test Backup",
        "description": "Test backup description",
        "backup_type": "settings",
        "size_bytes": "1024",
        "metadata": {"timestamp": "20250101_120000"},
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "test-admin-id"
    }
    mock_create_backup.return_value = MagicMock(**mock_backup)
    
    backup_data = {
        "name": "Test Backup",
        "description": "Test backup description",
        "backup_type": "settings"
    }
    response = client.post("/api/admin/backups", json=backup_data)
    assert response.status_code == 200
    assert response.json()["name"] == backup_data["name"]
    assert response.json()["description"] == backup_data["description"]
    assert response.json()["backup_type"] == backup_data["backup_type"]


@patch('app.services.system_settings_service.BackupService.delete_backup')
def test_delete_backup(mock_delete_backup, client):
    """Test deleting a backup"""
    # Mock the delete_backup method
    mock_delete_backup.return_value = True
    
    backup_id = "test-backup-id"
    response = client.delete(f"/api/admin/backups/{backup_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@patch('app.services.system_settings_service.BackupService.restore_backup')
def test_restore_backup(mock_restore_backup, client):
    """Test restoring a backup"""
    # Mock the restore_backup method
    mock_restore_backup.return_value = {
        "success": True,
        "message": "Backup restored successfully",
        "details": {
            "backup_id": "test-backup-id",
            "backup_type": "settings",
            "restore_options": {"restore_settings": True}
        }
    }
    
    backup_id = "test-backup-id"
    restore_options = {"restore_settings": True}
    response = client.post(f"/api/admin/backups/{backup_id}/restore", json=restore_options)
    assert response.status_code == 200
    assert response.json()["success"] is True


@patch('app.services.system_settings_service.BackupService.download_backup')
@patch('fastapi.responses.FileResponse')
def test_download_backup(mock_file_response, mock_download_backup, client):
    """Test downloading a backup"""
    # Mock the download_backup method
    mock_download_backup.return_value = {
        "file_path": "/path/to/backup.zip",
        "file_name": "backup.zip"
    }
    
    # Mock FileResponse
    mock_file_response.return_value = {"status": "success"}
    
    backup_id = "test-backup-id"
    response = client.get(f"/api/admin/backups/{backup_id}/download")
    assert response.status_code == 200
    
    # Test with non-existent backup
    mock_download_backup.return_value = None
    response = client.get(f"/api/admin/backups/non-existent-id/download")
    assert response.status_code == 404


# Service Layer Tests

def test_system_settings_service(mock_db):
    """Test SystemSettingsService"""
    # Mock the database queries
    mock_setting = MagicMock()
    mock_setting.key = "test_key"
    mock_setting.value = "test_value"
    mock_setting.description = "test description"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_setting
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_setting]
    
    # Test get_setting
    setting = SystemSettingsService.get_setting(mock_db, "test_key")
    assert setting is not None
    assert setting.key == "test_key"
    
    # Test get_settings
    settings = SystemSettingsService.get_settings(mock_db)
    assert len(settings) == 1
    assert settings[0].key == "test_key"
    
    # Test create_setting
    new_setting = SystemSettingCreate(key="new_key", value="new_value", description="new description")
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    created_setting = SystemSettingsService.create_setting(mock_db, new_setting)
    assert created_setting is not None
    
    # Test update_setting
    update_setting = SystemSettingUpdate(value="updated_value", description="updated description")
    updated_setting = SystemSettingsService.update_setting(mock_db, "test_key", update_setting)
    assert updated_setting is not None
    
    # Test delete_setting
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    
    result = SystemSettingsService.delete_setting(mock_db, "test_key")
    assert result is True


def test_database_connection_service(mock_db):
    """Test DatabaseConnectionService"""
    # Mock the database queries
    mock_connection = MagicMock()
    mock_connection.id = "test-connection-id"
    mock_connection.name = "Test Connection"
    mock_connection.type = "mssql"
    mock_connection.host = "localhost"
    mock_connection.port = "1433"
    mock_connection.username = "sa"
    mock_connection.database = "testdb"
    mock_connection.is_active = True
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_connection]
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_connection]
    
    # Test get_connection
    connection = DatabaseConnectionService.get_connection(mock_db, "test-connection-id")
    assert connection is not None
    assert connection.id == "test-connection-id"
    
    # Test get_connections
    connections = DatabaseConnectionService.get_connections(mock_db)
    assert len(connections) == 1
    assert connections[0].id == "test-connection-id"
    
    # Test create_connection
    new_connection = DatabaseConnectionCreate(
        name="New Connection",
        type="mssql",
        host="newhost",
        port="1433",
        username="newuser",
        password="newpassword",
        database="newdb",
        is_active=True
    )
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    created_connection = DatabaseConnectionService.create_connection(mock_db, new_connection)
    assert created_connection is not None
    
    # Test update_connection
    update_connection = MagicMock()
    update_connection.name = "Updated Connection"
    update_connection.host = "updatedhost"
    update_connection.port = "1434"
    update_connection.username = "updateduser"
    update_connection.password = None
    update_connection.database = "updateddb"
    update_connection.is_active = False
    
    updated_connection = DatabaseConnectionService.update_connection(mock_db, "test-connection-id", update_connection)
    assert updated_connection is not None
    
    # Test delete_connection
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    
    result = DatabaseConnectionService.delete_connection(mock_db, "test-connection-id")
    assert result is True
    
    # Test test_connection
    test_result = DatabaseConnectionService.test_connection(mock_db, "test-connection-id")
    assert test_result["success"] is True


def test_api_key_service(mock_db):
    """Test ApiKeyService"""
    # Mock the database queries
    mock_api_key = MagicMock()
    mock_api_key.id = "test-api-key-id"
    mock_api_key.name = "Test API Key"
    mock_api_key.service = "openai"
    mock_api_key.is_active = True
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_api_key
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_api_key]
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_api_key]
    
    # Test get_api_key
    api_key = ApiKeyService.get_api_key(mock_db, "test-api-key-id")
    assert api_key is not None
    assert api_key.id == "test-api-key-id"
    
    # Test get_api_keys
    api_keys = ApiKeyService.get_api_keys(mock_db)
    assert len(api_keys) == 1
    assert api_keys[0].id == "test-api-key-id"
    
    # Test create_api_key
    from pydantic import SecretStr
    new_api_key = ApiKeyCreate(
        name="New API Key",
        service="openai",
        key=SecretStr("sk-new123456789"),
        is_active=True
    )
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    created_api_key = ApiKeyService.create_api_key(mock_db, new_api_key)
    assert created_api_key is not None
    
    # Test update_api_key
    from pydantic import SecretStr
    update_api_key = MagicMock()
    update_api_key.name = "Updated API Key"
    update_api_key.key = SecretStr("sk-updated123456789")
    update_api_key.is_active = False
    
    updated_api_key = ApiKeyService.update_api_key(mock_db, "test-api-key-id", update_api_key)
    assert updated_api_key is not None
    
    # Test delete_api_key
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    
    result = ApiKeyService.delete_api_key(mock_db, "test-api-key-id")
    assert result is True
    
    # Test test_api_key
    test_result = ApiKeyService.test_api_key(mock_db, "test-api-key-id")
    assert test_result["success"] is True


@patch('os.path.exists')
@patch('os.path.getsize')
@patch('zipfile.ZipFile')
@patch('json.dump')
@patch('builtins.open')
@patch('tempfile.TemporaryDirectory')
def test_backup_service(mock_temp_dir, mock_open, mock_json_dump, mock_zipfile, mock_getsize, mock_exists, mock_db):
    """Test BackupService"""
    # Mock the database queries
    mock_backup = MagicMock()
    mock_backup.id = "test-backup-id"
    mock_backup.name = "Test Backup"
    mock_backup.description = "Test backup description"
    mock_backup.backup_type = "settings"
    mock_backup.file_path = "/path/to/backup.zip"
    mock_backup.metadata = {"timestamp": "20250101_120000"}
    mock_backup.size_bytes = "1024"
    mock_backup.created_at = datetime.utcnow()
    mock_backup.created_by = "test-admin-id"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_backup
    mock_db.query.return_value.order_by.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_backup]
    mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_backup]
    
    # Mock file operations
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/backup"
    mock_open.return_value.__enter__.return_value = MagicMock()
    mock_getsize.return_value = 1024
    mock_exists.return_value = True
    
    # Test get_backup
    backup = BackupService.get_backup(mock_db, "test-backup-id")
    assert backup is not None
    assert backup.id == "test-backup-id"
    
    # Test get_backups
    backups = BackupService.get_backups(mock_db)
    assert len(backups) == 1
    assert backups[0].id == "test-backup-id"
    
    # Test create_backup
    new_backup = SystemBackupCreate(
        name="New Backup",
        description="New backup description",
        backup_type=BackupType.SETTINGS
    )
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Mock the get_system_settings function
    mock_db.query.return_value.all.return_value = []
    
    created_backup = BackupService.create_backup(mock_db, new_backup, "test-admin-id")
    assert created_backup is not None
    
    # Test delete_backup
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None
    
    result = BackupService.delete_backup(mock_db, "test-backup-id")
    assert result is True
    
    # Test download_backup
    with patch('os.path.basename', return_value="backup.zip"):
        download_result = BackupService.download_backup(mock_db, "test-backup-id")
        assert download_result is not None
        assert download_result["file_path"] == "/path/to/backup.zip"
        assert download_result["file_name"] == "backup.zip"
    
    # Test download_backup with non-existent file
    mock_exists.return_value = False
    download_result = BackupService.download_backup(mock_db, "test-backup-id")
    assert download_result is None
    
    # Reset exists mock for subsequent tests
    mock_exists.return_value = True
    
    # Test restore_backup
    from ..models.system_settings import SystemRestoreRequest
    restore_request = SystemRestoreRequest(
        backup_id="test-backup-id",
        restore_options={"restore_settings": True}
    )
    
    # Mock zipfile extraction
    mock_zipfile.return_value.__enter__.return_value.extractall.return_value = None
    
    # Mock json loading
    with patch('json.load', return_value={"settings": []}):
        restore_result = BackupService.restore_backup(mock_db, restore_request, "test-admin-id")
        assert restore_result["success"] is True


# Encryption Tests

def test_encryption():
    """Test encryption utilities"""
    # Test encrypt_data and decrypt_data
    original_data = "sensitive_data"
    encrypted = encrypt_data(original_data)
    decrypted = decrypt_data(encrypted)
    
    assert encrypted != original_data
    assert decrypted == original_data
    
    # Test encryption failure handling
    with patch('app.utils.encryption.cipher_suite.encrypt', side_effect=Exception("Encryption failed")):
        encrypted = encrypt_data(original_data)
        assert encrypted.startswith("ENCRYPTION_FAILED:")
    
    # Test decryption failure handling
    with patch('app.utils.encryption.cipher_suite.decrypt', side_effect=Exception("Decryption failed")):
        decrypted = decrypt_data(encrypted)
        assert decrypted == "DECRYPTION_FAILED"