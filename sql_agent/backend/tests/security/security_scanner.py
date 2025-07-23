"""
Security vulnerability scanner for the SQL DB LLM Agent system.
"""
import os
import sys
import re
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import subprocess

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import SECURITY_SCAN_PATHS, SECURITY_SCAN_EXCLUDE, SECURITY_HEADERS, RESULTS_DIR


def scan_code_for_vulnerabilities():
    """
    Scan code for security vulnerabilities.
    
    Returns:
        dict: Scan results
    """
    print("Scanning code for security vulnerabilities...")
    
    results = {
        "name": "Code Vulnerability Scan",
        "issues": [],
        "vulnerable": False
    }
    
    # Patterns to search for
    vulnerability_patterns = {
        "hardcoded_secrets": {
            "pattern": r"(password|secret|key|token|api_key|apikey|api key)\s*=\s*['\"][^'\"]+['\"]",
            "description": "Potential hardcoded secret",
            "severity": "high"
        },
        "sql_injection": {
            "pattern": r"execute\(\s*f?['\"][^'\"]*\{.*?\}[^'\"]*['\"]",
            "description": "Potential SQL injection vulnerability",
            "severity": "high"
        },
        "command_injection": {
            "pattern": r"(os\.system|subprocess\.call|subprocess\.Popen|eval|exec)\s*\([^)]*\)",
            "description": "Potential command injection vulnerability",
            "severity": "high"
        },
        "insecure_deserialization": {
            "pattern": r"(pickle\.loads|yaml\.load|eval|json\.loads\s*\([^)]*untrusted)",
            "description": "Potential insecure deserialization",
            "severity": "high"
        },
        "xss": {
            "pattern": r"(innerHTML|outerHTML|document\.write|eval)\s*=",
            "description": "Potential XSS vulnerability",
            "severity": "high"
        },
        "path_traversal": {
            "pattern": r"(open|file|read|write)\s*\([^)]*\.\.[^)]*\)",
            "description": "Potential path traversal vulnerability",
            "severity": "high"
        },
        "insecure_random": {
            "pattern": r"(random\.|Math\.random)",
            "description": "Use of potentially insecure random number generator",
            "severity": "medium"
        },
        "jwt_none_algorithm": {
            "pattern": r"(jwt\.decode|jwt\.verify).*algorithm\s*=\s*['\"]?none['\"]?",
            "description": "Use of 'none' algorithm in JWT",
            "severity": "high"
        },
        "weak_hash": {
            "pattern": r"(md5|sha1)\.",
            "description": "Use of weak hash algorithm",
            "severity": "medium"
        },
        "debug_enabled": {
            "pattern": r"(DEBUG|debug)\s*=\s*True",
            "description": "Debug mode enabled in production code",
            "severity": "medium"
        }
    }
    
    # File extensions to scan
    extensions_to_scan = [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css"]
    
    # Scan each path
    for scan_path in SECURITY_SCAN_PATHS:
        if not scan_path.exists():
            print(f"  Path {scan_path} does not exist, skipping...")
            continue
        
        print(f"  Scanning {scan_path}...")
        
        # Walk through the directory
        for root, dirs, files in os.walk(scan_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in SECURITY_SCAN_EXCLUDE]
            
            for file in files:
                # Check file extension
                if not any(file.endswith(ext) for ext in extensions_to_scan):
                    continue
                
                file_path = Path(root) / file
                
                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    # Check for vulnerabilities
                    for vuln_type, vuln_info in vulnerability_patterns.items():
                        matches = re.finditer(vuln_info["pattern"], content, re.IGNORECASE)
                        
                        for match in matches:
                            # Get line number
                            line_number = content[:match.start()].count("\n") + 1
                            line_content = content.splitlines()[line_number - 1].strip()
                            
                            # Add issue
                            results["issues"].append({
                                "type": vuln_type,
                                "description": vuln_info["description"],
                                "severity": vuln_info["severity"],
                                "file": str(file_path.relative_to(scan_path.parent)),
                                "line": line_number,
                                "code": line_content
                            })
                            results["vulnerable"] = True
                
                except Exception as e:
                    print(f"  Error scanning {file_path}: {e}")
    
    # Sort issues by severity
    results["issues"].sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3))
    
    if results["vulnerable"]:
        print(f"  Found {len(results['issues'])} potential security issues")
    else:
        print("  No security issues found in code scan")
    
    return results


