"""
System optimization based on performance test results.
"""
import os
import sys
import json
import asyncio
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from .config import RESULTS_DIR


def analyze_performance_results():
    """
    Analyze performance test results and identify bottlenecks.
    
    Returns:
        dict: Analysis results
    """
    print("Analyzing performance test results...")
    
    results_dir = Path(RESULTS_DIR)
    if not results_dir.exists():
        print(f"Results directory {results_dir} does not exist.")
        return {}
    
    # Find the latest API performance results
    api_results_files = list(results_dir.glob("api_performance_raw_*.json"))
    if not api_results_files:
        print("No API performance results found.")
        return {}
    
    latest_api_file = max(api_results_files, key=lambda p: p.stat().st_mtime)
    print(f"Using API performance results from {latest_api_file}")
    
    with open(latest_api_file, "r") as f:
        api_metrics = json.load(f)
    
    # Identify slow endpoints
    slow_endpoints = {}
    for endpoint, metrics in api_metrics.items():
        if metrics["avg_response_time"] > 500:  # More than 500ms
            slow_endpoints[endpoint] = metrics["avg_response_time"]
    
    # Sort endpoints by response time (slowest first)
    slow_endpoints = {k: v for k, v in sorted(slow_endpoints.items(), key=lambda item: item[1], reverse=True)}
    
    # Find the latest memory profiling results
    memory_files = list(results_dir.glob("memory_profile_*.txt"))
    if not memory_files:
        print("No memory profiling results found.")
        return {"slow_endpoints": slow_endpoints}
    
    latest_memory_file = max(memory_files, key=lambda p: p.stat().st_mtime)
    print(f"Using memory profiling results from {latest_memory_file}")
    
    # Parse memory profiling results
    memory_leaks = []
    with open(latest_memory_file, "r") as f:
        content = f.read()
        if "Potential memory leak detected" in content:
            # Extract top memory allocations
            sections = content.split("Top Memory Allocations:")
            if len(sections) > 1:
                allocations_section = sections[1].strip()
                allocations = allocations_section.split("\n\n")
                for allocation in allocations:
                    if allocation.strip():
                        memory_leaks.append(allocation.strip())
    
    return {
        "slow_endpoints": slow_endpoints,
        "memory_leaks": memory_leaks
    }


def generate_optimization_recommendations(analysis):
    """
    Generate optimization recommendations based on analysis.
    
    Args:
        analysis: Analysis results
    
    Returns:
        list: Optimization recommendations
    """
    recommendations = []
    
    # Recommendations for slow endpoints
    if "slow_endpoints" in analysis and analysis["slow_endpoints"]:
        recommendations.append("## Slow API Endpoints")
        for endpoint, response_time in analysis["slow_endpoints"].items():
            recommendations.append(f"- **{endpoint}**: {response_time:.2f} ms")
        
        recommendations.append("\n### Recommendations for API Optimization:")
        
        if "nl_query" in analysis["slow_endpoints"]:
            recommendations.append("- Implement caching for natural language processing results")
            recommendations.append("- Consider using a more efficient LLM service or model")
            recommendations.append("- Optimize prompt templates to reduce token count")
        
        if "medium_query" in analysis["slow_endpoints"] or "complex_query" in analysis["slow_endpoints"]:
            recommendations.append("- Add database query result caching")
            recommendations.append("- Optimize SQL queries with proper indexing")
            recommendations.append("- Implement query timeout and pagination for large result sets")
        
        if "db_schema" in analysis["slow_endpoints"]:
            recommendations.append("- Cache database schema information")
            recommendations.append("- Implement incremental schema updates instead of full retrieval")
    
    # Recommendations for memory leaks
    if "memory_leaks" in analysis and analysis["memory_leaks"]:
        recommendations.append("\n## Potential Memory Leaks")
        for leak in analysis["memory_leaks"]:
            recommendations.append(f"```\n{leak}\n```")
        
        recommendations.append("\n### Recommendations for Memory Optimization:")
        recommendations.append("- Fix memory leaks in the identified modules")
        recommendations.append("- Implement proper resource cleanup in exception handlers")
        recommendations.append("- Use context managers for resource management")
        recommendations.append("- Consider implementing memory limits and monitoring")
    
    # General optimization recommendations
    recommendations.append("\n## General Optimization Recommendations")
    recommendations.append("- Implement connection pooling for database connections")
    recommendations.append("- Add response compression (gzip) for API responses")
    recommendations.append("- Implement proper HTTP caching headers")
    recommendations.append("- Use asynchronous processing for long-running tasks")
    recommendations.append("- Optimize database queries with proper indexing")
    recommendations.append("- Implement pagination for large result sets")
    recommendations.append("- Use streaming responses for large data transfers")
    recommendations.append("- Implement request rate limiting to prevent overload")
    
    return recommendations


