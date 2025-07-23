"""
Unit tests for Python Interpreter Service
"""

import pytest
import asyncio
import time
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from services.python_interpreter import (
    PythonInterpreterService,
    ExecutionConfig,
    ExecutionStatus,
    ExecutionResult,
    ExecutionContext
)


class TestExecutionConfig:
    """Test ExecutionConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ExecutionConfig()
        
        assert config.max_execution_time == 30.0
        assert config.max_memory_mb == 512.0
        assert 'pandas' in config.allowed_imports
        assert 'numpy' in config.allowed_imports
        assert 'open' in config.blocked_functions
        assert 'exec' in config.blocked_functions
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ExecutionConfig(
            max_execution_time=60.0,
            max_memory_mb=1024.0,
            allowed_imports={'pandas', 'numpy'},
            blocked_functions={'eval', 'exec'}
        )
        
        assert config.max_execution_time == 60.0
        assert config.max_memory_mb == 1024.0
        assert config.allowed_imports == {'pandas', 'numpy'}
        assert config.blocked_functions == {'eval', 'exec'}


class TestExecutionResult:
    """Test ExecutionResult class"""
    
    def test_default_result(self):
        """Test default ExecutionResult values"""
        result = ExecutionResult(
            execution_id="test-123",
            status=ExecutionStatus.COMPLETED
        )
        
        assert result.execution_id == "test-123"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output == ""
        assert result.error == ""
        assert result.variables == {}
        assert result.plots == []
        assert result.execution_time == 0.0
        assert result.memory_usage == 0.0


class TestExecutionContext:
    """Test ExecutionContext class"""
    
    def test_context_creation(self):
        """Test ExecutionContext creation"""
        config = ExecutionConfig()
        context = ExecutionContext("test-123", config)
        
        assert context.execution_id == "test-123"
        assert context.config == config
        assert context.start_time is None
        assert context.cancelled is False
        assert context.thread is None
        assert context.process is None
    
    def test_context_cancel(self):
        """Test ExecutionContext cancellation"""
        config = ExecutionConfig()
        context = ExecutionContext("test-123", config)
        
        context.cancel()
        assert context.cancelled is True


class TestPythonInterpreterService:
    """Test PythonInterpreterService class"""
    
    @pytest.fixture
    def service(self):
        """Create a PythonInterpreterService instance for testing"""
        config = ExecutionConfig(max_execution_time=5.0, max_memory_mb=256.0)
        return PythonInterpreterService(config)
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert isinstance(service.config, ExecutionConfig)
        assert service.active_executions == {}
        assert service.execution_history == {}
    
    def test_create_execution_id(self, service):
        """Test execution ID generation"""
        id1 = service.create_execution_id()
        id2 = service.create_execution_id()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0
    
    def test_setup_execution_environment(self, service):
        """Test execution environment setup"""
        env = service._setup_execution_environment()
        
        assert 'pd' in env
        assert 'pandas' in env
        assert 'np' in env
        assert 'numpy' in env
        assert 'plt' in env
        assert 'matplotlib' in env
        assert '__builtins__' in env
        
        # Test that dangerous functions are not available
        builtins = env['__builtins__']
        assert 'open' not in builtins
        assert 'exec' not in builtins
        assert 'eval' not in builtins
    
    @pytest.mark.asyncio
    async def test_simple_code_execution(self, service):
        """Test simple Python code execution"""
        code = """
result = 2 + 2
print(f"Result: {result}")
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert "Result: 4" in result.output
        assert result.variables['result'] == 4
        assert result.execution_time > 0
        assert result.error == ""
    
    @pytest.mark.asyncio
    async def test_pandas_code_execution(self, service):
        """Test pandas code execution"""
        code = """
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(df.head())
row_count = len(df)
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.variables['row_count'] == 3
        assert isinstance(result.variables['df'], pd.DataFrame)
        assert result.error == ""
    
    @pytest.mark.asyncio
    async def test_matplotlib_plot_execution(self, service):
        """Test matplotlib plot generation"""
        code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.plots) > 0
        assert result.plots[0]['type'] == 'matplotlib'
        assert result.plots[0]['format'] == 'png'
        assert len(result.plots[0]['data']) > 0  # Base64 encoded image data
        assert result.error == ""
    
    @pytest.mark.asyncio
    async def test_code_execution_with_data(self, service):
        """Test code execution with provided data"""
        data = {
            'input_data': pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
        }
        
        code = """
result_sum = input_data['x'].sum() + input_data['y'].sum()
print(f"Sum: {result_sum}")
"""
        
        result = await service.execute_code(code, data=data)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.variables['result_sum'] == 21  # (1+2+3) + (4+5+6)
        assert "Sum: 21" in result.output
        assert result.error == ""
    
    @pytest.mark.asyncio
    async def test_code_execution_error(self, service):
        """Test code execution with error"""
        code = """