async def scan_api_security_headers(session, base_url):
    """
    Scan API security headers.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
    
    Returns:
        dict: Scan results
    """
    print("Scanning API security headers...")
    
    results = {
        "name": "API Security Headers",
        "issues": [],
        "vulnerable": False
    }
    
    try:
        # Send request to API root
        async with session.get(f"{base_url}/") as response:
            headers = response.headers
            
            # Check for security headers
            for header in SECURITY_HEADERS:
                if header.lower() not in [h.lower() for h in headers.keys()]:
                    results["issues"].append({
                        "type": "missing_header",
                        "description": f"Missing security header: {header}",
                        "severity": "medium",
                        "endpoint": "/"
                    })
                    results["vulnerable"] = True
            
            # Check Content-Type header
            if "content-type" in headers:
                content_type = headers["content-type"]
                if "charset" not in content_type.lower():
                    results["issues"].append({
                        "type": "incomplete_header",
                        "description": "Content-Type header missing charset",
                        "severity": "low",
                        "endpoint": "/"
                    })
            
            # Check for information disclosure in headers
            sensitive_headers = ["server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version"]
            for header in sensitive_headers:
                if header.lower() in [h.lower() for h in headers.keys()]:
                    results["issues"].append({
                        "type": "information_disclosure",
                        "description": f"Information disclosure in header: {header}",
                        "severity": "low",
                        "endpoint": "/"
                    })
                    results["vulnerable"] = True
    
    except Exception as e:
        print(f"  Error scanning API security headers: {e}")
    
    if results["vulnerable"]:
        print(f"  Found {len(results['issues'])} security header issues")
    else:
        print("  No security header issues found")
    
    return results


