"""
Python Code Execution Service

This service provides a Python interpreter environment for executing data analysis
and visualization code in a controlled manner with resource limits and cancellation support.

Note: This is the original version of the Python interpreter service.
For the enhanced version with integrated data analysis capabilities,
use the EnhancedPythonInterpreterService from python_interpreter_enhanced.py.
"""

import asyncio
import io
import sys
import threading
import time
import traceback
import uuid
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import signal
import os
import platform
try:
    import resource
except ImportError:
    resource = None  # Not available on Windows
import psutil

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from io import StringIO
import base64


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Result of Python code execution"""
    execution_id: str
    status: ExecutionStatus
    output: str = ""
    error: str = ""
    variables: Dict[str, Any] = None
    plots: list = None
    execution_time: float = 0.0
    memory_usage: float = 0.0
    timestamp: float = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.plots is None:
            self.plots = []
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ExecutionConfig:
    """Configuration for Python code execution"""
    max_execution_time: float = 30.0  # seconds
    max_memory_mb: float = 512.0  # MB
    allowed_imports: set = None
    blocked_functions: set = None
    
    def __post_init__(self):
        if self.allowed_imports is None:
            self.allowed_imports = {
                'pandas', 'numpy', 'matplotlib', 'plotly', 'seaborn',
                'scipy', 'sklearn', 'datetime', 'math', 'statistics',
                'json', 're', 'collections', 'itertools'
            }
        if self.blocked_functions is None:
            self.blocked_functions = {
                'open', 'exec', 'eval', 'compile', '__import__',
                'input', 'raw_input', 'file', 'execfile'
            }


class ExecutionContext:
    """Context for managing a single Python code execution"""
    
    def __init__(self, execution_id: str, config: ExecutionConfig):
        self.execution_id = execution_id
        self.config = config
        self.start_time = None
        self.cancelled = False
        self.thread = None
        self.process = None
        self.cancel_event = threading.Event()
        
    def cancel(self):
        """Cancel the execution"""
        self.cancelled = True
        self.cancel_event.set()
        
        if self.thread and self.thread.is_alive():
            # Note: Python threads cannot be forcefully terminated
            # We rely on the execution loop checking self.cancelled
            # and the cancel_event being set
            pass
            
        # If we have a process ID, try to terminate it (for Windows support)
        if self.process and isinstance(self.process, psutil.Process):
            try:
                if self.process.is_running():
                    self.process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")
                pass


class PythonInterpreterService:
    """Service for executing Python code with resource limits and cancellation support"""
    
    def __init__(self, config: ExecutionConfig = None):
        self.config = config or ExecutionConfig()
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: Dict[str, ExecutionResult] = {}
        
    def create_execution_id(self) -> str:
        """Generate a unique execution ID"""
        return str(uuid.uuid4())
    
    def _setup_execution_environment(self) -> Dict[str, Any]:
        """Setup the execution environment with allowed modules and data"""
        # Create a restricted global environment
        safe_globals = {
            '__builtins__': {
                'len': len, 'str': str, 'int': int, 'float': float,
                'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
                'set': set, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter, 'sorted': sorted,
                'sum': sum, 'min': max, 'max': max, 'abs': abs,
                'round': round, 'print': print, 'type': type,
                'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
                'setattr': setattr, 'dir': dir, 'help': help,
                '__import__': __import__,  # Needed for import statements
            },
            'pd': pd,
            'pandas': pd,
            'np': np,
            'numpy': np,
            'plt': plt,
            'matplotlib': matplotlib,
            'go': go,
            'px': px,
            'plotly': {'graph_objects': go, 'express': px},
        }
        
        return safe_globals
    
    def _capture_plots(self) -> list:
        """Capture matplotlib plots as base64 encoded images"""
        plots = []
        
        # Get all matplotlib figures
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            
            # Save figure to bytes
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            img_buffer.seek(0)
            
            # Encode as base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            plots.append({
                'type': 'matplotlib',
                'figure_num': fig_num,
                'data': img_base64,
                'format': 'png'
            })
            
            img_buffer.close()
        
        # Clear all figures to prevent memory leaks
        plt.close('all')
        
        return plots
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            # On Windows, use WorkingSet instead of RSS if available
            if platform.system() == 'Windows' and hasattr(memory_info, 'WorkingSet'):
                return memory_info.WorkingSet / 1024 / 1024  # Convert to MB
            
            # Default to RSS (Resident Set Size)
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return 0.0
    
    def _execute_code_thread(self, code: str, context: ExecutionContext, 
                           data: Dict[str, Any] = None) -> ExecutionResult:
        """Execute Python code in a separate thread"""
        result = ExecutionResult(
            execution_id=context.execution_id,
            status=ExecutionStatus.RUNNING
        )
        
        try:
            # Setup execution environment
            exec_globals = self._setup_execution_environment()
            exec_locals = {}
            
            # Add provided data to the environment
            if data:
                exec_locals.update(data)
                
            # Add cancel check function to allow code to check for cancellation
            def check_cancelled():
                return context.cancelled or context.cancel_event.is_set()
            
            exec_globals['check_cancelled'] = check_cancelled
            
            # Add a modified sleep function that checks for cancellation
            original_sleep = time.sleep
            def cancellable_sleep(seconds):
                start_time = time.time()
                while time.time() - start_time < seconds:
                    if check_cancelled():
                        raise InterruptedError("Execution cancelled")
                    original_sleep(min(0.1, seconds - (time.time() - start_time)))
            
            exec_globals['time'] = type('time', (), {
                'sleep': cancellable_sleep,
                'time': time.time,
                **{name: getattr(time, name) for name in dir(time) 
                   if not name.startswith('_') and name not in ['sleep']}
            })
            
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            context.start_time = time.time()
            initial_memory = self._get_memory_usage()
            
            # Track the current process for potential termination
            context.process = psutil.Process(os.getpid())
            
            try:
                # Redirect output
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # Execute the code
                # Note: We can't easily interrupt exec(), so timeout relies on monitoring thread
                # and our cancellable functions
                exec(code, exec_globals, exec_locals)
                
                # Check if execution was cancelled
                if context.cancelled or context.cancel_event.is_set():
                    result.status = ExecutionStatus.CANCELLED
                    return result
                
                # Capture results
                result.output = stdout_capture.getvalue()
                result.variables = {k: v for k, v in exec_locals.items() 
                                  if not k.startswith('_')}
                result.plots = self._capture_plots()
                result.status = ExecutionStatus.COMPLETED
                
            except InterruptedError:
                result.status = ExecutionStatus.CANCELLED
                result.error = "Execution was cancelled"
                
            except Exception as e:
                result.status = ExecutionStatus.FAILED
                result.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Calculate execution metrics
                result.execution_time = time.time() - context.start_time
                result.memory_usage = self._get_memory_usage() - initial_memory
                
                # Add any stderr output to error
                stderr_output = stderr_capture.getvalue()
                if stderr_output:
                    if result.error:
                        result.error += f"\n\nStderr:\n{stderr_output}"
                    else:
                        result.error = stderr_output
                        
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = f"Execution setup error: {str(e)}"
            
        return result
    
    async def execute_code(self, code: str, data: Dict[str, Any] = None,
                          progress_callback: Optional[Callable[[str, float], None]] = None) -> ExecutionResult:
        """
        Execute Python code asynchronously with resource limits and cancellation support
        
        Args:
            code: Python code to execute
            data: Optional data dictionary to make available in execution environment
            progress_callback: Optional callback for progress updates
            
        Returns:
            ExecutionResult with execution details
        """
        execution_id = self.create_execution_id()
        context = ExecutionContext(execution_id, self.config)
        
        # Store active execution
        self.active_executions[execution_id] = context
        
        try:
            # Create and start execution thread
            result_container = [None]
            
            def thread_target():
                result_container[0] = self._execute_code_thread(code, context, data)
            
            thread = threading.Thread(target=thread_target)
            context.thread = thread
            thread.start()
            
            # Monitor execution with timeout and progress updates
            start_time = time.time()
            timeout_occurred = False
            memory_limit_exceeded = False
            
            while thread.is_alive():
                elapsed = time.time() - start_time
                
                # Check if cancelled externally
                if context.cancel_event.is_set():
                    break
                
                # Check timeout
                if elapsed > self.config.max_execution_time:
                    context.cancel()
                    timeout_occurred = True
                    # Give thread a short time to cleanup, then break
                    thread.join(timeout=0.5)
                    break
                
                # Check memory usage
                memory_usage = self._get_memory_usage()
                if memory_usage > self.config.max_memory_mb:
                    context.cancel()
                    memory_limit_exceeded = True
                    thread.join(timeout=1.0)
                    break
                
                # Send progress update
                if progress_callback:
                    progress = min(elapsed / self.config.max_execution_time, 0.9)
                    progress_callback(execution_id, progress)
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            # Handle special cases
            if timeout_occurred:
                elapsed = time.time() - start_time
                result = ExecutionResult(
                    execution_id=execution_id,
                    status=ExecutionStatus.TIMEOUT,
                    error=f"Execution timed out after {self.config.max_execution_time} seconds",
                    execution_time=elapsed
                )
            elif memory_limit_exceeded:
                elapsed = time.time() - start_time
                memory_usage = self._get_memory_usage()
                result = ExecutionResult(
                    execution_id=execution_id,
                    status=ExecutionStatus.FAILED,
                    error=f"Memory limit exceeded: {memory_usage:.1f}MB > {self.config.max_memory_mb}MB",
                    execution_time=elapsed,
                    memory_usage=memory_usage
                )
            else:
                # Thread completed normally or was cancelled
                thread.join()
                result = result_container[0]
                
                # If result is None (shouldn't happen but just in case)
                if result is None:
                    elapsed = time.time() - start_time
                    result = ExecutionResult(
                        execution_id=execution_id,
                        status=ExecutionStatus.FAILED,
                        error="Execution failed with unknown error",
                        execution_time=elapsed
                    )
            
            # Store result in history with timestamp
            result.timestamp = time.time()
            self.execution_history[execution_id] = result
            
            # Send final progress update if callback provided
            if progress_callback and result.status == ExecutionStatus.COMPLETED:
                progress_callback(execution_id, 1.0)
            
            return result
            
        finally:
            # Cleanup
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancellation was initiated, False if execution not found
        """
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            context.cancel()
            return True
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get the status of an execution"""
        if execution_id in self.active_executions:
            return ExecutionStatus.RUNNING
        elif execution_id in self.execution_history:
            return self.execution_history[execution_id].status
        return None
    
    def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get the result of a completed execution"""
        return self.execution_history.get(execution_id)
    
    def list_active_executions(self) -> list:
        """List all currently active executions"""
        return list(self.active_executions.keys())
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """Clean up old execution results"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        to_remove = []
        for execution_id, result in self.execution_history.items():
            if result.timestamp and result.timestamp < cutoff_time:
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.execution_history[execution_id]
            
        return len(to_remove)  # Return number of cleaned up results


# Global service instance
python_interpreter_service = PythonInterpreterService()

# Import the enhanced version for easier access
try:
    from .python_interpreter_enhanced import EnhancedPythonInterpreterService, enhanced_python_interpreter_service
except ImportError:
    # If the enhanced version is not available, use the original
    EnhancedPythonInterpreterService = PythonInterpreterService
    enhanced_python_interpreter_service = python_interpreter_service