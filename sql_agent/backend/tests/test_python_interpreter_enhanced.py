"""
Unit tests for enhanced Python Interpreter Service
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


@pytest.mark.asyncio
async def test_timestamp_tracking():
    """Test that timestamps are properly tracked in execution results"""
    service = PythonInterpreterService()
    
    code = "result = 1 + 1"
    result = await service.execute_code(code)
    
    assert result.timestamp is not None
    assert isinstance(result.timestamp, float)
    assert abs(result.timestamp - time.time()) < 5  # Should be recent


@pytest.mark.asyncio
async def test_cleanup_with_timestamps():
    """Test cleanup of old results using timestamps"""
    service = PythonInterpreterService()
    
    # Create some results with different timestamps
    now = time.time()
    
    # Old result (3 hours ago)
    old_result = ExecutionResult(
        execution_id="old-test",
        status=ExecutionStatus.COMPLETED,
        timestamp=now - 3 * 3600
    )
    service.execution_history["old-test"] = old_result
    
    # Recent result (10 minutes ago)
    recent_result = ExecutionResult(
        execution_id="recent-test",
        status=ExecutionStatus.COMPLETED,
        timestamp=now - 10 * 60
    )
    service.execution_history["recent-test"] = recent_result
    
    # Clean up results older than 1 hour
    cleaned_count = service.cleanup_old_results(max_age_hours=1)
    
    # Should have removed the old result but kept the recent one
    assert cleaned_count == 1
    assert "old-test" not in service.execution_history
    assert "recent-test" in service.execution_history


@pytest.mark.asyncio
async def test_cancellable_sleep():
    """Test that sleep operations can be cancelled"""
    service = PythonInterpreterService()
    
    code = """
import time
print("Starting long sleep...")
time.sleep(10)  # Should be cancelled during this sleep
print("This should not be printed")
"""
    
    # Start execution
    execution_task = asyncio.create_task(service.execute_code(code))
    
    # Wait a bit then cancel
    await asyncio.sleep(0.5)
    
    # Get execution ID from active executions
    execution_ids = service.list_active_executions()
    assert len(execution_ids) == 1
    
    execution_id = execution_ids[0]
    cancelled = service.cancel_execution(execution_id)
    assert cancelled is True
    
    # Wait for execution to complete
    result = await execution_task
    
    # Should be cancelled
    assert result.status == ExecutionStatus.CANCELLED
    assert "Starting long sleep..." in result.output
    assert "This should not be printed" not in result.output


@pytest.mark.asyncio
async def test_memory_limit_enforcement():
    """Test that memory limits are enforced"""
    # Set a very low memory limit for testing
    config = ExecutionConfig(max_memory_mb=1.0)  # 1MB limit
    service = PythonInterpreterService(config)
    
    # Mock memory usage to simulate exceeding the limit
    with patch.object(service, '_get_memory_usage', return_value=100.0):  # Return 100MB
        code = """
# This should be stopped due to memory limit
data = [0] * 1000000  # Allocate some memory
"""
        
        result = await service.execute_code(code)
        
        assert result.status == ExecutionStatus.FAILED
        assert "Memory limit exceeded" in result.error


@pytest.mark.asyncio
async def test_windows_memory_monitoring():
    """Test Windows-specific memory monitoring"""
    service = PythonInterpreterService()
    
    # Mock platform to simulate Windows
    with patch('platform.system', return_value='Windows'):
        # Mock psutil Process with Windows-specific memory info
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        
        # Set WorkingSet attribute for Windows
        mock_memory_info.WorkingSet = 200 * 1024 * 1024  # 200MB
        mock_memory_info.rss = 150 * 1024 * 1024  # 150MB (should use WorkingSet instead)
        
        mock_process.memory_info.return_value = mock_memory_info
        
        with patch('psutil.Process', return_value=mock_process):
            memory_usage = service._get_memory_usage()
            assert memory_usage == 200.0  # Should use WorkingSet value


if __name__ == "__main__":
    pytest.main([__file__])