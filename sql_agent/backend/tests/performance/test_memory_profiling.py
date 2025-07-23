"""
Memory profiling and leak detection for the SQL DB LLM Agent system.
"""
import time
import asyncio
import gc
import os
import sys
import tracemalloc
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import psutil
import aiohttp
import random

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import TEST_USER, TEST_QUERIES, NL_TEST_QUERIES, RESULTS_DIR


async def profile_memory_usage(session, base_url, headers, db_id, iterations=50):
    """
    Profile memory usage during repeated API calls.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
        headers: Request headers
        db_id: Database ID
        iterations: Number of iterations
    
    Returns:
        dict: Memory usage metrics
    """
    # Start memory tracking
    tracemalloc.start()
    process = psutil.Process(os.getpid())
    
    # Initial memory snapshot
    initial_snapshot = tracemalloc.take_snapshot()
    initial_memory = process.memory_info().rss
    
    memory_usage = [0]  # First point is 0 (baseline)
    snapshots = [initial_snapshot]
    
    print(f"Initial memory usage: {initial_memory / (1024 * 1024):.2f} MB")
    
    # Perform repeated API calls
    for i in range(iterations):
        # Alternate between different API calls
        if i % 3 == 0:
            # Execute simple query
            async with session.post(
                f"{base_url}/api/query/execute",
                headers=headers,
                json={
                    "database_id": db_id,
                    "sql": TEST_QUERIES["simple"]
                }
            ) as response:
                await response.text()
        elif i % 3 == 1:
            # Execute medium query
            async with session.post(
                f"{base_url}/api/query/execute",
                headers=headers,
                json={
                    "database_id": db_id,
                    "sql": TEST_QUERIES["medium"]
                }
            ) as response:
                await response.text()
        else:
            # Submit natural language query
            async with session.post(
                f"{base_url}/api/query/natural",
                headers=headers,
                json={
                    "database_id": db_id,
                    "query": random.choice(NL_TEST_QUERIES)
                }
            ) as response:
                await response.text()
        
        # Force garbage collection
        if i % 10 == 9:
            gc.collect()
        
        # Take memory snapshot
        current_memory = process.memory_info().rss
        memory_diff = current_memory - initial_memory
        memory_usage.append(memory_diff / (1024 * 1024))  # Convert to MB
        
        if i % 10 == 9:
            snapshot = tracemalloc.take_snapshot()
            snapshots.append(snapshot)
            print(f"Iteration {i+1}/{iterations}: Memory usage: {memory_diff / (1024 * 1024):.2f} MB")
    
    # Final memory snapshot
    final_snapshot = tracemalloc.take_snapshot()
    final_memory = process.memory_info().rss
    memory_diff = final_memory - initial_memory
    
    print(f"Final memory usage: {final_memory / (1024 * 1024):.2f} MB")
    print(f"Memory difference: {memory_diff / (1024 * 1024):.2f} MB")
    
    # Stop memory tracking
    tracemalloc.stop()
    
    # Analyze memory usage
    top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
    
    # Generate memory profile report
    generate_memory_profile_report(memory_usage, top_stats[:20])
    
    return {
        "initial_memory": initial_memory,
        "final_memory": final_memory,
        "memory_diff": memory_diff,
        "memory_usage": memory_usage,
        "top_stats": [(stat.traceback, stat.size) for stat in top_stats[:20]]
    }