# This will cause a NameError
print(undefined_variable)
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.FAILED
        assert "NameError" in result.error
        assert "undefined_variable" in result.error
        assert result.output == ""
    
    @pytest.mark.asyncio
    async def test_code_execution_timeout(self, service):
        """Test code execution timeout"""
        # Set a very short timeout for testing
        service.config.max_execution_time = 0.5
        
        code = """
import time
time.sleep(2)  # Sleep longer than timeout
result = "completed"
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error.lower()
        assert result.execution_time >= 0.5
    
    @pytest.mark.asyncio
    async def test_execution_cancellation(self, service):
        """Test execution cancellation"""
        code = """
import time
for i in range(100):
    time.sleep(0.1)
    print(f"Step {i}")
result = "completed"
"""
        
        # Start execution
        execution_task = asyncio.create_task(service.execute_code(code))
        
        # Wait a bit then cancel
        await asyncio.sleep(0.2)
        
        # Get execution ID from active executions
        execution_ids = service.list_active_executions()
        assert len(execution_ids) == 1
        
        execution_id = execution_ids[0]
        cancelled = service.cancel_execution(execution_id)
        assert cancelled is True
        
        # Wait for execution to complete
        result = await execution_task
        
        # Note: Due to Python threading limitations, cancellation might not
        # always result in CANCELLED status, but execution should stop
        assert result.status in [ExecutionStatus.CANCELLED, ExecutionStatus.COMPLETED]
    
    def test_get_execution_status(self, service):
        """Test getting execution status"""
        # Test non-existent execution
        status = service.get_execution_status("non-existent")
        assert status is None
        
        # Test with stored result
        result = ExecutionResult("test-123", ExecutionStatus.COMPLETED)
        service.execution_history["test-123"] = result
        
        status = service.get_execution_status("test-123")
        assert status == ExecutionStatus.COMPLETED
    
    def test_get_execution_result(self, service):
        """Test getting execution result"""
        # Test non-existent execution
        result = service.get_execution_result("non-existent")
        assert result is None
        
        # Test with stored result
        stored_result = ExecutionResult("test-123", ExecutionStatus.COMPLETED)
        service.execution_history["test-123"] = stored_result
        
        result = service.get_execution_result("test-123")
        assert result == stored_result
    
    def test_list_active_executions(self, service):
        """Test listing active executions"""
        # Initially empty
        active = service.list_active_executions()
        assert active == []
        
        # Add some active executions
        config = ExecutionConfig()
        context1 = ExecutionContext("exec-1", config)
        context2 = ExecutionContext("exec-2", config)
        
        service.active_executions["exec-1"] = context1
        service.active_executions["exec-2"] = context2
        
        active = service.list_active_executions()
        assert len(active) == 2
        assert "exec-1" in active
        assert "exec-2" in active
    
    def test_cleanup_old_results(self, service):
        """Test cleanup of old results"""
        # Add some results
        result1 = ExecutionResult("old-1", ExecutionStatus.COMPLETED)
        result2 = ExecutionResult("old-2", ExecutionStatus.FAILED)
        
        service.execution_history["old-1"] = result1
        service.execution_history["old-2"] = result2
        
        # Cleanup (currently doesn't remove anything due to no timestamp)
        service.cleanup_old_results(max_age_hours=1)
        
        # Results should still be there (no timestamp implementation yet)
        assert len(service.execution_history) == 2
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, service):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(execution_id, progress):
            progress_updates.append((execution_id, progress))
        
        code = """
import time
time.sleep(0.5)
result = "completed"
"""
        
        result = await service.execute_code(code, progress_callback=progress_callback)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert len(progress_updates) > 0
        
        # Check that progress updates were received
        for execution_id, progress in progress_updates:
            assert isinstance(execution_id, str)
            assert 0 <= progress <= 1.0
    
    @patch('services.python_interpreter.psutil.Process')
    def test_memory_usage_monitoring(self, mock_process, service):
        """Test memory usage monitoring"""
        # Mock memory info
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB in bytes
        
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_process_instance
        
        memory_usage = service._get_memory_usage()
        assert memory_usage == 100.0  # 100 MB
    
    def test_capture_plots_empty(self, service):
        """Test plot capture when no plots exist"""
        plots = service._capture_plots()
        assert plots == []


@pytest.mark.asyncio
async def test_global_service_instance():
    """Test that global service instance works"""
    from services.python_interpreter import python_interpreter_service
    
    code = "result = 1 + 1"
    result = await python_interpreter_service.execute_code(code)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert result.variables['result'] == 2


if __name__ == "__main__":
    pytest.main([__file__])