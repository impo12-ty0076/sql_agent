"""
Security hardening for the SQL DB LLM Agent system.
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import json

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import RESULTS_DIR


def apply_security_headers():
    """
    Apply security headers to the API.
    
    Returns:
        dict: Results of the operation
    """
    print("Applying security headers...")
    
    results = {
        "name": "Security Headers",
        "changes": [],
        "success": False
    }
    
    # Path to the main.py file
    main_path = Path(__file__).parent.parent.parent / "main.py"
    
    if not main_path.exists():
        print(f"  Main file {main_path} not found.")
        return results
    
    try:
        # Read current implementation
        with open(main_path, "r") as f:
            main_content = f.read()
        
        # Check if security headers middleware already exists
        if "SecurityHeadersMiddleware" in main_content:
            print("  Security headers middleware already exists.")
            results["changes"].append({
                "file": str(main_path),
                "status": "skipped",
                "message": "Security headers middleware already exists"
            })
        else:
            # Create security headers middleware
            security_headers_middleware = """
class SecurityHeadersMiddleware:
    \"\"\"
    Middleware for adding security headers to responses.
    \"\"\"
    
    async def __call__(self, request: Request, call_next):
        \"\"\"
        Process the request and add security headers to the response.
        
        Args:
            request: The request object
            call_next: The next middleware or endpoint
        
        Returns:
            Response: The response object with security headers
        \"\"\"
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        
        return response
"""
            
            # Add import for Request if not already present
            if "from fastapi import Request" not in main_content and "from fastapi import" in main_content:
                main_content = main_content.replace(
                    "from fastapi import",
                    "from fastapi import Request,"
                )
            elif "from fastapi import" not in main_content:
                # Add import at the top
                import_section_end = main_content.find("# 내부 모듈 임포트")
                if import_section_end == -1:
                    import_section_end = main_content.find("# 로깅 설정")
                
                if import_section_end != -1:
                    main_content = main_content[:import_section_end] + "from fastapi import Request\n" + main_content[import_section_end:]
            
            # Add middleware class
            middleware_section_end = main_content.find("# FastAPI 앱 생성")
            if middleware_section_end == -1:
                middleware_section_end = main_content.find("app = FastAPI(")
            
            if middleware_section_end != -1:
                main_content = main_content[:middleware_section_end] + security_headers_middleware + "\n\n" + main_content[middleware_section_end:]
            
            # Add middleware to app
            middleware_add_section = main_content.find("# 로깅 미들웨어 추가")
            if middleware_add_section != -1:
                next_line_end = main_content.find("\n", middleware_add_section)
                if next_line_end != -1:
                    main_content = main_content[:next_line_end + 1] + "\n# 보안 헤더 미들웨어 추가\napp.middleware(\"http\")(SecurityHeadersMiddleware())\n" + main_content[next_line_end + 1:]
            
            # Write updated main.py
            with open(main_path, "w") as f:
                f.write(main_content)
            
            print("  Added security headers middleware.")
            results["changes"].append({
                "file": str(main_path),
                "status": "modified",
                "message": "Added security headers middleware"
            })
            results["success"] = True
    
    except Exception as e:
        print(f"  Error applying security headers: {e}")
        results["changes"].append({
            "file": str(main_path),
            "status": "error",
            "message": f"Error: {str(e)}"
        })
    
    return results


def implement_sql_injection_protection():
    """
    Implement SQL injection protection.
    
    Returns:
        dict: Results of the operation
    """
    print("Implementing SQL injection protection...")
    
    results = {
        "name": "SQL Injection Protection",
        "changes": [],
        "success": False
    }
    
    # Path to the query service file
    query_service_path = Path(__file__).parent.parent.parent / "services" / "query_service.py"
    
    if not query_service_path.exists():
        print(f"  Query service file {query_service_path} not found.")
        return results
    
    try:
        # Read current implementation
        with open(query_service_path, "r") as f:
            service_content = f.read()
        
        # Check if SQL injection protection already exists
        if "validate_sql_safety" in service_content:
            print("  SQL injection protection already exists.")
            results["changes"].append({
                "file": str(query_service_path),
                "status": "skipped",
                "message": "SQL injection protection already exists"
            })
        else:
            # Add SQL validation method
            sql_validation_method = """
    def validate_sql_safety(self, sql: str) -> tuple[bool, str]:
        \"\"\"
        Validate SQL query for safety.
        
        Args:
            sql: SQL query to validate
        
        Returns:
            tuple: (is_safe, error_message)
        \"\"\"
        # Convert to lowercase for case-insensitive checks
        sql_lower = sql.lower()
        
        # Check for data modification statements
        data_modification_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "replace"]
        for keyword in data_modification_keywords:
            if re.search(r'\\b' + keyword + r'\\b', sql_lower):
                return False, f"Data modification statements ({keyword.upper()}) are not allowed"
        
        # Check for multiple statements
        if ";" in sql_lower and not sql_lower.endswith(";"):
            return False, "Multiple SQL statements are not allowed"
        
        # Check for common SQL injection patterns
        injection_patterns = [
            r"--",                      # SQL comment
            r"/\\*.*?\\*/",             # SQL block comment
            r"\\bor\\s+1\\s*=\\s*1\\b", # OR 1=1
            r"\\bunion\\s+select\\b",   # UNION SELECT
            r"\\bexec\\b",              # EXEC
            r"\\bxp_\\w+",              # xp_ stored procedures
            r"\\bdrop\\s+table\\b",     # DROP TABLE
            r"\\bsys\\.",               # System tables
            r"\\binformation_schema\\." # Information schema
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_lower):
                return False, f"Potential SQL injection detected: {pattern}"
        
        # Limit query length
        if len(sql) > 10000:
            return False, "SQL query is too long"
        
        return True, ""