def generate_memory_profile_report(memory_usage, top_stats):
    """
    Generate a memory profile report.
    
    Args:
        memory_usage: Memory usage over time
        top_stats: Top memory allocations
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"memory_profile_{timestamp}.txt", "w") as f:
        f.write(f"Memory Profile Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Memory Usage Over Time:\n")
        f.write("-" * 30 + "\n")
        for i, usage in enumerate(memory_usage):
            f.write(f"Iteration {i}: {usage:.2f} MB\n")
        
        f.write("\nTop Memory Allocations:\n")
        f.write("-" * 30 + "\n")
        for i, (traceback, size) in enumerate(top_stats):
            f.write(f"{i+1}. Size: {size / 1024:.2f} KB\n")
            for frame in traceback:
                f.write(f"   {frame.filename}:{frame.lineno}: {frame.name}\n")
            f.write("\n")
    
    # Generate memory usage chart
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(memory_usage)), memory_usage, marker='o', linestyle='-', alpha=0.7)
    plt.xlabel('Iteration')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage Over Time')
    plt.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(range(len(memory_usage)), memory_usage, 1)
    p = np.poly1d(z)
    plt.plot(range(len(memory_usage)), p(range(len(memory_usage))), "r--", alpha=0.7)
    
    plt.savefig(results_dir / f"memory_profile_{timestamp}.png")
    
    print(f"Memory profile report saved to {results_dir}")


async def detect_memory_leaks():
    """
    Detect potential memory leaks in the system.
    """
    print("Detecting potential memory leaks...")
    
    # API base URL
    base_url = "http://localhost:8000"
    
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
        
        # Profile memory usage
        memory_metrics = await profile_memory_usage(session, base_url, headers, db_id)
        
        # Analyze for potential leaks
        memory_diff = memory_metrics["memory_diff"]
        memory_usage = memory_metrics["memory_usage"]
        
        # Check if memory usage is consistently increasing
        is_leaking = memory_diff > 5 * 1024 * 1024  # More than 5 MB increase
        
        if is_leaking:
            print("Potential memory leak detected!")
            print(f"Memory increased by {memory_diff / (1024 * 1024):.2f} MB over {len(memory_usage)} iterations")
            print("Top memory allocations:")
            for i, (traceback, size) in enumerate(memory_metrics["top_stats"][:5]):
                print(f"{i+1}. Size: {size / 1024:.2f} KB")
                for frame in traceback:
                    print(f"   {frame.filename}:{frame.lineno}: {frame.name}")
        else:
            print("No significant memory leaks detected.")
        
        return {
            "is_leaking": is_leaking,
            "memory_diff": memory_diff,
            "top_allocations": memory_metrics["top_stats"][:5]
        }


async def profile_large_result_memory_usage(session, base_url, headers, db_id):
    """
    Profile memory usage when handling large query results.
    
    Args:
        session: aiohttp ClientSession
        base_url: API base URL
        headers: Request headers
        db_id: Database ID
    
    Returns:
        dict: Memory usage metrics
    """
    print("Profiling memory usage for large query results...")
    
    # Start memory tracking
    tracemalloc.start()
    process = psutil.Process(os.getpid())
    
    # Initial memory snapshot
    initial_snapshot = tracemalloc.take_snapshot()
    initial_memory = process.memory_info().rss
    
    print(f"Initial memory usage: {initial_memory / (1024 * 1024):.2f} MB")
    
    # Execute a query that returns a large result set
    # This is a simulated large result query - in a real test, you'd use a query that actually returns many rows
    large_query = "SELECT * FROM dbo.employees CROSS JOIN dbo.departments"
    
    async with session.post(
        f"{base_url}/api/query/execute",
        headers=headers,
        json={
            "database_id": db_id,
            "sql": large_query
        }
    ) as response:
        result_data = await response.json()
    
    # Check memory after query execution
    post_query_memory = process.memory_info().rss
    post_query_diff = post_query_memory - initial_memory
    
    print(f"Memory after query execution: {post_query_memory / (1024 * 1024):.2f} MB")
    print(f"Memory difference: {post_query_diff / (1024 * 1024):.2f} MB")
    
    # If result_id is available, get the result
    if "result_id" in result_data:
        result_id = result_data["result_id"]
        
        async with session.get(
            f"{base_url}/api/result/{result_id}",
            headers=headers
        ) as response:
            await response.json()
        
        # Check memory after result retrieval
        post_result_memory = process.memory_info().rss
        post_result_diff = post_result_memory - post_query_memory
        
        print(f"Memory after result retrieval: {post_result_memory / (1024 * 1024):.2f} MB")
        print(f"Memory difference: {post_result_diff / (1024 * 1024):.2f} MB")
    
    # Force garbage collection
    gc.collect()
    
    # Final memory snapshot
    final_snapshot = tracemalloc.take_snapshot()
    final_memory = process.memory_info().rss
    final_diff = final_memory - initial_memory
    
    print(f"Final memory usage: {final_memory / (1024 * 1024):.2f} MB")
    print(f"Total memory difference: {final_diff / (1024 * 1024):.2f} MB")
    
    # Stop memory tracking
    tracemalloc.stop()
    
    # Analyze memory usage
    top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
    
    # Generate memory profile report
    generate_large_result_memory_report({
        "initial_memory": initial_memory,
        "post_query_memory": post_query_memory,
        "post_query_diff": post_query_diff,
        "final_memory": final_memory,
        "final_diff": final_diff,
        "top_stats": [(stat.traceback, stat.size) for stat in top_stats[:20]]
    })
    
    return {
        "initial_memory": initial_memory,
        "post_query_memory": post_query_memory,
        "post_query_diff": post_query_diff,
        "final_memory": final_memory,
        "final_diff": final_diff,
        "top_stats": [(stat.traceback, stat.size) for stat in top_stats[:20]]
    }


def generate_large_result_memory_report(metrics):
    """
    Generate a memory profile report for large query results.
    
    Args:
        metrics: Memory usage metrics
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"large_result_memory_{timestamp}.txt", "w") as f:
        f.write(f"Large Result Memory Profile Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Memory Usage:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Initial Memory: {metrics['initial_memory'] / (1024 * 1024):.2f} MB\n")
        f.write(f"Memory After Query Execution: {metrics['post_query_memory'] / (1024 * 1024):.2f} MB\n")
        f.write(f"Query Execution Memory Difference: {metrics['post_query_diff'] / (1024 * 1024):.2f} MB\n")
        f.write(f"Final Memory: {metrics['final_memory'] / (1024 * 1024):.2f} MB\n")
        f.write(f"Total Memory Difference: {metrics['final_diff'] / (1024 * 1024):.2f} MB\n\n")
        
        f.write("Top Memory Allocations:\n")
        f.write("-" * 30 + "\n")
        for i, (traceback, size) in enumerate(metrics["top_stats"]):
            f.write(f"{i+1}. Size: {size / 1024:.2f} KB\n")
            for frame in traceback:
                f.write(f"   {frame.filename}:{frame.lineno}: {frame.name}\n")
            f.write("\n")
    
    # Generate memory usage chart
    plt.figure(figsize=(10, 6))
    
    # Create bar chart of memory usage
    stages = ['Initial', 'After Query', 'Final']
    memory_values = [
        metrics['initial_memory'] / (1024 * 1024),
        metrics['post_query_memory'] / (1024 * 1024),
        metrics['final_memory'] / (1024 * 1024)
    ]
    
    plt.bar(stages, memory_values, alpha=0.7)
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage for Large Query Results')
    
    # Add memory difference annotations
    plt.annotate(
        f"+{metrics['post_query_diff'] / (1024 * 1024):.2f} MB",
        xy=(1, memory_values[1]),
        xytext=(1, memory_values[1] + 2),
        ha='center',
        va='bottom',
        arrowprops=dict(arrowstyle='->', lw=1.5)
    )
    
    plt.annotate(
        f"{(metrics['final_memory'] - metrics['post_query_memory']) / (1024 * 1024):.2f} MB",
        xy=(2, memory_values[2]),
        xytext=(2, memory_values[2] + 2),
        ha='center',
        va='bottom',
        arrowprops=dict(arrowstyle='->', lw=1.5)
    )
    
    plt.savefig(results_dir / f"large_result_memory_{timestamp}.png")
    
    print(f"Large result memory profile report saved to {results_dir}")


async def main():
    """
    Run all memory profiling tests.
    """
    try:
        # API base URL
        base_url = "http://localhost:8000"
        
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
            
            # Detect memory leaks
            leak_results = await detect_memory_leaks()
            
            # Profile large result memory usage
            large_result_metrics = await profile_large_result_memory_usage(session, base_url, headers, db_id)
            
            print("All memory profiling tests completed.")
    except Exception as e:
        print(f"Error running memory profiling tests: {e}")


if __name__ == "__main__":
    asyncio.run(main())