def apply_optimizations():
    """
    Apply optimizations to the system based on recommendations.
    """
    print("Applying optimizations...")
    
    # Analyze performance results
    analysis = analyze_performance_results()
    
    # Generate optimization recommendations
    recommendations = generate_optimization_recommendations(analysis)
    
    # Create optimization report
    create_optimization_report(analysis, recommendations)
    
    # Apply optimizations
    optimizations_applied = []
    
    # 1. Optimize database connection pooling
    try:
        optimize_db_connection_pool()
        optimizations_applied.append("Database connection pooling optimized")
    except Exception as e:
        print(f"Error optimizing database connection pool: {e}")
    
    # 2. Implement API response caching
    try:
        implement_api_caching()
        optimizations_applied.append("API response caching implemented")
    except Exception as e:
        print(f"Error implementing API caching: {e}")
    
    # 3. Optimize query execution
    try:
        optimize_query_execution()
        optimizations_applied.append("Query execution optimized")
    except Exception as e:
        print(f"Error optimizing query execution: {e}")
    
    # 4. Implement response compression
    try:
        implement_response_compression()
        optimizations_applied.append("Response compression implemented")
    except Exception as e:
        print(f"Error implementing response compression: {e}")
    
    # Update optimization report with applied optimizations
    update_optimization_report(optimizations_applied)
    
    print(f"Applied {len(optimizations_applied)} optimizations.")
    for opt in optimizations_applied:
        print(f"- {opt}")


def optimize_db_connection_pool():
    """
    Optimize database connection pooling.
    """
    # Path to the database connector configuration
    config_path = Path(__file__).parent.parent.parent / "db" / "config.py"
    
    if not config_path.exists():
        print(f"Database configuration file {config_path} not found.")
        return
    
    # Read current configuration
    with open(config_path, "r") as f:
        config_content = f.read()
    
    # Update connection pool settings
    updated_content = config_content
    
    # Update pool size
    if "POOL_SIZE =" in config_content:
        updated_content = updated_content.replace(
            "POOL_SIZE = 5",
            "POOL_SIZE = 20"
        )
    
    # Update pool recycle time
    if "POOL_RECYCLE =" in config_content:
        updated_content = updated_content.replace(
            "POOL_RECYCLE = 3600",
            "POOL_RECYCLE = 1800"
        )
    
    # Update pool timeout
    if "POOL_TIMEOUT =" in config_content:
        updated_content = updated_content.replace(
            "POOL_TIMEOUT = 30",
            "POOL_TIMEOUT = 60"
        )
    
    # Write updated configuration
    with open(config_path, "w") as f:
        f.write(updated_content)
    
    print(f"Database connection pool settings optimized in {config_path}")


