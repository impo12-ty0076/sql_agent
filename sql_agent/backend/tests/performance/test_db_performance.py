"""
Database performance tests for the SQL DB LLM Agent system.
"""
import time
import asyncio
import statistics
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.db.connectors.base_connector import BaseConnector
from backend.db.connectors.mssql_connector import MSSQLConnector
from backend.db.connectors.hana_connector import HanaConnector
from backend.core.config import settings
from .config import TEST_QUERIES, RESULTS_DIR


async def measure_query_performance(connector, query, iterations=10):
    """
    Measure the performance of a query.
    
    Args:
        connector: Database connector
        query: SQL query to execute
        iterations: Number of times to execute the query
    
    Returns:
        dict: Performance metrics
    """
    execution_times = []
    row_counts = []
    memory_usages = []
    
    for i in range(iterations):
        start_time = time.time()
        start_memory = get_process_memory()
        
        result = await connector.execute_query(query)
        
        end_time = time.time()
        end_memory = get_process_memory()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        memory_usage = end_memory - start_memory
        
        execution_times.append(execution_time)
        row_counts.append(len(result["rows"]) if "rows" in result else 0)
        memory_usages.append(memory_usage)
    
    return {
        "execution_times": execution_times,
        "avg_execution_time": statistics.mean(execution_times),
        "median_execution_time": statistics.median(execution_times),
        "min_execution_time": min(execution_times),
        "max_execution_time": max(execution_times),
        "std_dev_execution_time": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
        "avg_row_count": statistics.mean(row_counts),
        "avg_memory_usage": statistics.mean(memory_usages),
        "max_memory_usage": max(memory_usages)
    }


def get_process_memory():
    """
    Get the current memory usage of the process.
    
    Returns:
        float: Memory usage in bytes
    """
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


async def test_mssql_performance():
    """
    Test MS-SQL connector performance.
    """
    print("Testing MS-SQL connector performance...")
    
    # Create MS-SQL connector
    connector = MSSQLConnector(
        host=settings.TEST_MSSQL_HOST,
        port=settings.TEST_MSSQL_PORT,
        username=settings.TEST_MSSQL_USER,
        password=settings.TEST_MSSQL_PASSWORD,
        database=settings.TEST_MSSQL_DB
    )
    
    # Connect to database
    await connector.connect()
    
    try:
        # Test simple query
        print("Testing simple query performance...")
        simple_metrics = await measure_query_performance(connector, TEST_QUERIES["simple"], iterations=20)
        
        # Test medium query
        print("Testing medium query performance...")
        medium_metrics = await measure_query_performance(connector, TEST_QUERIES["medium"], iterations=15)
        
        # Test complex query
        print("Testing complex query performance...")
        complex_metrics = await measure_query_performance(connector, TEST_QUERIES["complex"], iterations=10)
        
        # Generate performance report
        generate_performance_report("mssql", {
            "simple": simple_metrics,
            "medium": medium_metrics,
            "complex": complex_metrics
        })
        
        return {
            "simple": simple_metrics,
            "medium": medium_metrics,
            "complex": complex_metrics
        }
    finally:
        # Disconnect from database
        await connector.disconnect()


async def test_hana_performance():
    """
    Test SAP HANA connector performance.
    """
    print("Testing SAP HANA connector performance...")
    
    # Create HANA connector
    connector = HanaConnector(
        host=settings.TEST_HANA_HOST,
        port=settings.TEST_HANA_PORT,
        username=settings.TEST_HANA_USER,
        password=settings.TEST_HANA_PASSWORD,
        database=settings.TEST_HANA_DB
    )
    
    # Connect to database
    await connector.connect()
    
    try:
        # Test simple query
        print("Testing simple query performance...")
        simple_metrics = await measure_query_performance(connector, TEST_QUERIES["simple"], iterations=20)
        
        # Test medium query
        print("Testing medium query performance...")
        medium_metrics = await measure_query_performance(connector, TEST_QUERIES["medium"], iterations=15)
        
        # Test complex query
        print("Testing complex query performance...")
        complex_metrics = await measure_query_performance(connector, TEST_QUERIES["complex"], iterations=10)
        
        # Generate performance report
        generate_performance_report("hana", {
            "simple": simple_metrics,
            "medium": medium_metrics,
            "complex": complex_metrics
        })
        
        return {
            "simple": simple_metrics,
            "medium": medium_metrics,
            "complex": complex_metrics
        }
    finally:
        # Disconnect from database
        await connector.disconnect()


