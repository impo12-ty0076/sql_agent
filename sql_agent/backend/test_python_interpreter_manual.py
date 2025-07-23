"""
Manual test script for Python Interpreter Service
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

from services.python_interpreter import PythonInterpreterService, ExecutionConfig


async def test_basic_execution():
    """Test basic Python code execution"""
    print("Testing basic execution...")
    
    service = PythonInterpreterService()
    
    code = """
result = 2 + 2
print(f"Result: {result}")
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Variables: {result.variables}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print(f"Error: {result.error}")
    print()


async def test_pandas_execution():
    """Test pandas code execution"""
    print("Testing pandas execution...")
    
    service = PythonInterpreterService()
    
    code = """
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50]
})

print("DataFrame:")
print(df)

mean_a = df['A'].mean()
sum_b = df['B'].sum()

print(f"Mean of A: {mean_a}")
print(f"Sum of B: {sum_b}")
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Variables keys: {list(result.variables.keys())}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print(f"Error: {result.error}")
    print()


async def test_matplotlib_execution():
    """Test matplotlib plot generation"""
    print("Testing matplotlib execution...")
    
    service = PythonInterpreterService()
    
    code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, label='sin(x)')
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.legend()
plt.grid(True)

print("Plot created successfully")
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Number of plots: {len(result.plots)}")
    if result.plots:
        print(f"Plot type: {result.plots[0]['type']}")
        print(f"Plot format: {result.plots[0]['format']}")
        print(f"Plot data length: {len(result.plots[0]['data'])}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print(f"Error: {result.error}")
    print()


async def test_error_handling():
    """Test error handling"""
    print("Testing error handling...")
    
    service = PythonInterpreterService()
    
    code = """
# This will cause an error
print(undefined_variable)
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print()


async def test_timeout():
    """Test execution timeout"""
    print("Testing timeout...")
    
    config = ExecutionConfig(max_execution_time=1.0)  # 1 second timeout
    service = PythonInterpreterService(config)
    
    code = """
import time
print("Starting long operation...")
time.sleep(3)  # Sleep longer than timeout
print("This should not be printed")
result = "completed"
"""
    
    result = await service.execute_code(code)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print()


async def test_with_data():
    """Test execution with provided data"""
    print("Testing execution with provided data...")
    
    service = PythonInterpreterService()
    
    import pandas as pd
    data = {
        'sales_data': pd.DataFrame({
            'product': ['A', 'B', 'C', 'D'],
            'sales': [100, 200, 150, 300],
            'profit': [20, 40, 30, 60]
        })
    }
    
    code = """
print("Sales Data:")
print(sales_data)

total_sales = sales_data['sales'].sum()
total_profit = sales_data['profit'].sum()
profit_margin = (total_profit / total_sales) * 100

print(f"Total Sales: {total_sales}")
print(f"Total Profit: {total_profit}")
print(f"Profit Margin: {profit_margin:.2f}%")

# Create a simple analysis
best_product = sales_data.loc[sales_data['sales'].idxmax(), 'product']
print(f"Best selling product: {best_product}")
"""
    
    result = await service.execute_code(code, data=data)
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Variables keys: {list(result.variables.keys())}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print(f"Error: {result.error}")
    print()


async def test_cancellation():
    """Test execution cancellation"""
    print("Testing cancellation...")
    
    service = PythonInterpreterService()
    
    code = """
import time
for i in range(10):
    print(f"Step {i}")
    time.sleep(0.2)
print("Completed all steps")
"""
    
    # Start execution
    execution_task = asyncio.create_task(service.execute_code(code))
    
    # Wait a bit then cancel
    await asyncio.sleep(0.5)
    
    # Get execution ID and cancel
    active_executions = service.list_active_executions()
    if active_executions:
        execution_id = active_executions[0]
        cancelled = service.cancel_execution(execution_id)
        print(f"Cancellation initiated: {cancelled}")
    
    # Wait for execution to complete
    result = await execution_task
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time:.3f}s")
    print()


async def main():
    """Run all tests"""
    print("=== Python Interpreter Service Manual Tests ===\n")
    
    await test_basic_execution()
    await test_pandas_execution()
    await test_matplotlib_execution()
    await test_error_handling()
    await test_timeout()
    await test_with_data()
    await test_cancellation()
    
    print("=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())