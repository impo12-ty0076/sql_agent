"""
Authentication and authorization security tests for the SQL DB LLM Agent system.
"""
import asyncio
import aiohttp
import json
import sys
import time
import jwt
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import TEST_USER, TEST_ADMIN, AUTH_TEST_ENDPOINTS, JWT_TEST_SETTINGS, RESULTS_DIR


async def test_authentication_bypass(session, base_url):
    """
    Test authentication bypass vulnerabilities.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
    
    Returns:
        dict: Test results
    """
    print("Testing authentication bypass vulnerabilities...")
    
    results = {
        "name": "Authentication Bypass",
        "tests": [],
        "vulnerable": False
    }
    
    # Test accessing protected endpoints without authentication
    for endpoint in AUTH_TEST_ENDPOINTS:
        try:
            # Send request without authentication
            async with session.get(f"{base_url}{endpoint}") as response:
                status_code = response.status
                response_data = await response.text()
                
                # Check if authentication was bypassed (should return 401)
                is_vulnerable = status_code != 401
                
                results["tests"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "is_vulnerable": is_vulnerable,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                if is_vulnerable:
                    results["vulnerable"] = True
                    print(f"  Potential vulnerability found: Authentication bypass at {endpoint}")
        except Exception as e:
            results["tests"].append({
                "endpoint": endpoint,
                "error": str(e),
                "is_vulnerable": False
            })
    
    if results["vulnerable"]:
        print("  WARNING: Authentication bypass vulnerabilities detected!")
    else:
        print("  No authentication bypass vulnerabilities detected.")
    
    return results


async def test_jwt_vulnerabilities(session, base_url):
    """
    Test JWT token vulnerabilities.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
    
    Returns:
        dict: Test results
    """
    print("Testing JWT token vulnerabilities...")
    
    results = {
        "name": "JWT Vulnerabilities",
        "tests": [],
        "vulnerable": False
    }
    
    # Get a valid token first
    try:
        login_response = await session.post(
            f"{base_url}/api/auth/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        login_data = await login_response.json()
        valid_token = login_data["access_token"]
        
        # Decode the token to understand its structure
        try:
            # Try to decode without verification first to understand the structure
            decoded_token = jwt.decode(valid_token, options={"verify_signature": False})
            
            # Test expired token
            if JWT_TEST_SETTINGS["expired_token"]:
                # Create an expired token by modifying the exp claim
                expired_payload = decoded_token.copy()
                expired_payload["exp"] = int(time.time()) - 3600  # 1 hour ago
                
                # We don't have the secret key, so we'll just modify the payload and keep the original signature
                # This should fail validation, which is the expected behavior
                parts = valid_token.split(".")
                if len(parts) == 3:
                    header, _, signature = parts
                    modified_payload = jwt.encode(expired_payload, "", algorithm="none").split(".")[1]
                    expired_token = f"{header}.{modified_payload}.{signature}"
                    
                    # Test the expired token
                    async with session.get(
                        f"{base_url}/api/db/list",
                        headers={"Authorization": f"Bearer {expired_token}"}
                    ) as response:
                        status_code = response.status
                        response_data = await response.text()
                        
                        # Check if expired token was accepted (should return 401)
                        is_vulnerable = status_code != 401
                        
                        results["tests"].append({
                            "test_type": "expired_token",
                            "status_code": status_code,
                            "is_vulnerable": is_vulnerable,
                            "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                        })
                        
                        if is_vulnerable:
                            results["vulnerable"] = True
                            print("  Potential vulnerability found: Expired tokens are accepted")
            
            # Test tampered payload
            if JWT_TEST_SETTINGS["tampered_payload"]:
                # Create a tampered token by modifying the payload
                tampered_payload = decoded_token.copy()
                if "role" in tampered_payload:
                    tampered_payload["role"] = "admin"  # Attempt privilege escalation
                elif "user_role" in tampered_payload:
                    tampered_payload["user_role"] = "admin"
                
                # We don't have the secret key, so we'll just modify the payload and keep the original signature
                # This should fail validation, which is the expected behavior
                parts = valid_token.split(".")
                if len(parts) == 3:
                    header, _, signature = parts
                    modified_payload = jwt.encode(tampered_payload, "", algorithm="none").split(".")[1]
                    tampered_token = f"{header}.{modified_payload}.{signature}"
                    
                    # Test the tampered token
                    async with session.get(
                        f"{base_url}/api/admin/users",  # Admin endpoint
                        headers={"Authorization": f"Bearer {tampered_token}"}
                    ) as response:
                        status_code = response.status
                        response_data = await response.text()
                        
                        # Check if tampered token was accepted (should return 401 or 403)
                        is_vulnerable = status_code not in [401, 403]
                        
                        results["tests"].append({
                            "test_type": "tampered_payload",
                            "status_code": status_code,
                            "is_vulnerable": is_vulnerable,
                            "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                        })
                        
                        if is_vulnerable:
                            results["vulnerable"] = True
                            print("  Potential vulnerability found: Tampered tokens are accepted")
            
            # Test algorithm confusion (none algorithm)
            try:
                # Create a token with 'none' algorithm
                none_payload = decoded_token.copy()
                none_token = jwt.encode(none_payload, "", algorithm="none").replace(".", "..")
                
                # Test the none algorithm token
                async with session.get(
                    f"{base_url}/api/db/list",
                    headers={"Authorization": f"Bearer {none_token}"}
                ) as response:
                    status_code = response.status
                    response_data = await response.text()
                    
                    # Check if none algorithm token was accepted (should return 401)
                    is_vulnerable = status_code != 401
                    
                    results["tests"].append({
                        "test_type": "none_algorithm",
                        "status_code": status_code,
                        "is_vulnerable": is_vulnerable,
                        "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                    })
                    
                    if is_vulnerable:
                        results["vulnerable"] = True
                        print("  Potential vulnerability found: 'none' algorithm tokens are accepted")
            except Exception as e:
                results["tests"].append({
                    "test_type": "none_algorithm",
                    "error": str(e),
                    "is_vulnerable": False
                })
        
        except Exception as e:
            print(f"  Error decoding token: {e}")
    
    except Exception as e:
        print(f"  Error getting valid token: {e}")
    
    if results["vulnerable"]:
        print("  WARNING: JWT token vulnerabilities detected!")
    else:
        print("  No JWT token vulnerabilities detected.")
    
    return results


async def test_authorization_bypass(session, base_url):
    """
    Test authorization bypass vulnerabilities.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
    
    Returns:
        dict: Test results
    """
    print("Testing authorization bypass vulnerabilities...")
    
    results = {
        "name": "Authorization Bypass",
        "tests": [],
        "vulnerable": False
    }
    
    # Login as regular user
    try:
        user_login_response = await session.post(
            f"{base_url}/api/auth/login",
            data={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        user_login_data = await user_login_response.json()
        user_token = user_login_data["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test accessing admin endpoints as regular user
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/policies",
            "/api/admin/logs",
            "/api/admin/system/settings"
        ]
        
        for endpoint in admin_endpoints:
            try:
                # Send request as regular user
                async with session.get(f"{base_url}{endpoint}", headers=user_headers) as response:
                    status_code = response.status
                    response_data = await response.text()
                    
                    # Check if authorization was bypassed (should return 403)
                    is_vulnerable = status_code != 403
                    
                    results["tests"].append({
                        "endpoint": endpoint,
                        "status_code": status_code,
                        "is_vulnerable": is_vulnerable,
                        "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                    })
                    
                    if is_vulnerable:
                        results["vulnerable"] = True
                        print(f"  Potential vulnerability found: Authorization bypass at {endpoint}")
            except Exception as e:
                results["tests"].append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "is_vulnerable": False
                })
        
        # Test accessing other users' data
        # First, login as admin to create a test resource
        admin_login_response = await session.post(
            f"{base_url}/api/auth/login",
            data={
                "username": TEST_ADMIN["username"],
                "password": TEST_ADMIN["password"]
            }
        )
        admin_login_data = await admin_login_response.json()
        admin_token = admin_login_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a test query as admin
        admin_query_response = await session.post(
            f"{base_url}/api/query/execute",
            headers=admin_headers,
            json={
                "database_id": "1",  # Assuming database ID 1 exists
                "sql": "SELECT 1 AS test"
            }
        )
        admin_query_data = await admin_query_response.json()
        
        if "query_id" in admin_query_data:
            admin_query_id = admin_query_data["query_id"]
            
            # Try to access admin's query as regular user
            async with session.get(
                f"{base_url}/api/query/{admin_query_id}",
                headers=user_headers
            ) as response:
                status_code = response.status
                response_data = await response.text()
                
                # Check if authorization was bypassed (should return 403)
                is_vulnerable = status_code != 403
                
                results["tests"].append({
                    "endpoint": f"/api/query/{admin_query_id}",
                    "status_code": status_code,
                    "is_vulnerable": is_vulnerable,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                if is_vulnerable:
                    results["vulnerable"] = True
                    print(f"  Potential vulnerability found: Authorization bypass at /api/query/{admin_query_id}")
    
    except Exception as e:
        print(f"  Error testing authorization bypass: {e}")
    
    if results["vulnerable"]:
        print("  WARNING: Authorization bypass vulnerabilities detected!")
    else:
        print("  No authorization bypass vulnerabilities detected.")
    
    return results


async def test_brute_force_protection(session, base_url):
    """
    Test brute force protection.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
    
    Returns:
        dict: Test results
    """
    print("Testing brute force protection...")
    
    results = {
        "name": "Brute Force Protection",
        "tests": [],
        "vulnerable": True  # Assume vulnerable until proven otherwise
    }
    
    # Try multiple failed login attempts
    max_attempts = 10
    for i in range(max_attempts):
        try:
            # Send login request with incorrect password
            async with session.post(
                f"{base_url}/api/auth/login",
                data={
                    "username": TEST_USER["username"],
                    "password": f"wrong_password_{i}"
                }
            ) as response:
                status_code = response.status
                response_data = await response.text()
                
                results["tests"].append({
                    "attempt": i + 1,
                    "status_code": status_code,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                # If we get rate limited or account locked, brute force protection is working
                if status_code == 429 or "locked" in response_data.lower():
                    results["vulnerable"] = False
                    print(f"  Brute force protection detected after {i + 1} attempts")
                    break
        except Exception as e:
            results["tests"].append({
                "attempt": i + 1,
                "error": str(e)
            })
    
    if results["vulnerable"]:
        print("  WARNING: No brute force protection detected!")
    else:
        print("  Brute force protection is working.")
    
    return results


def generate_auth_security_report(results):
    """
    Generate a report for authentication and authorization security tests.
    
    Args:
        results: Test results
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"auth_security_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# Authentication and Authorization Security Test Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        vulnerable_count = sum(1 for result in results if result["vulnerable"])
        f.write(f"## Summary\n\n")
        f.write(f"- Total test categories: {len(results)}\n")
        f.write(f"- Vulnerable categories: {vulnerable_count}\n")
        f.write(f"- Security status: {'VULNERABLE' if vulnerable_count > 0 else 'SECURE'}\n\n")
        
        # Detailed results
        f.write(f"## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### {result['name']}\n\n")
            f.write(f"- Status: {'VULNERABLE' if result['vulnerable'] else 'SECURE'}\n")
            f.write(f"- Tests performed: {len(result['tests'])}\n\n")
            
            if result["vulnerable"]:
                f.write("#### Vulnerabilities Found\n\n")
                for test in result["tests"]:
                    if test.get("is_vulnerable", False):
                        if "endpoint" in test:
                            f.write(f"- Endpoint: `{test['endpoint']}`\n")
                        elif "test_type" in test:
                            f.write(f"- Test type: `{test['test_type']}`\n")
                        f.write(f"  - Status code: {test['status_code']}\n")
                        if "response_excerpt" in test:
                            f.write(f"  - Response excerpt: `{test['response_excerpt'][:100]}...`\n\n")
            
            f.write("\n")
        
        # Recommendations
        f.write(f"## Recommendations\n\n")
        
        if vulnerable_count > 0:
            f.write("### Critical Issues\n\n")
            f.write("The following issues should be addressed immediately:\n\n")
            
            for result in results:
                if result["vulnerable"]:
                    f.write(f"- Fix {result['name'].lower()} vulnerabilities\n")
            
            f.write("\n### Implementation Recommendations\n\n")
            
            # Authentication bypass recommendations
            auth_bypass = next((r for r in results if r["name"] == "Authentication Bypass" and r["vulnerable"]), None)
            if auth_bypass:
                f.write("#### Authentication Bypass\n\n")
                f.write("1. Ensure all protected endpoints verify authentication tokens\n")
                f.write("2. Implement proper middleware for authentication checks\n")
                f.write("3. Use consistent authentication patterns across all endpoints\n\n")
            
            # JWT vulnerabilities recommendations
            jwt_vulns = next((r for r in results if r["name"] == "JWT Vulnerabilities" and r["vulnerable"]), None)
            if jwt_vulns:
                f.write("#### JWT Vulnerabilities\n\n")
                f.write("1. Use strong signing keys for JWT tokens\n")
                f.write("2. Implement proper token validation including expiration checks\n")
                f.write("3. Reject tokens with 'none' algorithm\n")
                f.write("4. Validate all claims in the token\n\n")
            
            # Authorization bypass recommendations
            auth_bypass = next((r for r in results if r["name"] == "Authorization Bypass" and r["vulnerable"]), None)
            if auth_bypass:
                f.write("#### Authorization Bypass\n\n")
                f.write("1. Implement proper role-based access control\n")
                f.write("2. Verify user permissions before accessing resources\n")
                f.write("3. Implement object-level permissions for user data\n\n")
            
            # Brute force protection recommendations
            brute_force = next((r for r in results if r["name"] == "Brute Force Protection" and r["vulnerable"]), None)
            if brute_force:
                f.write("#### Brute Force Protection\n\n")
                f.write("1. Implement rate limiting for authentication endpoints\n")
                f.write("2. Add account lockout after multiple failed attempts\n")
                f.write("3. Implement CAPTCHA for login after suspicious activity\n\n")
        else:
            f.write("The system appears to be secure against authentication and authorization attacks. Continue to maintain:\n\n")
            f.write("1. **Strong authentication**: Continue using secure authentication mechanisms\n")
            f.write("2. **Proper authorization**: Continue enforcing proper access controls\n")
            f.write("3. **Regular testing**: Regularly test for authentication and authorization vulnerabilities\n")
    
    print(f"Authentication and authorization security test report saved to {report_path}")
    return report_path


async def main():
    """
    Run all authentication and authorization security tests.
    """
    print("Running authentication and authorization security tests...")
    
    # API base URL
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Run authentication and authorization tests
            auth_bypass_results = await test_authentication_bypass(session, base_url)
            jwt_results = await test_jwt_vulnerabilities(session, base_url)
            authz_bypass_results = await test_authorization_bypass(session, base_url)
            brute_force_results = await test_brute_force_protection(session, base_url)
            
            # Generate report
            all_results = [auth_bypass_results, jwt_results, authz_bypass_results, brute_force_results]
            report_path = generate_auth_security_report(all_results)
            
            print(f"Authentication and authorization security tests completed. Report saved to {report_path}")
            
            return all_results
    except Exception as e:
        print(f"Error running authentication and authorization security tests: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())