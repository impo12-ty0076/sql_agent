"""
Manual test script for Enhanced Python Interpreter Service
"""

import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.append('.')

from services.python_interpreter import PythonInterpreterService, ExecutionConfig


async def test_cancellable_sleep():
    """Test cancellable sleep function"""
    print("Testing cancellable sleep...")
    
    service = PythonInterpreterService()
    
    code = """
import time
print("Starting sleep loop...")
for i in range(10):
    print(f"Sleeping iteration {i}")
    time.sleep(1)  # This should be cancellable
    print(f"Finished iteration {i}")
print("This should not be printed if cancelled")
"""
    
    # Start execution
    execution_task = asyncio.create_task(service.execute_code(code))
    
    # Wait a bit then cancel
    await asyncio.sleep(2.5)
    
    # Get execution ID and cancel
    active_executions = service.list_active_executions()
    if active_executions:
        execution_id = active_executions[0]
        print(f"Cancelling execution {execution_id}...")
        cancelled = service.cancel_execution(execution_id)
        print(f"Cancellation initiated: {cancelled}")
    
    # Wait for execution to complete
    result = await execution_task
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print()


async def test_timestamp_tracking():
    """Test timestamp tracking in execution results"""
    print("Testing timestamp tracking...")
    
    service = PythonInterpreterService()
    
    # Execute a simple code
    code = "result = 42"
    result = await service.execute_code(code)
    
    print(f"Execution ID: {result.execution_id}")
    print(f"Status: {result.status}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Current time: {time.time()}")
    print(f"Difference: {time.time() - result.timestamp:.3f}s")
    print()
    
    # Store an old result
    old_result = result
    old_result.timestamp = time.time() - 3600  # 1 hour ago
    service.execution_history["old-test"] = old_result
    
    # Clean up results older than 30 minutes
    cleaned_count = service.cleanup_old_results(max_age_hours=0.5)  # 30 minutes
    print(f"Cleaned up {cleaned_count} old results")
    print(f"Old result still exists: {'old-test' in service.execution_history}")
    print()


async def test_memory_monitoring():
    """Test memory monitoring"""
    print("Testing memory monitoring...")
    
    service = PythonInterpreterService()
    
    # Get current memory usage
    memory_usage = service._get_memory_usage()
    print(f"Current memory usage: {memory_usage:.2f} MB")
    
    # Execute code that allocates memory
    code = """
# Allocate a large list
large_list = [0] * 1000000  # ~8MB
print(f"Created list with {len(large_list)} elements")
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Memory usage: {result.memory_usage:.2f} MB")
    print()


async def test_resource_limits():
    """Test resource limits"""
    print("Testing resource limits...")
    
    # Create service with strict limits
    config = ExecutionConfig(max_execution_time=1.0, max_memory_mb=50.0)
    service = PythonInterpreterService(config)
    
    # Test timeout
    print("Testing timeout limit...")
    code_timeout = """
import time
print("Starting long operation...")
time.sleep(2)  # Should timeout
print("This should not be printed")
"""
    
    result = await service.execute_code(code_timeout)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print()
    
    # Test memory limit (may not trigger on all systems)
    print("Testing memory limit...")
    code_memory = """
# Try to allocate a lot of memory
big_list = [[0] * 1000 for _ in range(10000)]
print("Allocated big list")
"""
    
    result = await service.execute_code(code_memory)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Memory usage: {result.memory_usage:.2f} MB")
    print()


async def main():
    """Run all tests"""
    print("=== Enhanced Python Interpreter Service Manual Tests ===\n")
    
    await test_cancellable_sleep()
    await test_timestamp_tracking()
    await test_memory_monitoring()
    await test_resource_limits()
    
    print("=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())