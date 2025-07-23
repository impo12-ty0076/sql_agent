"""
API performance tests for the SQL DB LLM Agent system.
"""
import time
import asyncio
import statistics
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import json
import aiohttp
import random
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import TEST_USER, TEST_QUERIES, NL_TEST_QUERIES, RESULTS_DIR


async def measure_api_performance(session, method, url, headers=None, json_data=None, iterations=10):
    """
    Measure the performance of an API endpoint.
    
    Args:
        session: aiohttp ClientSession
        method: HTTP method (get, post, etc.)
        url: API endpoint URL
        headers: Request headers
        json_data: Request JSON data
        iterations: Number of times to call the API
    
    Returns:
        dict: Performance metrics
    """
    response_times = []
    status_codes = []
    
    for i in range(iterations):
        start_time = time.time()
        
        if method.lower() == "get":
            async with session.get(url, headers=headers) as response:
                await response.text()
                status_codes.append(response.status)
        elif method.lower() == "post":
            async with session.post(url, headers=headers, json=json_data) as response:
                await response.text()
                status_codes.append(response.status)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        response_times.append(response_time)
    
    return {
        "response_times": response_times,
        "avg_response_time": statistics.mean(response_times),
        "median_response_time": statistics.median(response_times),
        "min_response_time": min(response_times),
        "max_response_time": max(response_times),
        "std_dev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
        "success_rate": sum(1 for code in status_codes if 200 <= code < 300) / len(status_codes) * 100
    }


async def test_api_endpoints():
    """
    Test the performance of key API endpoints.
    """
    print("Testing API endpoint performance...")
    
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
        
        # Test endpoints
        endpoints = {
            "db_list": {
                "method": "get",
                "url": f"{base_url}/api/db/list",
                "headers": headers,
                "iterations": 20
            },
            "db_schema": {
                "method": "get",
                "url": f"{base_url}/api/db/schema/{db_id}",
                "headers": headers,
                "iterations": 15
            },
            "simple_query": {
                "method": "post",
                "url": f"{base_url}/api/query/execute",
                "headers": headers,
                "json_data": {
                    "database_id": db_id,
                    "sql": TEST_QUERIES["simple"]
                },
                "iterations": 10
            },
            "medium_query": {
                "method": "post",
                "url": f"{base_url}/api/query/execute",
                "headers": headers,
                "json_data": {
                    "database_id": db_id,
                    "sql": TEST_QUERIES["medium"]
                },
                "iterations": 8
            },
            "nl_query": {
                "method": "post",
                "url": f"{base_url}/api/query/natural",
                "headers": headers,
                "json_data": {
                    "database_id": db_id,
                    "query": random.choice(NL_TEST_QUERIES)
                },
                "iterations": 5
            },
            "history": {
                "method": "get",
                "url": f"{base_url}/api/history",
                "headers": headers,
                "iterations": 15
            }
        }
        
        results = {}
        
        for name, config in endpoints.items():
            print(f"Testing {name} endpoint...")
            results[name] = await measure_api_performance(
                session,
                config["method"],
                config["url"],
                config.get("headers"),
                config.get("json_data"),
                config.get("iterations", 10)
            )
        
        # Generate performance report
        generate_api_performance_report(results)
        
        return results


