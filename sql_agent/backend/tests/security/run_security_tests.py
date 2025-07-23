"""
Main script to run all security tests and hardening.
"""
import os
import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import RESULTS_DIR


async def run_sql_injection_tests():
    """
    Run SQL injection tests.
    """
    print("\n=== Running SQL Injection Tests ===\n")
    
    from .test_sql_injection import main as sql_injection_main
    return await sql_injection_main()


async def run_auth_security_tests():
    """
    Run authentication and authorization security tests.
    """
    print("\n=== Running Authentication and Authorization Security Tests ===\n")
    
    from .test_auth_security import main as auth_security_main
    return await auth_security_main()


async def run_security_scans():
    """
    Run security vulnerability scans.
    """
    print("\n=== Running Security Vulnerability Scans ===\n")
    
    from .security_scanner import main as scanner_main
    return await scanner_main()


def run_security_hardening():
    """
    Apply security hardening measures.
    """
    print("\n=== Applying Security Hardening Measures ===\n")
    
    from .security_hardening import main as hardening_main
    return hardening_main()


def generate_summary_report(all_results):
    """
    Generate a summary report of all security tests and hardening.
    
    Args:
        all_results: Results of all security tests and hardening
    """
    print("\n=== Generating Summary Report ===\n")
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"security_summary_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# Security Testing and Hardening Summary Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        sql_injection_results = all_results.get("sql_injection", [])
        auth_security_results = all_results.get("auth_security", [])
        security_scan_results = all_results.get("security_scan", [])
        hardening_results = all_results.get("hardening", [])
        
        sql_injection_vulnerable = any(result.get("vulnerable", False) for result in sql_injection_results)
        auth_security_vulnerable = any(result.get("vulnerable", False) for result in auth_security_results)
        security_scan_vulnerable = any(result.get("vulnerable", False) for result in security_scan_results)
        hardening_success = all(result.get("success", False) for result in hardening_results) if hardening_results else False
        
        f.write(f"## Summary\n\n")
        f.write(f"- SQL Injection Tests: {'VULNERABLE' if sql_injection_vulnerable else 'SECURE'}\n")
        f.write(f"- Authentication and Authorization Tests: {'VULNERABLE' if auth_security_vulnerable else 'SECURE'}\n")
        f.write(f"- Security Vulnerability Scans: {'VULNERABLE' if security_scan_vulnerable else 'SECURE'}\n")
        f.write(f"- Security Hardening: {'COMPLETED' if hardening_success else 'PARTIALLY COMPLETED'}\n\n")
        
        # Overall security status
        overall_status = "SECURE" if not (sql_injection_vulnerable or auth_security_vulnerable or security_scan_vulnerable) and hardening_success else "VULNERABLE"
        f.write(f"### Overall Security Status: {overall_status}\n\n")
        
        # Key findings
        f.write(f"## Key Findings\n\n")
        
        # SQL injection findings
        if sql_injection_results:
            f.write(f"### SQL Injection\n\n")
            vulnerable_endpoints = []
            for result in sql_injection_results:
                if result.get("vulnerable", False):
                    vulnerable_endpoints.append(result.get("endpoint", "Unknown endpoint"))
            
            if vulnerable_endpoints:
                f.write(f"- Vulnerable endpoints: {', '.join(vulnerable_endpoints)}\n")
            else:
                f.write(f"- No SQL injection vulnerabilities found\n")
        
        # Authentication and authorization findings
        if auth_security_results:
            f.write(f"\n### Authentication and Authorization\n\n")
            vulnerable_categories = []
            for result in auth_security_results:
                if result.get("vulnerable", False):
                    vulnerable_categories.append(result.get("name", "Unknown category"))
            
            if vulnerable_categories:
                f.write(f"- Vulnerable categories: {', '.join(vulnerable_categories)}\n")
            else:
                f.write(f"- No authentication or authorization vulnerabilities found\n")
        
        # Security scan findings
        if security_scan_results:
            f.write(f"\n### Security Scans\n\n")
            vulnerable_categories = []
            for result in security_scan_results:
                if result.get("vulnerable", False):
                    vulnerable_categories.append(result.get("name", "Unknown category"))
            
            if vulnerable_categories:
                f.write(f"- Vulnerable categories: {', '.join(vulnerable_categories)}\n")
            else:
                f.write(f"- No security vulnerabilities found in scans\n")
        
        # Hardening results
        if hardening_results:
            f.write(f"\n### Security Hardening\n\n")
            successful_categories = []
            failed_categories = []
            for result in hardening_results:
                if result.get("success", False):
                    successful_categories.append(result.get("name", "Unknown category"))
                else:
                    failed_categories.append(result.get("name", "Unknown category"))
            
            if successful_categories:
                f.write(f"- Successfully hardened: {', '.join(successful_categories)}\n")
            
            if failed_categories:
                f.write(f"- Failed to harden: {', '.join(failed_categories)}\n")
        
        # Recommendations
        f.write(f"\n## Recommendations\n\n")
        
        if sql_injection_vulnerable or auth_security_vulnerable or security_scan_vulnerable:
            f.write(f"### Critical Issues\n\n")
            f.write(f"The following issues should be addressed immediately:\n\n")
            
            if sql_injection_vulnerable:
                f.write(f"1. Fix SQL injection vulnerabilities\n")
                f.write(f"   - Implement parameterized queries\n")
                f.write(f"   - Validate and sanitize all user inputs\n")
                f.write(f"   - Use ORM or prepared statements\n\n")
            
            if auth_security_vulnerable:
                f.write(f"2. Fix authentication and authorization vulnerabilities\n")
                f.write(f"   - Implement proper authentication checks\n")
                f.write(f"   - Secure JWT token handling\n")
                f.write(f"   - Implement proper access controls\n\n")
            
            if security_scan_vulnerable:
                f.write(f"3. Fix security vulnerabilities found in scans\n")
                f.write(f"   - Address code vulnerabilities\n")
                f.write(f"   - Implement security headers\n")
                f.write(f"   - Update vulnerable dependencies\n\n")
        
        f.write(f"### Ongoing Security Measures\n\n")
        f.write(f"1. **Regular Security Testing**: Implement regular security testing in CI/CD pipeline\n")
        f.write(f"2. **Dependency Management**: Regularly update dependencies and scan for vulnerabilities\n")
        f.write(f"3. **Security Training**: Provide security training for developers\n")
        f.write(f"4. **Security Monitoring**: Implement security monitoring and logging\n")
        f.write(f"5. **Incident Response**: Develop and test an incident response plan\n")
    
    print(f"Security summary report saved to {report_path}")
    return report_path


