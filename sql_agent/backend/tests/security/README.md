# Security Tests for SQL DB LLM Agent

This directory contains security tests, vulnerability scanning tools, and security hardening scripts for the SQL DB LLM Agent system.

## Test Categories

The security tests are organized into the following categories:

1. **SQL Injection Tests** (`test_sql_injection.py`)
   - Query execution SQL injection testing
   - Natural language processing SQL injection testing
   - API parameter SQL injection testing

2. **Authentication and Authorization Tests** (`test_auth_security.py`)
   - Authentication bypass testing
   - JWT token vulnerability testing
   - Authorization bypass testing
   - Brute force protection testing

3. **Security Vulnerability Scanning** (`security_scanner.py`)
   - Code vulnerability scanning
   - API security header checking
   - Dependency vulnerability checking

4. **Security Hardening** (`security_hardening.py`)
   - Security header implementation
   - SQL injection protection implementation
   - Rate limiting implementation
   - JWT security improvements

## Running the Tests

You can run the security tests using the provided `run_security_tests.py` script:

```bash
# Run all security tests and hardening
python -m backend.tests.security.run_security_tests --all

# Run specific test categories
python -m backend.tests.security.run_security_tests --sql
python -m backend.tests.security.run_security_tests --auth
python -m backend.tests.security.run_security_tests --scan

# Apply security hardening
python -m backend.tests.security.run_security_tests --harden
```

## Test Results

Test results are saved in the `backend/tests/security/results` directory. The results include:

- SQL injection test reports
- Authentication and authorization security test reports
- Security vulnerability scan reports
- Security hardening reports
- Summary reports

## SQL Injection Testing

The SQL injection tests check for vulnerabilities in:

1. **Query Execution**: Tests if the system properly validates and sanitizes SQL queries before execution
2. **Natural Language Processing**: Tests if the natural language to SQL conversion is vulnerable to injection
3. **API Parameters**: Tests if API parameters are properly validated to prevent SQL injection

## Authentication and Authorization Testing

The authentication and authorization tests check for:

1. **Authentication Bypass**: Tests if protected endpoints can be accessed without authentication
2. **JWT Vulnerabilities**: Tests for vulnerabilities in JWT token handling
3. **Authorization Bypass**: Tests if users can access resources they shouldn't have access to
4. **Brute Force Protection**: Tests if the system has protection against brute force attacks

## Security Vulnerability Scanning

The security vulnerability scanning checks for:

1. **Code Vulnerabilities**: Scans code for common security vulnerabilities
2. **Security Headers**: Checks if proper security headers are implemented
3. **Dependency Vulnerabilities**: Checks for vulnerabilities in dependencies

## Security Hardening

The security hardening scripts implement:

1. **Security Headers**: Adds security headers to API responses
2. **SQL Injection Protection**: Implements SQL validation and sanitization
3. **Rate Limiting**: Adds rate limiting to prevent abuse
4. **JWT Security**: Improves JWT token security

## Best Practices

When running security tests:

1. Run tests in a controlled environment, not in production
2. Address critical vulnerabilities immediately
3. Regularly run security tests as part of CI/CD pipeline
4. Keep dependencies up to date
5. Implement security best practices in code
6. Train developers on security best practices