def generate_api_performance_report(metrics):
    """
    Generate a performance report for API endpoints.
    
    Args:
        metrics: Performance metrics
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"api_performance_{timestamp}.txt", "w") as f:
        f.write(f"API Performance Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        for endpoint, endpoint_metrics in metrics.items():
            f.write(f"{endpoint} Endpoint Performance:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Average Response Time: {endpoint_metrics['avg_response_time']:.2f} ms\n")
            f.write(f"Median Response Time: {endpoint_metrics['median_response_time']:.2f} ms\n")
            f.write(f"Min Response Time: {endpoint_metrics['min_response_time']:.2f} ms\n")
            f.write(f"Max Response Time: {endpoint_metrics['max_response_time']:.2f} ms\n")
            f.write(f"Standard Deviation: {endpoint_metrics['std_dev_response_time']:.2f} ms\n")
            f.write(f"Success Rate: {endpoint_metrics['success_rate']:.2f}%\n\n")
    
    # Write raw metrics to JSON file
    with open(results_dir / f"api_performance_raw_{timestamp}.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Generate performance charts
    plt.figure(figsize=(12, 8))
    
    # Response time comparison
    plt.subplot(2, 1, 1)
    endpoints = list(metrics.keys())
    avg_times = [metrics[ep]["avg_response_time"] for ep in endpoints]
    std_devs = [metrics[ep]["std_dev_response_time"] for ep in endpoints]
    
    x = np.arange(len(endpoints))
    plt.bar(x, avg_times, yerr=std_devs, align='center', alpha=0.7, ecolor='black', capsize=10)
    plt.ylabel('Response Time (ms)')
    plt.title('API Endpoint Response Time')
    plt.xticks(x, endpoints, rotation=45, ha='right')
    
    # Success rate comparison
    plt.subplot(2, 1, 2)
    success_rates = [metrics[ep]["success_rate"] for ep in endpoints]
    
    plt.bar(x, success_rates, align='center', alpha=0.7)
    plt.ylabel('Success Rate (%)')
    plt.title('API Endpoint Success Rate')
    plt.xticks(x, endpoints, rotation=45, ha='right')
    plt.ylim(0, 105)  # Set y-axis limit to 0-105%
    
    plt.tight_layout()
    plt.savefig(results_dir / f"api_performance_{timestamp}.png")
    
    print(f"API performance report saved to {results_dir}")


async def test_concurrent_api_calls():
    """
    Test the performance of concurrent API calls.
    """
    print("Testing concurrent API calls...")
    
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
        
        # Test concurrent simple queries
        print("Testing concurrent simple queries...")
        
        async def execute_simple_query():
            start_time = time.time()
            async with session.post(
                f"{base_url}/api/query/execute",
                headers=headers,
                json={
                    "database_id": db_id,
                    "sql": TEST_QUERIES["simple"]
                }
            ) as response:
                await response.text()
                return time.time() - start_time, response.status
        
        # Execute 20 concurrent queries
        tasks = [execute_simple_query() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        execution_times = [r[0] * 1000 for r in results]  # Convert to milliseconds
        status_codes = [r[1] for r in results]
        
        # Calculate metrics
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        success_rate = sum(1 for code in status_codes if 200 <= code < 300) / len(status_codes) * 100
        
        print(f"Concurrent query execution metrics:")
        print(f"  Average time: {avg_time:.2f} ms")
        print(f"  Median time: {median_time:.2f} ms")
        print(f"  Min time: {min_time:.2f} ms")
        print(f"  Max time: {max_time:.2f} ms")
        print(f"  Success rate: {success_rate:.2f}%")
        
        # Generate performance report
        generate_concurrent_api_report({
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "execution_times": execution_times,
            "success_rate": success_rate
        })
        
        return {
            "avg_time": avg_time,
            "median_time": median_time,
            "max_time": max_time,
            "min_time": min_time,
            "execution_times": execution_times,
            "success_rate": success_rate
        }


def generate_concurrent_api_report(metrics):
    """
    Generate a report for concurrent API calls.
    
    Args:
        metrics: Performance metrics
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    with open(results_dir / f"concurrent_api_performance_{timestamp}.txt", "w") as f:
        f.write(f"Concurrent API Calls Performance Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Average Response Time: {metrics['avg_time']:.2f} ms\n")
        f.write(f"Median Response Time: {metrics['median_time']:.2f} ms\n")
        f.write(f"Min Response Time: {metrics['min_time']:.2f} ms\n")
        f.write(f"Max Response Time: {metrics['max_time']:.2f} ms\n")
        f.write(f"Success Rate: {metrics['success_rate']:.2f}%\n")
    
    # Generate histogram of response times
    plt.figure(figsize=(10, 6))
    plt.hist(metrics['execution_times'], bins=20, alpha=0.7)
    plt.xlabel('Response Time (ms)')
    plt.ylabel('Frequency')
    plt.title('Concurrent API Calls Response Time Distribution')
    plt.grid(True, alpha=0.3)
    plt.savefig(results_dir / f"concurrent_api_performance_{timestamp}.png")
    
    print(f"Concurrent API calls performance report saved to {results_dir}")


async def main():
    """
    Run all API performance tests.
    """
    try:
        # Test API endpoints
        api_metrics = await test_api_endpoints()
        
        # Test concurrent API calls
        concurrent_metrics = await test_concurrent_api_calls()
        
        print("All API performance tests completed.")
    except Exception as e:
        print(f"Error running API performance tests: {e}")


if __name__ == "__main__":
    asyncio.run(main())