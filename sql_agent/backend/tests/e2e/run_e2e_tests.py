"""
End-to-end test runner for the SQL DB LLM Agent system.
"""
import os
import sys
import pytest
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))


def run_e2e_tests(test_pattern=None, verbose=False):
    """
    Run end-to-end tests with the specified pattern.
    
    Args:
        test_pattern: Optional pattern to filter tests
        verbose: Whether to show verbose output
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Set up the test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build pytest arguments
    pytest_args = [test_dir, "-v"] if verbose else [test_dir]
    
    # Add test pattern if specified
    if test_pattern:
        pytest_args.extend(["-k", test_pattern])
    
    # Add HTML report generation
    report_path = os.path.join(test_dir, "e2e_test_report.html")
    pytest_args.extend(["--html", report_path, "--self-contained-html"])
    
    # Run the tests
    print(f"Running end-to-end tests{f' matching pattern: {test_pattern}' if test_pattern else ''}")
    result = pytest.main(pytest_args)
    
    if result == 0:
        print(f"All end-to-end tests passed! Report saved to {report_path}")
    else:
        print(f"Some end-to-end tests failed. See report at {report_path}")
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run end-to-end tests for SQL DB LLM Agent")
    parser.add_argument("-k", "--pattern", help="Test pattern to match (e.g. 'auth' for auth tests)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    sys.exit(run_e2e_tests(args.pattern, args.verbose))