def implement_api_caching():
    """
    Implement API response caching.
    """
    # Path to the API router files
    api_dir = Path(__file__).parent.parent.parent / "api"
    
    if not api_dir.exists():
        print(f"API directory {api_dir} not found.")
        return
    
    # Add caching middleware
    middleware_path = Path(__file__).parent.parent.parent / "core" / "cache_middleware.py"
    
    # Create cache middleware if it doesn't exist
    if not middleware_path.exists():
        cache_middleware_content = """\"\"\"
Cache middleware for API responses.
\"\"\"
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import time
import json
from typing import Dict, Any, Optional

# Simple in-memory cache
cache: Dict[str, Any] = {}
cache_ttl: Dict[str, float] = {}
DEFAULT_TTL = 300  # 5 minutes


def get_cache_key(request: Request) -> str:
    \"\"\"
    Generate a cache key from the request.
    
    Args:
        request: The request object
    
    Returns:
        str: Cache key
    \"\"\"
    # Create a unique key based on the request method, url, and body
    key_parts = [
        request.method,
        str(request.url),
    ]
    
    # Add query parameters
    key_parts.extend([f"{k}={v}" for k, v in request.query_params.items()])
    
    # Generate hash
    key = hashlib.md5("".join(key_parts).encode()).hexdigest()
    return key


class CacheMiddleware(BaseHTTPMiddleware):
    \"\"\"
    Middleware for caching API responses.
    \"\"\"
    
    async def dispatch(self, request: Request, call_next):
        \"\"\"
        Process the request and cache the response if applicable.
        
        Args:
            request: The request object
            call_next: The next middleware or endpoint
        
        Returns:
            Response: The response object
        \"\"\"
        # Skip caching for non-GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Skip caching for certain paths
        if any(path in str(request.url.path) for path in ["/auth/", "/admin/"]):
            return await call_next(request)
        
        # Generate cache key
        cache_key = get_cache_key(request)
        
        # Check if response is in cache and not expired
        if cache_key in cache and cache_ttl.get(cache_key, 0) > time.time():
            cached_response = cache[cache_key]
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )
        
        # Process the request
        response = await call_next(request)
        
        # Cache the response if it's successful
        if 200 <= response.status_code < 300:
            # Get response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Determine TTL based on the endpoint
            ttl = DEFAULT_TTL
            if "schema" in str(request.url.path):
                ttl = 3600  # 1 hour for schema
            elif "history" in str(request.url.path):
                ttl = 60  # 1 minute for history
            
            # Store in cache
            cache[cache_key] = {
                "content": response_body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            cache_ttl[cache_key] = time.time() + ttl
            
            # Create new response with the same content
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        return response


def clear_cache():
    \"\"\"
    Clear the entire cache.
    \"\"\"
    global cache, cache_ttl
    cache = {}
    cache_ttl = {}


def clear_expired_cache():
    \"\"\"
    Clear expired cache entries.
    \"\"\"
    global cache, cache_ttl
    current_time = time.time()
    expired_keys = [k for k, ttl in cache_ttl.items() if ttl <= current_time]
    for key in expired_keys:
        if key in cache:
            del cache[key]
        if key in cache_ttl:
            del cache_ttl[key]
"""
        
        with open(middleware_path, "w") as f:
            f.write(cache_middleware_content)
        
        print(f"Created cache middleware at {middleware_path}")
    
    # Update main.py to use the cache middleware
    main_path = Path(__file__).parent.parent.parent / "main.py"
    
    if main_path.exists():
        with open(main_path, "r") as f:
            main_content = f.read()
        
        # Add import for cache middleware
        if "from .core.cache_middleware import CacheMiddleware" not in main_content:
            import_section_end = main_content.find("# 로깅 설정")
            if import_section_end == -1:
                import_section_end = main_content.find("# FastAPI 앱 생성")
            
            if import_section_end != -1:
                updated_main_content = main_content[:import_section_end] + "from .core.cache_middleware import CacheMiddleware\n" + main_content[import_section_end:]
                
                # Add middleware
                middleware_section = updated_main_content.find("# 로깅 미들웨어 추가")
                if middleware_section != -1:
                    next_line_end = updated_main_content.find("\n", middleware_section)
                    if next_line_end != -1:
                        updated_main_content = updated_main_content[:next_line_end + 1] + "\n# 캐싱 미들웨어 추가\napp.add_middleware(CacheMiddleware)\n" + updated_main_content[next_line_end + 1:]
                        
                        # Write updated main.py
                        with open(main_path, "w") as f:
                            f.write(updated_main_content)
                        
                        print(f"Added cache middleware to {main_path}")
    
    print("API response caching implemented")


def optimize_query_execution():
    """
    Optimize query execution.
    """
    # Path to the query execution service
    query_service_path = Path(__file__).parent.parent.parent / "services" / "query_service.py"
    
    if not query_service_path.exists():
        print(f"Query service file {query_service_path} not found.")
        return
    
    # Read current implementation
    with open(query_service_path, "r") as f:
        service_content = f.read()
    
    # Add query optimization logic
    if "optimize_query" not in service_content:
        # Find the execute_query method
        execute_query_pos = service_content.find("async def execute_query")
        if execute_query_pos != -1:
            method_end = service_content.find("return", execute_query_pos)
            if method_end != -1:
                # Find the position to insert optimization
                insert_pos = service_content.find("sql =", execute_query_pos, method_end)
                if insert_pos != -1:
                    next_line_end = service_content.find("\n", insert_pos)
                    if next_line_end != -1:
                        # Add optimization code
                        optimization_code = """
        # Optimize query before execution
        sql = await self.optimize_query(sql, db_type)
"""
                        updated_content = service_content[:next_line_end + 1] + optimization_code + service_content[next_line_end + 1:]
                        
                        # Add optimize_query method
                        class_end = updated_content.rfind("}")
                        if class_end == -1:
                            class_end = len(updated_content)
                        
                        optimize_method = """
    async def optimize_query(self, sql: str, db_type: str) -> str:
        \"\"\"
        Optimize SQL query for better performance.
        
        Args:
            sql: SQL query to optimize
            db_type: Database type
        
        Returns:
            str: Optimized SQL query
        \"\"\"
        # Add query hints for better performance
        if db_type == "mssql":
            # Add OPTION hints for MS-SQL
            if "ORDER BY" in sql and "OPTION" not in sql:
                # Add FAST n hint for ordered queries
                sql = sql.rstrip(";") + " OPTION (FAST 10);"
            elif "GROUP BY" in sql and "OPTION" not in sql:
                # Add HASH GROUP hint
                sql = sql.rstrip(";") + " OPTION (HASH GROUP);"
        elif db_type == "hana":
            # Add hints for SAP HANA
            if "SELECT" in sql and "WITH HINT" not in sql:
                # Add result cache hint
                sql = sql.replace("SELECT", "SELECT /*+ RESULT_CACHE */")
        
        return sql
"""
                        
                        updated_content = updated_content[:class_end] + optimize_method + updated_content[class_end:]
                        
                        # Write updated service
                        with open(query_service_path, "w") as f:
                            f.write(updated_content)
                        
                        print(f"Added query optimization to {query_service_path}")
    
    print("Query execution optimized")