async def main():
    """
    Run all security tests and hardening.
    """
    parser = argparse.ArgumentParser(description="Run security tests and hardening")
    parser.add_argument("--sql", action="store_true", help="Run SQL injection tests")
    parser.add_argument("--auth", action="store_true", help="Run authentication and authorization security tests")
    parser.add_argument("--scan", action="store_true", help="Run security vulnerability scans")
    parser.add_argument("--harden", action="store_true", help="Apply security hardening measures")
    parser.add_argument("--all", action="store_true", help="Run all tests and hardening")
    
    args = parser.parse_args()
    
    # If no specific tests are selected, run all tests
    run_all = args.all or not (args.sql or args.auth or args.scan or args.harden)
    
    all_results = {}
    
    try:
        # Run selected tests
        if run_all or args.sql:
            all_results["sql_injection"] = await run_sql_injection_tests()
        
        if run_all or args.auth:
            all_results["auth_security"] = await run_auth_security_tests()
        
        if run_all or args.scan:
            all_results["security_scan"] = await run_security_scans()
        
        if run_all or args.harden:
            all_results["hardening"] = run_security_hardening()
        
        # Generate summary report
        summary_report = generate_summary_report(all_results)
        print(f"\nAll security tests and hardening completed. Summary report: {summary_report}")
    
    except Exception as e:
        print(f"Error running security tests and hardening: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())