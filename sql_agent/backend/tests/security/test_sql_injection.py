"""
SQL injection tests for the SQL DB LLM Agent system.
"""
import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import TEST_USER, SQL_INJECTION_PAYLOADS, RESULTS_DIR


async def test_sql_injection_in_query_execution(session, base_url, headers, db_id):
    """
    Test SQL injection vulnerabilities in query execution.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
        headers: Request headers
        db_id: Database ID
    
    Returns:
        dict: Test results
    """
    print("Testing SQL injection in query execution...")
    
    results = {
        "endpoint": "/api/query/execute",
        "tests": [],
        "vulnerable": False
    }
    
    for payload in SQL_INJECTION_PAYLOADS:
        # Create a test query with the payload
        test_query = f"SELECT * FROM employees WHERE name = '{payload}'"
        
        try:
            # Execute the query
            async with session.post(
                f"{base_url}/api/query/execute",
                headers=headers,
                json={
                    "database_id": db_id,
                    "sql": test_query
                }
            ) as response:
                response_data = await response.text()
                status_code = response.status
                
                # Check if the query was rejected (should be)
                is_vulnerable = status_code == 200
                
                results["tests"].append({
                    "payload": payload,
                    "status_code": status_code,
                    "is_vulnerable": is_vulnerable,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                if is_vulnerable:
                    results["vulnerable"] = True
                    print(f"  Potential vulnerability found with payload: {payload}")
        except Exception as e:
            results["tests"].append({
                "payload": payload,
                "error": str(e),
                "is_vulnerable": False
            })
    
    if results["vulnerable"]:
        print("  WARNING: SQL injection vulnerabilities detected!")
    else:
        print("  No SQL injection vulnerabilities detected.")
    
    return results


async def test_sql_injection_in_natural_language(session, base_url, headers, db_id):
    """
    Test SQL injection vulnerabilities in natural language queries.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
        headers: Request headers
        db_id: Database ID
    
    Returns:
        dict: Test results
    """
    print("Testing SQL injection in natural language queries...")
    
    results = {
        "endpoint": "/api/query/natural",
        "tests": [],
        "vulnerable": False
    }
    
    for payload in SQL_INJECTION_PAYLOADS:
        # Create a test query with the payload
        test_query = f"Show me employees where name = '{payload}'"
        
        try:
            # Submit the natural language query
            async with session.post(
                f"{base_url}/api/query/natural",
                headers=headers,
                json={
                    "database_id": db_id,
                    "query": test_query
                }
            ) as response:
                response_data = await response.text()
                status_code = response.status
                
                # Check if the query was processed (should be, but the generated SQL should be safe)
                is_vulnerable = False
                
                if status_code == 200:
                    # Check if the generated SQL contains the raw payload
                    response_json = json.loads(response_data)
                    if "generated_sql" in response_json:
                        generated_sql = response_json["generated_sql"]
                        # Check if the payload is directly included in the SQL without proper escaping
                        is_vulnerable = payload in generated_sql and "'" + payload + "'" not in generated_sql
                
                results["tests"].append({
                    "payload": payload,
                    "status_code": status_code,
                    "is_vulnerable": is_vulnerable,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                if is_vulnerable:
                    results["vulnerable"] = True
                    print(f"  Potential vulnerability found with payload: {payload}")
        except Exception as e:
            results["tests"].append({
                "payload": payload,
                "error": str(e),
                "is_vulnerable": False
            })
    
    if results["vulnerable"]:
        print("  WARNING: SQL injection vulnerabilities detected in natural language processing!")
    else:
        print("  No SQL injection vulnerabilities detected in natural language processing.")
    
    return results


async def test_sql_injection_in_parameters(session, base_url, headers):
    """
    Test SQL injection vulnerabilities in API parameters.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
        headers: Request headers
    
    Returns:
        dict: Test results
    """
    print("Testing SQL injection in API parameters...")
    
    results = {
        "endpoint": "various",
        "tests": [],
        "vulnerable": False
    }
    
    # Test endpoints that might be vulnerable to SQL injection in parameters
    test_endpoints = [
        {"url": "/api/db/schema/{}", "method": "get", "param_name": "db_id"},
        {"url": "/api/history", "method": "get", "param_name": "search"},
        {"url": "/api/result/{}", "method": "get", "param_name": "result_id"},
        {"url": "/api/share/{}", "method": "get", "param_name": "share_id"}
    ]
    
    for endpoint in test_endpoints:
        for payload in SQL_INJECTION_PAYLOADS[:5]:  # Use a subset of payloads for brevity
            try:
                # Create the request URL with the payload
                if "{}" in endpoint["url"]:
                    url = f"{base_url}{endpoint['url'].format(payload)}"
                else:
                    url = f"{base_url}{endpoint['url']}?{endpoint['param_name']}={payload}"
                
                # Send the request
                if endpoint["method"] == "get":
                    async with session.get(url, headers=headers) as response:
                        response_data = await response.text()
                        status_code = response.status
                else:
                    async with session.post(url, headers=headers) as response:
                        response_data = await response.text()
                        status_code = response.status
                
                # Check for signs of SQL injection
                is_vulnerable = False
                
                # Look for SQL error messages that might indicate vulnerability
                sql_error_indicators = [
                    "syntax error",
                    "SQL syntax",
                    "mysql_fetch",
                    "ORA-",
                    "PostgreSQL",
                    "SQLite3::",
                    "Microsoft SQL Server",
                    "ODBC Driver",
                    "SAP HANA",
                    "unexpected token"
                ]
                
                for indicator in sql_error_indicators:
                    if indicator.lower() in response_data.lower():
                        is_vulnerable = True
                        break
                
                results["tests"].append({
                    "endpoint": endpoint["url"],
                    "param_name": endpoint["param_name"],
                    "payload": payload,
                    "status_code": status_code,
                    "is_vulnerable": is_vulnerable,
                    "response_excerpt": response_data[:200] if len(response_data) > 200 else response_data
                })
                
                if is_vulnerable:
                    results["vulnerable"] = True
                    print(f"  Potential vulnerability found in {endpoint['url']} with payload: {payload}")
            except Exception as e:
                results["tests"].append({
                    "endpoint": endpoint["url"],
                    "param_name": endpoint["param_name"],
                    "payload": payload,
                    "error": str(e),
                    "is_vulnerable": False
                })
    
    if results["vulnerable"]:
        print("  WARNING: SQL injection vulnerabilities detected in API parameters!")
    else:
        print("  No SQL injection vulnerabilities detected in API parameters.")
    
    return results


def generate_sql_injection_report(results):
    """
    Generate a report for SQL injection tests.
    
    Args:
        results: Test results
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"sql_injection_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# SQL Injection Test Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        vulnerable_count = sum(1 for result in results if result["vulnerable"])
        f.write(f"## Summary\n\n")
        f.write(f"- Total endpoints tested: {len(results)}\n")
        f.write(f"- Vulnerable endpoints: {vulnerable_count}\n")
        f.write(f"- Security status: {'VULNERABLE' if vulnerable_count > 0 else 'SECURE'}\n\n")
        
        # Detailed results
        f.write(f"## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### Endpoint: {result['endpoint']}\n\n")
            f.write(f"- Status: {'VULNERABLE' if result['vulnerable'] else 'SECURE'}\n")
            f.write(f"- Tests performed: {len(result['tests'])}\n\n")
            
            if result["vulnerable"]:
                f.write("#### Vulnerabilities Found\n\n")
                for test in result["tests"]:
                    if test.get("is_vulnerable", False):
                        f.write(f"- Payload: `{test['payload']}`\n")
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
                    f.write(f"- Fix SQL injection vulnerability in {result['endpoint']}\n")
            
            f.write("\n### Implementation Recommendations\n\n")
            f.write("1. **Use parameterized queries**: Always use parameterized queries or prepared statements\n")
            f.write("2. **Input validation**: Validate and sanitize all user inputs\n")
            f.write("3. **Use ORM**: Consider using an ORM framework that handles SQL escaping\n")
            f.write("4. **Least privilege**: Ensure database users have minimal required permissions\n")
            f.write("5. **Error handling**: Implement proper error handling to avoid exposing SQL errors\n")
        else:
            f.write("The system appears to be secure against SQL injection attacks. Continue to maintain:\n\n")
            f.write("1. **Parameterized queries**: Continue using parameterized queries or prepared statements\n")
            f.write("2. **Input validation**: Continue validating and sanitizing all user inputs\n")
            f.write("3. **Regular testing**: Regularly test for SQL injection vulnerabilities\n")
    
    print(f"SQL injection test report saved to {report_path}")
    return report_path


async def main():
    """
    Run all SQL injection tests.
    """
    print("Running SQL injection tests...")
    
    # API base URL
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Login
            login_response = await session.post(
                f"{base_url}/api/auth/login",
                data={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            login_data = await login_response.json()
            token = login_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get available databases
            db_response = await session.get(
                f"{base_url}/api/db/list",
                headers=headers
            )
            db_list = await db_response.json()
            db_id = db_list[0]["id"]
            
            # Connect to database
            await session.post(
                f"{base_url}/api/db/connect/{db_id}",
                headers=headers
            )
            
            # Run SQL injection tests
            query_execution_results = await test_sql_injection_in_query_execution(session, base_url, headers, db_id)
            natural_language_results = await test_sql_injection_in_natural_language(session, base_url, headers, db_id)
            parameter_results = await test_sql_injection_in_parameters(session, base_url, headers)
            
            # Generate report
            all_results = [query_execution_results, natural_language_results, parameter_results]
            report_path = generate_sql_injection_report(all_results)
            
            print(f"SQL injection tests completed. Report saved to {report_path}")
            
            return all_results
    except Exception as e:
        print(f"Error running SQL injection tests: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())