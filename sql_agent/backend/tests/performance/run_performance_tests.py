"""
Main script to run all performance tests and optimizations.
"""
import os
import sys
import argparse
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import RESULTS_DIR


def setup_test_environment():
    """
    Set up the test environment.
    """
    print("Setting up test environment...")
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Check if required packages are installed
    try:
        import locust
        import psutil
        import matplotlib
        import numpy
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Installing required packages...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "locust", "psutil", "matplotlib", "numpy"
        ])


async def run_db_performance_tests():
    """
    Run database performance tests.
    """
    print("\n=== Running Database Performance Tests ===\n")
    
    from .test_db_performance import main as db_main
    await db_main()


async def run_api_performance_tests():
    """
    Run API performance tests.
    """
    print("\n=== Running API Performance Tests ===\n")
    
    from .test_api_performance import main as api_main
    await api_main()


async def run_memory_profiling():
    """
    Run memory profiling tests.
    """
    print("\n=== Running Memory Profiling Tests ===\n")
    
    from .test_memory_profiling import main as memory_main
    await memory_main()


def run_load_tests(headless=True, users=50, duration=60):
    """
    Run load tests using Locust.
    
    Args:
        headless: Whether to run in headless mode
        users: Number of simulated users
        duration: Test duration in seconds
    """
    print("\n=== Running Load Tests ===\n")
    
    # Set environment variables for Locust
    os.environ["LOCUST_HEADLESS"] = "true" if headless else "false"
    os.environ["PERF_TEST_USERS"] = str(users)
    os.environ["PERF_TEST_DURATION"] = str(duration)
    
    # Import and run Locust tests
    from .locustfile import main as locust_main
    locust_main()


def run_system_optimization():
    """
    Run system optimization.
    """
    print("\n=== Running System Optimization ===\n")
    
    from .optimize_system import apply_optimizations
    apply_optimizations()


def generate_summary_report():
    """
    Generate a summary report of all performance tests.
    """
    print("\n=== Generating Summary Report ===\n")
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Find all performance test results
    db_results = list(results_dir.glob("*_performance_*.txt"))
    api_results = list(results_dir.glob("api_performance_*.txt"))
    memory_results = list(results_dir.glob("memory_profile_*.txt"))
    load_results = list(results_dir.glob("load_test_summary_*.txt"))
    optimization_results = list(results_dir.glob("optimization_report_*.md"))
    
    # Write summary report
    report_path = results_dir / f"performance_summary_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# Performance Testing Summary Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Tests Executed\n\n")
        f.write(f"- Database Performance Tests: {len(db_results)} result files\n")
        f.write(f"- API Performance Tests: {len(api_results)} result files\n")
        f.write(f"- Memory Profiling Tests: {len(memory_results)} result files\n")
        f.write(f"- Load Tests: {len(load_results)} result files\n")
        f.write(f"- Optimization Reports: {len(optimization_results)} files\n\n")
        
        # Include latest optimization report if available
        if optimization_results:
            latest_optimization = max(optimization_results, key=lambda p: p.stat().st_mtime)
            f.write("## Latest Optimization Report\n\n")
            with open(latest_optimization, "r") as opt_file:
                # Skip the title
                opt_content = opt_file.read()
                title_end = opt_content.find("\n\n")
                if title_end != -1:
                    f.write(opt_content[title_end + 2:])
                else:
                    f.write(opt_content)
        
        f.write("\n## Performance Test Results\n\n")
        f.write("See individual test result files for detailed information.\n\n")
        
        f.write("### Result Files\n\n")
        all_results = db_results + api_results + memory_results + load_results + optimization_results
        for result_file in sorted(all_results, key=lambda p: p.name):
            f.write(f"- {result_file.name}\n")
    
    print(f"Summary report generated at {report_path}")
    return report_path


async def main():
    """
    Run all performance tests and optimizations.
    """
    parser = argparse.ArgumentParser(description="Run performance tests and optimizations")
    parser.add_argument("--db", action="store_true", help="Run database performance tests")
    parser.add_argument("--api", action="store_true", help="Run API performance tests")
    parser.add_argument("--memory", action="store_true", help="Run memory profiling tests")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--optimize", action="store_true", help="Run system optimization")
    parser.add_argument("--all", action="store_true", help="Run all tests and optimizations")
    parser.add_argument("--users", type=int, default=50, help="Number of simulated users for load tests")
    parser.add_argument("--duration", type=int, default=60, help="Duration of load tests in seconds")
    parser.add_argument("--headless", action="store_true", help="Run load tests in headless mode")
    
    args = parser.parse_args()
    
    # If no specific tests are selected, run all tests
    run_all = args.all or not (args.db or args.api or args.memory or args.load or args.optimize)
    
    # Set up test environment
    setup_test_environment()
    
    try:
        # Run selected tests
        if run_all or args.db:
            await run_db_performance_tests()
        
        if run_all or args.api:
            await run_api_performance_tests()
        
        if run_all or args.memory:
            await run_memory_profiling()
        
        if run_all or args.load:
            run_load_tests(args.headless, args.users, args.duration)
        
        if run_all or args.optimize:
            run_system_optimization()
        
        # Generate summary report
        summary_report = generate_summary_report()
        print(f"\nAll performance tests completed. Summary report: {summary_report}")
    
    except Exception as e:
        print(f"Error running performance tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())