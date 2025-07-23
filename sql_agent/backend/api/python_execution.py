"""
Python Code Execution API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio

from ..services.python_interpreter import (
    python_interpreter_service,
    ExecutionStatus,
    ExecutionConfig
)


router = APIRouter(prefix="/api/python", tags=["python-execution"])


class ExecuteCodeRequest(BaseModel):
    """Request model for code execution"""
    code: str
    data: Optional[Dict[str, Any]] = None
    max_execution_time: Optional[float] = 30.0
    max_memory_mb: Optional[float] = 512.0


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status"""
    execution_id: str
    status: str
    message: Optional[str] = None


class ExecutionResultResponse(BaseModel):
    """Response model for execution result"""
    execution_id: str
    status: str
    output: str
    error: str
    variables: Dict[str, Any]
    plots: List[Dict[str, Any]]
    execution_time: float
    memory_usage: float
    timestamp: Optional[float] = None


class ProgressUpdate(BaseModel):
    """Progress update model"""
    execution_id: str
    progress: float
    message: str


# Store for progress updates (in production, use Redis or similar)
progress_store: Dict[str, List[ProgressUpdate]] = {}


@router.post("/execute", response_model=ExecutionStatusResponse)
async def execute_code(request: ExecuteCodeRequest):
    """
    Execute Python code asynchronously
    
    This endpoint starts Python code execution and returns immediately with an execution ID.
    Use the status and result endpoints to monitor progress and get results.
    """
    try:
        # Create execution config
        config = ExecutionConfig(
            max_execution_time=request.max_execution_time,
            max_memory_mb=request.max_memory_mb
        )
        
        # Update service config
        python_interpreter_service.config = config
        
        # Progress callback to store updates
        def progress_callback(execution_id: str, progress: float):
            if execution_id not in progress_store:
                progress_store[execution_id] = []
            
            progress_store[execution_id].append(ProgressUpdate(
                execution_id=execution_id,
                progress=progress,
                message=f"Execution {progress*100:.1f}% complete"
            ))
        
        # Start execution in background
        execution_id = python_interpreter_service.create_execution_id()
        
        # Execute code asynchronously
        asyncio.create_task(
            python_interpreter_service.execute_code(
                request.code,
                data=request.data,
                progress_callback=progress_callback
            )
        )
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING.value,
            message="Code execution started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start execution: {str(e)}")


@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """Get the status of a code execution"""
    try:
        status = python_interpreter_service.get_execution_status(execution_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            status=status.value,
            message=f"Execution is {status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/result/{execution_id}", response_model=ExecutionResultResponse)
async def get_execution_result(execution_id: str):
    """Get the result of a completed code execution"""
    try:
        result = python_interpreter_service.get_execution_result(execution_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Execution result not found")
        
        return ExecutionResultResponse(
            execution_id=result.execution_id,
            status=result.status.value,
            output=result.output,
            error=result.error,
            variables=result.variables,
            plots=result.plots,
            execution_time=result.execution_time,
            memory_usage=result.memory_usage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.post("/cancel/{execution_id}", response_model=ExecutionStatusResponse)
async def cancel_execution(execution_id: str):
    """Cancel a running code execution"""
    try:
        cancelled = python_interpreter_service.cancel_execution(execution_id)
        
        if not cancelled:
            raise HTTPException(status_code=404, detail="Execution not found or not running")
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            status=ExecutionStatus.CANCELLED.value,
            message="Cancellation requested"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


@router.get("/active", response_model=List[str])
async def list_active_executions():
    """List all currently active executions"""
    try:
        return python_interpreter_service.list_active_executions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/progress/{execution_id}", response_model=List[ProgressUpdate])
async def get_execution_progress(execution_id: str):
    """Get progress updates for an execution"""
    try:
        if execution_id not in progress_store:
            return []
        
        return progress_store[execution_id]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_results(max_age_hours: int = 24):
    """Clean up old execution results"""
    try:
        cleaned_count = python_interpreter_service.cleanup_old_results(max_age_hours)
        
        # Also cleanup progress store
        # In production, implement proper cleanup based on timestamps
        old_progress_keys = []
        for execution_id in progress_store.keys():
            if execution_id not in python_interpreter_service.execution_history:
                old_progress_keys.append(execution_id)
                
        for key in old_progress_keys:
            del progress_store[key]
        
        return {
            "message": f"Cleaned up results older than {max_age_hours} hours",
            "cleaned_results_count": cleaned_count,
            "cleaned_progress_count": len(old_progress_keys)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for Python execution service"""
    try:
        # Test basic functionality
        test_code = "result = 1 + 1"
        result = await python_interpreter_service.execute_code(test_code)
        
        if result.status == ExecutionStatus.COMPLETED and result.variables.get('result') == 2:
            return {
                "status": "healthy",
                "message": "Python interpreter service is working correctly"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Python interpreter service test failed"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Python interpreter service error: {str(e)}"
        }