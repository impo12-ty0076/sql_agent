"""
Quick timeout test
"""

import asyncio
import sys
sys.path.append('.')

from services.python_interpreter import PythonInterpreterService, ExecutionConfig


async def test_timeout():
    """Test execution timeout"""
    print("Testing timeout with 1 second limit...")
    
    config = ExecutionConfig(max_execution_time=0.5)  # 0.5 second timeout
    service = PythonInterpreterService(config)
    
    code = """
import time
print("Starting long operation...")
time.sleep(2)  # Sleep for 2 seconds (longer than 0.5s timeout)
print("This should not be printed due to timeout")
result = "completed"
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time:.3f}s")


if __name__ == "__main__":
    asyncio.run(test_timeout())