async def test_connection_pool_performance():
    """
    Test database connection pool performance.
    """
    print("Testing connection pool performance...")
    
    # Create MS-SQL connector with connection pool
    connector = MSSQLConnector(
        host=settings.TEST_MSSQL_HOST,
        port=settings.TEST_MSSQL_PORT,
        username=settings.TEST_MSSQL_USER,
        password=settings.TEST_MSSQL_PASSWORD,
        database=settings.TEST_MSSQL_DB,
        pool_size=10
    )
    
    # Connect to database
    await connector.connect()
    
    try:
        # Test concurrent query execution
        print("Testing concurrent query execution...")
        
        async def execute_query():
            start_time = time.time()
            await connector.execute_query(TEST_QUERIES["simple"])
            return time.time() - start_time
        
        # Execute 50 concurrent queries
        tasks = [execute_query() for _ in range(50)]
        execution_times = await asyncio.gather(*tasks)
        
        # Calculate metrics
        avg_time = statistics.mean(execution_times) * 1000  # Convert to milliseconds
        median_time = statistics.median(execution_times) * 1000
        max_time = max(execution_times) * 1000
        min_time = min(execution_times) * 1000
        
        print(f"Concurrent query execution metrics:")
        print(f"  Average time: {avg_time:.2f} ms")
        print(f"  Median time: {median_time:.2f} ms")
        print(f"  Min time: {min_time:.2f} ms")
        print(f"  Max time: {max_time:.2f} ms")
        
        # Generate performance report
        generate_connection_pool_report({
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "execution_times": [t * 1000 for t in execution_times]
        })
        
        return {
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "execution_times": execution_times
        }
    finally:
        # Disconnect from database
        await connector.disconnect()


def generate_performance_report(db_type, metrics):
    """
    Generate a performance report for database queries.
    
    Args:
        db_type: Database type (mssql or hana)
        metrics: Performance metrics
    """
    from datetime import datetime
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"{db_type}_performance_{timestamp}.txt", "w") as f:
        f.write(f"{db_type.upper()} Performance Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        for query_type, query_metrics in metrics.items():
            f.write(f"{query_type.capitalize()} Query Performance:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Average Execution Time: {query_metrics['avg_execution_time']:.2f} ms\n")
            f.write(f"Median Execution Time: {query_metrics['median_execution_time']:.2f} ms\n")
            f.write(f"Min Execution Time: {query_metrics['min_execution_time']:.2f} ms\n")
            f.write(f"Max Execution Time: {query_metrics['max_execution_time']:.2f} ms\n")
            f.write(f"Standard Deviation: {query_metrics['std_dev_execution_time']:.2f} ms\n")
            f.write(f"Average Row Count: {query_metrics['avg_row_count']:.2f}\n")
            f.write(f"Average Memory Usage: {query_metrics['avg_memory_usage'] / 1024:.2f} KB\n")
            f.write(f"Max Memory Usage: {query_metrics['max_memory_usage'] / 1024:.2f} KB\n\n")
    
    # Generate performance charts
    plt.figure(figsize=(12, 8))
    
    # Query execution time comparison
    plt.subplot(2, 1, 1)
    query_types = list(metrics.keys())
    avg_times = [metrics[qt]["avg_execution_time"] for qt in query_types]
    std_devs = [metrics[qt]["std_dev_execution_time"] for qt in query_types]
    
    x = np.arange(len(query_types))
    plt.bar(x, avg_times, yerr=std_devs, align='center', alpha=0.7, ecolor='black', capsize=10)
    plt.ylabel('Execution Time (ms)')
    plt.title(f'{db_type.upper()} Query Execution Time')
    plt.xticks(x, [qt.capitalize() for qt in query_types])
    
    # Memory usage comparison
    plt.subplot(2, 1, 2)
    memory_usage = [metrics[qt]["avg_memory_usage"] / 1024 for qt in query_types]  # Convert to KB
    
    plt.bar(x, memory_usage, align='center', alpha=0.7)
    plt.ylabel('Memory Usage (KB)')
    plt.title(f'{db_type.upper()} Query Memory Usage')
    plt.xticks(x, [qt.capitalize() for qt in query_types])
    
    plt.tight_layout()
    plt.savefig(results_dir / f"{db_type}_performance_{timestamp}.png")
    
    print(f"{db_type.upper()} performance report saved to {results_dir}")


def generate_connection_pool_report(metrics):
    """
    Generate a report for connection pool performance.
    
    Args:
        metrics: Performance metrics
    """
    from datetime import datetime
    
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"connection_pool_performance_{timestamp}.txt", "w") as f:
        f.write(f"Connection Pool Performance Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Average Execution Time: {metrics['avg_time']:.2f} ms\n")
        f.write(f"Median Execution Time: {metrics['median_time']:.2f} ms\n")
        f.write(f"Min Execution Time: {metrics['min_time']:.2f} ms\n")
        f.write(f"Max Execution Time: {metrics['max_time']:.2f} ms\n")
    
    # Generate histogram of execution times
    plt.figure(figsize=(10, 6))
    plt.hist(metrics['execution_times'], bins=20, alpha=0.7)
    plt.xlabel('Execution Time (ms)')
    plt.ylabel('Frequency')
    plt.title('Connection Pool Query Execution Time Distribution')
    plt.grid(True, alpha=0.3)
    plt.savefig(results_dir / f"connection_pool_performance_{timestamp}.png")
    
    print(f"Connection pool performance report saved to {results_dir}")


async def main():
    """
    Run all database performance tests.
    """
    try:
        # Test MS-SQL performance
        mssql_metrics = await test_mssql_performance()
        
        # Test SAP HANA performance (if available)
        try:
            hana_metrics = await test_hana_performance()
        except Exception as e:
            print(f"SAP HANA performance test failed: {e}")
        
        # Test connection pool performance
        pool_metrics = await test_connection_pool_performance()
        
        print("All database performance tests completed.")
    except Exception as e:
        print(f"Error running database performance tests: {e}")


if __name__ == "__main__":
    asyncio.run(main())