def check_dependency_vulnerabilities():
    """
    Check for vulnerabilities in dependencies.
    
    Returns:
        dict: Scan results
    """
    print("Checking for vulnerabilities in dependencies...")
    
    results = {
        "name": "Dependency Vulnerabilities",
        "issues": [],
        "vulnerable": False
    }
    
    # Check Python dependencies
    try:
        # Use safety to check Python dependencies
        requirements_path = Path(__file__).parent.parent.parent / "requirements.txt"
        if requirements_path.exists():
            print("  Checking Python dependencies...")
            
            # Try to install safety if not already installed
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "safety"], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError:
                print("  Could not install safety, skipping Python dependency check")
            else:
                # Run safety check
                try:
                    safety_output = subprocess.run(
                        [sys.executable, "-m", "safety", "check", "-r", str(requirements_path), "--json"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
                    )
                    
                    if safety_output.returncode != 0:
                        # Parse JSON output
                        try:
                            vulnerabilities = json.loads(safety_output.stdout)
                            
                            for vuln in vulnerabilities.get("vulnerabilities", []):
                                results["issues"].append({
                                    "type": "python_dependency",
                                    "description": f"Vulnerable Python package: {vuln.get('package_name')} {vuln.get('vulnerable_spec')}",
                                    "severity": "high",
                                    "details": vuln.get("advisory"),
                                    "fix": f"Update to {vuln.get('package_name')}>={vuln.get('fixed_version') or 'latest'}"
                                })
                                results["vulnerable"] = True
                        except json.JSONDecodeError:
                            # If JSON parsing fails, try to extract information from text output
                            if "Found" in safety_output.stdout.decode("utf-8"):
                                results["issues"].append({
                                    "type": "python_dependency",
                                    "description": "Vulnerable Python packages found",
                                    "severity": "high",
                                    "details": safety_output.stdout.decode("utf-8")[:500]
                                })
                                results["vulnerable"] = True
                except Exception as e:
                    print(f"  Error running safety check: {e}")
    except Exception as e:
        print(f"  Error checking Python dependencies: {e}")
    
    # Check JavaScript dependencies
    try:
        # Check if package.json exists
        package_json_path = Path(__file__).parent.parent.parent.parent / "frontend" / "package.json"
        if package_json_path.exists():
            print("  Checking JavaScript dependencies...")
            
            # Try to install npm-audit-html if not already installed
            try:
                subprocess.run(["npm", "install", "-g", "npm-audit-html"], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError:
                print("  Could not install npm-audit-html, skipping JavaScript dependency check")
            else:
                # Run npm audit
                try:
                    npm_audit_output = subprocess.run(
                        ["npm", "audit", "--json"],
                        cwd=package_json_path.parent,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
                    )
                    
                    # Parse JSON output
                    try:
                        audit_result = json.loads(npm_audit_output.stdout)
                        
                        vulnerabilities = audit_result.get("vulnerabilities", {})
                        for pkg_name, vuln_info in vulnerabilities.items():
                            severity = vuln_info.get("severity", "low")
                            
                            results["issues"].append({
                                "type": "js_dependency",
                                "description": f"Vulnerable JavaScript package: {pkg_name} {vuln_info.get('version')}",
                                "severity": severity,
                                "details": vuln_info.get("overview", ""),
                                "fix": f"Update to {pkg_name}>={vuln_info.get('fixAvailable', {}).get('version', 'latest')}"
                            })
                            results["vulnerable"] = True
                    except json.JSONDecodeError:
                        # If JSON parsing fails, check if vulnerabilities were found
                        if "vulnerabilities" in npm_audit_output.stdout.decode("utf-8"):
                            results["issues"].append({
                                "type": "js_dependency",
                                "description": "Vulnerable JavaScript packages found",
                                "severity": "high",
                                "details": npm_audit_output.stdout.decode("utf-8")[:500]
                            })
                            results["vulnerable"] = True
                except Exception as e:
                    print(f"  Error running npm audit: {e}")
    except Exception as e:
        print(f"  Error checking JavaScript dependencies: {e}")
    
    if results["vulnerable"]:
        print(f"  Found {len(results['issues'])} vulnerable dependencies")
    else:
        print("  No vulnerable dependencies found")
    
    return results


def generate_security_scan_report(results):
    """
    Generate a report for security vulnerability scans.
    
    Args:
        results: Scan results
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"security_scan_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# Security Vulnerability Scan Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        vulnerable_count = sum(1 for result in results if result["vulnerable"])
        total_issues = sum(len(result["issues"]) for result in results)
        
        f.write(f"## Summary\n\n")
        f.write(f"- Total scan categories: {len(results)}\n")
        f.write(f"- Vulnerable categories: {vulnerable_count}\n")
        f.write(f"- Total issues found: {total_issues}\n")
        f.write(f"- Security status: {'VULNERABLE' if vulnerable_count > 0 else 'SECURE'}\n\n")
        
        # Detailed results
        f.write(f"## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### {result['name']}\n\n")
            f.write(f"- Status: {'VULNERABLE' if result['vulnerable'] else 'SECURE'}\n")
            f.write(f"- Issues found: {len(result['issues'])}\n\n")
            
            if result["vulnerable"]:
                f.write("#### Issues\n\n")
                
                # Group issues by severity
                high_issues = [issue for issue in result["issues"] if issue["severity"] == "high"]
                medium_issues = [issue for issue in result["issues"] if issue["severity"] == "medium"]
                low_issues = [issue for issue in result["issues"] if issue["severity"] == "low"]
                
                if high_issues:
                    f.write("##### High Severity\n\n")
                    for issue in high_issues:
                        f.write(f"- **{issue['description']}**\n")
                        if "file" in issue and "line" in issue:
                            f.write(f"  - Location: {issue['file']}:{issue['line']}\n")
                        if "code" in issue:
                            f.write(f"  - Code: `{issue['code']}`\n")
                        if "details" in issue:
                            f.write(f"  - Details: {issue['details']}\n")
                        if "fix" in issue:
                            f.write(f"  - Fix: {issue['fix']}\n")
                        f.write("\n")
                
                if medium_issues:
                    f.write("##### Medium Severity\n\n")
                    for issue in medium_issues:
                        f.write(f"- **{issue['description']}**\n")
                        if "file" in issue and "line" in issue:
                            f.write(f"  - Location: {issue['file']}:{issue['line']}\n")
                        if "code" in issue:
                            f.write(f"  - Code: `{issue['code']}`\n")
                        if "details" in issue:
                            f.write(f"  - Details: {issue['details']}\n")
                        if "fix" in issue:
                            f.write(f"  - Fix: {issue['fix']}\n")
                        f.write("\n")
                
                if low_issues:
                    f.write("##### Low Severity\n\n")
                    for issue in low_issues:
                        f.write(f"- **{issue['description']}**\n")
                        if "file" in issue and "line" in issue:
                            f.write(f"  - Location: {issue['file']}:{issue['line']}\n")
                        if "code" in issue:
                            f.write(f"  - Code: `{issue['code']}`\n")
                        if "details" in issue:
                            f.write(f"  - Details: {issue['details']}\n")
                        if "fix" in issue:
                            f.write(f"  - Fix: {issue['fix']}\n")
                        f.write("\n")
            
            f.write("\n")
        
        # Recommendations
        f.write(f"## Recommendations\n\n")
        
        if vulnerable_count > 0:
            f.write("### Critical Issues\n\n")
            f.write("The following issues should be addressed immediately:\n\n")
            
            # List high severity issues
            high_severity_issues = []
            for result in results:
                for issue in result["issues"]:
                    if issue["severity"] == "high":
                        high_severity_issues.append(issue)
            
            for issue in high_severity_issues:
                f.write(f"- {issue['description']}\n")
            
            f.write("\n### Implementation Recommendations\n\n")
            
            # Code vulnerability recommendations
            code_vulns = next((r for r in results if r["name"] == "Code Vulnerability Scan" and r["vulnerable"]), None)
            if code_vulns:
                f.write("#### Code Vulnerabilities\n\n")
                f.write("1. Fix identified code vulnerabilities\n")
                f.write("2. Implement secure coding practices\n")
                f.write("3. Use static code analysis tools in CI/CD pipeline\n")
                f.write("4. Conduct regular code reviews with security focus\n\n")
            
            # API security header recommendations
            header_vulns = next((r for r in results if r["name"] == "API Security Headers" and r["vulnerable"]), None)
            if header_vulns:
                f.write("#### API Security Headers\n\n")
                f.write("1. Implement all recommended security headers\n")
                f.write("2. Configure proper Content Security Policy\n")
                f.write("3. Remove information disclosure headers\n")
                f.write("4. Set secure and HttpOnly flags on cookies\n\n")
            
            # Dependency vulnerability recommendations
            dep_vulns = next((r for r in results if r["name"] == "Dependency Vulnerabilities" and r["vulnerable"]), None)
            if dep_vulns:
                f.write("#### Dependency Vulnerabilities\n\n")
                f.write("1. Update vulnerable dependencies to secure versions\n")
                f.write("2. Implement dependency scanning in CI/CD pipeline\n")
                f.write("3. Regularly audit and update dependencies\n")
                f.write("4. Consider using dependency lock files\n\n")
        else:
            f.write("The system appears to be secure based on the scans performed. Continue to maintain:\n\n")
            f.write("1. **Secure coding practices**: Continue following secure coding guidelines\n")
            f.write("2. **Regular security scans**: Continue performing regular security scans\n")
            f.write("3. **Dependency updates**: Keep dependencies up to date\n")
    
    print(f"Security vulnerability scan report saved to {report_path}")
    return report_path


async def main():
    """
    Run all security vulnerability scans.
    """
    print("Running security vulnerability scans...")
    
    # API base URL
    base_url = "http://localhost:8000"
    
    try:
        # Run code vulnerability scan
        code_scan_results = scan_code_for_vulnerabilities()
        
        # Run dependency vulnerability check
        dependency_results = check_dependency_vulnerabilities()
        
        # Run API security header scan
        async with aiohttp.ClientSession() as session:
            header_scan_results = await scan_api_security_headers(session, base_url)
        
        # Generate report
        all_results = [code_scan_results, header_scan_results, dependency_results]
        report_path = generate_security_scan_report(all_results)
        
        print(f"Security vulnerability scans completed. Report saved to {report_path}")
        
        return all_results
    except Exception as e:
        print(f"Error running security vulnerability scans: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())