"""
            
            # Find the execute_query method
            execute_query_pos = service_content.find("async def execute_query")
            if execute_query_pos != -1:
                method_end = service_content.find("return", execute_query_pos)
                if method_end != -1:
                    # Find the position to insert validation
                    insert_pos = service_content.find("sql =", execute_query_pos, method_end)
                    if insert_pos != -1:
                        next_line_end = service_content.find("\n", insert_pos)
                        if next_line_end != -1:
                            # Add validation code
                            validation_code = """
        # Validate SQL safety
        is_safe, error_message = self.validate_sql_safety(sql)
        if not is_safe:
            raise ValueError(f"SQL validation failed: {error_message}")
"""
                            updated_content = service_content[:next_line_end + 1] + validation_code + service_content[next_line_end + 1:]
                            
                            # Add import for re if not already present
                            if "import re" not in updated_content:
                                import_section_end = updated_content.find("class QueryService")
                                if import_section_end != -1:
                                    updated_content = "import re\n" + updated_content
                            
                            # Add validation method
                            class_end = updated_content.rfind("}")
                            if class_end == -1:
                                class_end = len(updated_content)
                            
                            updated_content = updated_content[:class_end] + sql_validation_method + updated_content[class_end:]
                            
                            # Write updated service
                            with open(query_service_path, "w") as f:
                                f.write(updated_content)
                            
                            print("  Added SQL injection protection.")
                            results["changes"].append({
                                "file": str(query_service_path),
                                "status": "modified",
                                "message": "Added SQL injection protection"
                            })
                            results["success"] = True
    
    except Exception as e:
        print(f"  Error implementing SQL injection protection: {e}")
        results["changes"].append({
            "file": str(query_service_path),
            "status": "error",
            "message": f"Error: {str(e)}"
        })
    
    return results


def implement_rate_limiting():
    """
    Implement rate limiting.
    
    Returns:
        dict: Results of the operation
    """
    print("Implementing rate limiting...")
    
    results = {
        "name": "Rate Limiting",
        "changes": [],
        "success": False
    }
    
    # Path to the main.py file
    main_path = Path(__file__).parent.parent.parent / "main.py"
    
    if not main_path.exists():
        print(f"  Main file {main_path} not found.")
        return results
    
    try:
        # Read current implementation
        with open(main_path, "r") as f:
            main_content = f.read()
        
        # Check if rate limiting middleware already exists
        if "RateLimitingMiddleware" in main_content:
            print("  Rate limiting middleware already exists.")
            results["changes"].append({
                "file": str(main_path),
                "status": "skipped",
                "message": "Rate limiting middleware already exists"
            })
        else:
            # Create rate limiting middleware
            rate_limiting_middleware = """