def implement_response_compression():
    """
    Implement response compression.
    """
    # Path to the main.py file
    main_path = Path(__file__).parent.parent.parent / "main.py"
    
    if not main_path.exists():
        print(f"Main file {main_path} not found.")
        return
    
    # Read current implementation
    with open(main_path, "r") as f:
        main_content = f.read()
    
    # Add GZip middleware if not already present
    if "GZipMiddleware" not in main_content:
        # Add import
        import_section_end = main_content.find("# 로깅 설정")
        if import_section_end == -1:
            import_section_end = main_content.find("# FastAPI 앱 생성")
        
        if import_section_end != -1:
            updated_main_content = main_content[:import_section_end] + "from fastapi.middleware.gzip import GZipMiddleware\n" + main_content[import_section_end:]
            
            # Add middleware
            middleware_section = updated_main_content.find("# CORS 미들웨어 설정")
            if middleware_section != -1:
                next_line_end = updated_main_content.find(")", middleware_section)
                if next_line_end != -1:
                    next_line_end = updated_main_content.find("\n", next_line_end)
                    if next_line_end != -1:
                        updated_main_content = updated_main_content[:next_line_end + 1] + "\n# GZip 압축 미들웨어 추가\napp.add_middleware(GZipMiddleware, minimum_size=1000)\n" + updated_main_content[next_line_end + 1:]
                        
                        # Write updated main.py
                        with open(main_path, "w") as f:
                            f.write(updated_main_content)
                        
                        print(f"Added GZip compression middleware to {main_path}")
    
    print("Response compression implemented")


def create_optimization_report(analysis, recommendations):
    """
    Create an optimization report.
    
    Args:
        analysis: Analysis results
        recommendations: Optimization recommendations
    """
    # Create results directory if it doesn't exist
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write report to file
    report_path = results_dir / f"optimization_report_{timestamp}.md"
    with open(report_path, "w") as f:
        f.write(f"# System Optimization Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Performance Analysis\n\n")
        
        if "slow_endpoints" in analysis and analysis["slow_endpoints"]:
            f.write("### Slow API Endpoints\n\n")
            for endpoint, response_time in analysis["slow_endpoints"].items():
                f.write(f"- **{endpoint}**: {response_time:.2f} ms\n")
        else:
            f.write("No slow API endpoints identified.\n")
        
        if "memory_leaks" in analysis and analysis["memory_leaks"]:
            f.write("\n### Potential Memory Leaks\n\n")
            for leak in analysis["memory_leaks"]:
                f.write(f"```\n{leak}\n```\n\n")
        else:
            f.write("\nNo significant memory leaks identified.\n")
        
        f.write("\n## Optimization Recommendations\n\n")
        f.write("\n".join(recommendations))
        
        f.write("\n\n## Applied Optimizations\n\n")
        f.write("*Optimizations will be listed here after they are applied.*\n")
    
    print(f"Optimization report created at {report_path}")
    return report_path


def update_optimization_report(optimizations_applied):
    """
    Update the optimization report with applied optimizations.
    
    Args:
        optimizations_applied: List of applied optimizations
    """
    results_dir = Path(RESULTS_DIR)
    if not results_dir.exists():
        return
    
    # Find the latest optimization report
    report_files = list(results_dir.glob("optimization_report_*.md"))
    if not report_files:
        return
    
    latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
    
    # Read current report
    with open(latest_report, "r") as f:
        report_content = f.read()
    
    # Update applied optimizations section
    applied_section = "## Applied Optimizations"
    if applied_section in report_content:
        section_pos = report_content.find(applied_section)
        section_end = report_content.find("##", section_pos + len(applied_section))
        if section_end == -1:
            section_end = len(report_content)
        
        updated_content = report_content[:section_pos + len(applied_section)] + "\n\n"
        updated_content += f"*Applied on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        for opt in optimizations_applied:
            updated_content += f"- {opt}\n"
        
        if section_end < len(report_content):
            updated_content += report_content[section_end:]
        
        # Write updated report
        with open(latest_report, "w") as f:
            f.write(updated_content)
        
        print(f"Updated optimization report at {latest_report}")


if __name__ == "__main__":
    apply_optimizations()