class RateLimitingMiddleware:
    \"\"\"
    Middleware for rate limiting requests.
    \"\"\"
    def __init__(self):
        self.requests = {}
        self.window_size = 60  # 1 minute window
        self.max_requests = {
            "/api/auth/login": 10,      # 10 login attempts per minute
            "/api/query/execute": 30,   # 30 queries per minute
            "/api/query/natural": 20,   # 20 natural language queries per minute
            "default": 100              # 100 requests per minute for other endpoints
        }
    
    async def __call__(self, request: Request, call_next):
        \"\"\"
        Process the request and apply rate limiting.
        
        Args:
            request: The request object
            call_next: The next middleware or endpoint
        
        Returns:
            Response: The response object
        \"\"\"
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get path for rate limiting
        path = request.url.path
        
        # Get current time
        current_time = time.time()
        
        # Clean up old requests
        for key in list(self.requests.keys()):
            ip, req_path, req_time = key.split("|")
            if float(req_time) < current_time - self.window_size:
                del self.requests[key]
        
        # Count requests for this client and path
        count = 0
        for key in self.requests:
            ip, req_path, _ = key.split("|")
            if ip == client_ip and req_path == path:
                count += 1
        
        # Get rate limit for this path
        rate_limit = self.max_requests.get(path, self.max_requests["default"])
        
        # Check if rate limit exceeded
        if count >= rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later."
                }
            )
        
        # Add request to tracking
        self.requests[f"{client_ip}|{path}|{current_time}"] = True
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit - count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
"""
            
            # Add imports if not already present
            imports_to_add = []
            if "from fastapi import Request" not in main_content and "from fastapi import" in main_content:
                main_content = main_content.replace(
                    "from fastapi import",
                    "from fastapi import Request, status,"
                )
            elif "from fastapi import" not in main_content:
                imports_to_add.append("from fastapi import Request, status")
            
            if "from fastapi.responses import JSONResponse" not in main_content:
                imports_to_add.append("from fastapi.responses import JSONResponse")
            
            if "import time" not in main_content:
                imports_to_add.append("import time")
            
            # Add imports at the top
            if imports_to_add:
                import_section_end = main_content.find("# 내부 모듈 임포트")
                if import_section_end == -1:
                    import_section_end = main_content.find("# 로깅 설정")
                
                if import_section_end != -1:
                    main_content = main_content[:import_section_end] + "\n".join(imports_to_add) + "\n" + main_content[import_section_end:]
            
            # Add middleware class
            middleware_section_end = main_content.find("# FastAPI 앱 생성")
            if middleware_section_end == -1:
                middleware_section_end = main_content.find("app = FastAPI(")
            
            if middleware_section_end != -1:
                main_content = main_content[:middleware_section_end] + rate_limiting_middleware + "\n\n" + main_content[middleware_section_end:]
            
            # Add middleware to app
            middleware_add_section = main_content.find("# 로깅 미들웨어 추가")
            if middleware_add_section != -1:
                next_line_end = main_content.find("\n", middleware_add_section)
                if next_line_end != -1:
                    main_content = main_content[:next_line_end + 1] + "\n# 속도 제한 미들웨어 추가\napp.middleware(\"http\")(RateLimitingMiddleware())\n" + main_content[next_line_end + 1:]
            
            # Write updated main.py
            with open(main_path, "w") as f:
                f.write(main_content)
            
            print("  Added rate limiting middleware.")
            results["changes"].append({
                "file": str(main_path),
                "status": "modified",
                "message": "Added rate limiting middleware"
            })
            results["success"] = True
    
    except Exception as e:
        print(f"  Error implementing rate limiting: {e}")
        results["changes"].append({
            "file": str(main_path),
            "status": "error",
            "message": f"Error: {str(e)}"
        })
    
    return results


def implement_jwt_security():
    """
    Implement JWT security improvements.
    
    Returns:
        dict: Results of the operation
    """
    print("Implementing JWT security improvements...")
    
    results = {
        "name": "JWT Security",
        "changes": [],
        "success": False
    }
    
    # Path to the security.py file
    security_path = Path(__file__).parent.parent.parent / "core" / "security.py"
    
    if not security_path.exists():
        print(f"  Security file {security_path} not found.")
        return results
    
    try:
        # Read current implementation
        with open(security_path, "r") as f:
            security_content = f.read()
        
        # Check if JWT security improvements already exist
        if "verify_token" in security_content and "nbf" in security_content:
            print("  JWT security improvements already exist.")
            results["changes"].append({
                "file": str(security_path),
                "status": "skipped",
                "message": "JWT security improvements already exist"
            })
        else:
            # Update JWT token creation
            updated_content = security_content
            
            # Find create_access_token function
            create_token_pos = security_content.find("def create_access_token")
            if create_token_pos != -1:
                function_end = security_content.find("return encoded_jwt", create_token_pos)
                if function_end != -1:
                    # Find the position to update
                    to_encode_pos = security_content.find("to_encode = data.copy()", create_token_pos, function_end)
                    if to_encode_pos != -1:
                        next_line_end = security_content.find("\n", to_encode_pos)
                        if next_line_end != -1:
                            # Update token creation with additional claims
                            token_update_code = """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": str(uuid.uuid4()),
        "iss": "sql_db_llm_agent",
        "aud": ["sql_db_llm_agent_api"]
    })"""
                            updated_content = updated_content.replace(
                                "to_encode = data.copy()",
                                token_update_code
                            )
                            
                            # Add import for uuid if not already present
                            if "import uuid" not in updated_content:
                                import_section_end = updated_content.find("from datetime import")
                                if import_section_end != -1:
                                    next_line_end = updated_content.find("\n", import_section_end)
                                    if next_line_end != -1:
                                        updated_content = updated_content[:next_line_end + 1] + "import uuid\n" + updated_content[next_line_end + 1:]
            
            # Add token verification function
            verify_token_function = """
def verify_token(token: str) -> tuple[bool, dict]:
    \"\"\"
    Verify JWT token and return decoded payload.
    
    Args:
        token: JWT token to verify
    
    Returns:
        tuple: (is_valid, payload)
    \"\"\"
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "require": ["exp", "iat", "nbf", "sub"]
            },
            audience=["sql_db_llm_agent_api"]
        )
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, {"error": "Token has expired"}
    except jwt.InvalidTokenError as e:
        return False, {"error": f"Invalid token: {str(e)}"}
"""
            
            # Add verify_token function
            if "def verify_token" not in updated_content:
                # Find a good position to add the function
                oauth2_scheme_pos = updated_content.find("oauth2_scheme = OAuth2PasswordBearer")
                if oauth2_scheme_pos != -1:
                    next_line_end = updated_content.find("\n", oauth2_scheme_pos)
                    if next_line_end != -1:
                        updated_content = updated_content[:next_line_end + 2] + verify_token_function + updated_content[next_line_end + 2:]
            
            # Update get_current_user function to use verify_token
            get_user_pos = updated_content.find("async def get_current_user")
            if get_user_pos != -1:
                function_end = updated_content.find("return user", get_user_pos)
                if function_end != -1:
                    # Find the position to update
                    try_pos = updated_content.find("try:", get_user_pos, function_end)
                    if try_pos != -1:
                        except_pos = updated_content.find("except", try_pos, function_end)
                        if except_pos != -1:
                            # Update token verification
                            token_verify_code = """
    try:
        is_valid, payload = verify_token(token)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=payload.get("error", "Invalid authentication credentials"),
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception"""
                            updated_content = updated_content[:try_pos] + token_verify_code + updated_content[except_pos:]
            
            # Write updated security.py
            with open(security_path, "w") as f:
                f.write(updated_content)
            
            print("  Added JWT security improvements.")
            results["changes"].append({
                "file": str(security_path),
                "status": "modified",
                "message": "Added JWT security improvements"
            })
            results["success"] = True
    
    except Exception as e:
        print(f"  Error implementing JWT security improvements: {e}")
        results["changes"].append({
            "file": str(security_path),
            "status": "error",
            "message": f"Error: {str(e)}"
        })
    
    return results


def generate_security_hardening_report(results):
    """
    Generate a report for security hardening.
    
    Args:
        results: Results of security hardening operations
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"security_hardening_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# Security Hardening Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        successful_count = sum(1 for result in results if result["success"])
        f.write(f"## Summary\n\n")
        f.write(f"- Total hardening operations: {len(results)}\n")
        f.write(f"- Successful operations: {successful_count}\n")
        f.write(f"- Status: {'COMPLETED' if successful_count == len(results) else 'PARTIALLY COMPLETED'}\n\n")
        
        # Detailed results
        f.write(f"## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### {result['name']}\n\n")
            f.write(f"- Status: {'SUCCESS' if result['success'] else 'FAILED'}\n")
            f.write(f"- Changes: {len(result['changes'])}\n\n")
            
            if result["changes"]:
                f.write("#### Changes\n\n")
                for change in result["changes"]:
                    f.write(f"- File: `{change['file']}`\n")
                    f.write(f"  - Status: {change['status']}\n")
                    f.write(f"  - Message: {change['message']}\n\n")
            
            f.write("\n")
        
        # Recommendations
        f.write(f"## Additional Recommendations\n\n")
        
        f.write("### General Security Recommendations\n\n")
        f.write("1. **Regular Updates**: Keep all dependencies up to date\n")
        f.write("2. **Security Scanning**: Implement regular security scanning in CI/CD pipeline\n")
        f.write("3. **Logging**: Implement comprehensive security logging and monitoring\n")
        f.write("4. **Secrets Management**: Use a secure secrets management solution\n")
        f.write("5. **Input Validation**: Implement thorough input validation for all user inputs\n\n")
        
        f.write("### Environment-Specific Recommendations\n\n")
        f.write("1. **HTTPS**: Ensure all production deployments use HTTPS\n")
        f.write("2. **Firewall**: Configure firewall rules to restrict access\n")
        f.write("3. **Database Security**: Ensure database connections use TLS and proper authentication\n")
        f.write("4. **Container Security**: If using containers, implement container security best practices\n")
        f.write("5. **Network Segmentation**: Implement proper network segmentation\n")
    
    print(f"Security hardening report saved to {report_path}")
    return report_path


def main():
    """
    Apply security hardening measures.
    """
    print("Applying security hardening measures...")
    
    try:
        # Apply security headers
        headers_results = apply_security_headers()
        
        # Implement SQL injection protection
        sql_injection_results = implement_sql_injection_protection()
        
        # Implement rate limiting
        rate_limiting_results = implement_rate_limiting()
        
        # Implement JWT security improvements
        jwt_security_results = implement_jwt_security()
        
        # Generate report
        all_results = [headers_results, sql_injection_results, rate_limiting_results, jwt_security_results]
        report_path = generate_security_hardening_report(all_results)
        
        print(f"Security hardening completed. Report saved to {report_path}")
        
        return all_results
    except Exception as e:
        print(f"Error applying security hardening measures: {e}")
        return None


if __name__ == "__main__":
    main()