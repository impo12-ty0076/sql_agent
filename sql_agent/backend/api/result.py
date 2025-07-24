"""
Result Processing and Display API

This module provides API endpoints for query result processing, formatting, pagination,
summary generation, and report creation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

from ..services.query_execution_service import QueryExecutionService
from ..db.crud.query_result import get_query_result_by_id, update_query_result_summary
from ..services.report_generation import ReportGenerator, report_storage_service
from ..llm.factory import get_llm_service
from ..llm.result_summary_service import ResultSummaryService
from ..core.auth import get_current_user_id

# Pydantic models for API
class PaginationParams(BaseModel):
    """API model for pagination parameters"""
    page: int = Field(1, description="Page number (1-indexed)")
    page_size: int = Field(100, description="Number of rows per page")
    sort_column: Optional[str] = Field(None, description="Column to sort by")
    sort_direction: Optional[str] = Field("asc", description="Sort direction (asc or desc)")


class ResultSummaryRequest(BaseModel):
    """API model for requesting a result summary"""
    result_id: str
    summary_type: str = Field("basic", description="Type of summary to generate (basic, detailed)")
    include_insights: bool = Field(True, description="Whether to include insights in the summary")


class CreateReportFromResultRequest(BaseModel):
    """API model for creating a report from query results"""
    result_id: str
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    template_type: str = "default"
    include_summary: bool = Field(True, description="Whether to include summary in the report")
    include_visualizations: bool = Field(True, description="Whether to include visualizations in the report")


class ReportGenerationStatusResponse(BaseModel):
    """API model for report generation status response"""
    task_id: str
    status: str
    report_id: Optional[str] = None
    progress: float = Field(0.0, description="Progress percentage (0-100)")
    message: Optional[str] = None
    error: Optional[str] = None


# Create router
router = APIRouter(
    prefix="/result",
    tags=["result"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Service instances
query_execution_service = QueryExecutionService()
llm_service = get_llm_service()
result_summary_service = ResultSummaryService(llm_service)

# Dictionary to track report generation tasks
report_generation_tasks = {}


@router.get("/{result_id}")
async def get_result(
    result_id: str = Path(..., description="The ID of the result to retrieve"),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 결과 조회
    
    이 엔드포인트는 지정된 결과 ID에 대한 전체 쿼리 결과 데이터를 조회합니다.
    """
    try:
        # Get current user ID
        user_id = await get_current_user_id(token)
        
        # Get result from database
        result = await get_query_result_by_id(result_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Result with ID {result_id} not found")
        
        # Check if user has permission to access this result
        # In a real implementation, we would check if the result belongs to the user
        # For now, we'll assume the user has permission
        
        # Build response
        response = {
            "result_id": result.id,
            "query_id": result.query_id,
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "truncated": result.truncated,
            "total_row_count": result.total_row_count,
            "summary": result.summary,
            "created_at": result.created_at.isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.post("/{result_id}/paginated")
async def get_paginated_result(
    pagination: PaginationParams,
    result_id: str = Path(..., description="The ID of the result to retrieve"),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    페이지네이션된 쿼리 결과 조회
    
    이 엔드포인트는 지정된 결과 ID에 대한 쿼리 결과 데이터를 페이지네이션하여 조회합니다.
    """
    try:
        # Get current user ID
        user_id = await get_current_user_id(token)
        
        # Get result from database
        result = await get_query_result_by_id(result_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Result with ID {result_id} not found")
        
        # Check if user has permission to access this result
        # In a real implementation, we would check if the result belongs to the user
        # For now, we'll assume the user has permission
        
        # Calculate pagination
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        
        # Sort if requested
        rows = result.rows
        if pagination.sort_column is not None:
            try:
                # Find the index of the sort column
                col_idx = next((i for i, col in enumerate(result.columns) if col["name"] == pagination.sort_column), None)
                if col_idx is not None:
                    # Sort the rows
                    reverse = pagination.sort_direction.lower() == "desc"
                    rows = sorted(rows, key=lambda row: row[col_idx] if row[col_idx] is not None else "", reverse=reverse)
            except Exception as e:
                # If sorting fails, just use the original order
                pass
        
        # Get the paginated subset of rows
        paginated_rows = rows[start_idx:end_idx] if start_idx < len(rows) else []
        
        # Calculate total pages
        total_pages = (result.row_count + pagination.page_size - 1) // pagination.page_size
        
        # Build response
        response = {
            "result_id": result.id,
            "query_id": result.query_id,
            "columns": result.columns,
            "rows": paginated_rows,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages,
            "total_rows": result.row_count,
            "truncated": result.truncated,
            "total_row_count": result.total_row_count,
            "sort_column": pagination.sort_column,
            "sort_direction": pagination.sort_direction
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get paginated result: {str(e)}")


@router.post("/{result_id}/summary")
async def generate_result_summary(
    request: ResultSummaryRequest,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 결과 요약 생성
    
    이 엔드포인트는 쿼리 결과 데이터에 대한 자연어 요약을 생성합니다.
    """
    try:
        # Get current user ID
        user_id = await get_current_user_id(token)
        
        # Get result from database
        result = await get_query_result_by_id(request.result_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Result with ID {request.result_id} not found")
        
        # Check if user has permission to access this result
        # In a real implementation, we would check if the result belongs to the user
        # For now, we'll assume the user has permission
        
        # Check if summary already exists
        if result.summary:
            return {
                "result_id": result.id,
                "summary": result.summary,
                "generated_now": False
            }
        
        # Generate summary
        summary = await result_summary_service.generate_summary(
            columns=result.columns,
            rows=result.rows,
            summary_type=request.summary_type,
            include_insights=request.include_insights
        )
        
        # Update result with summary
        updated_result = await update_query_result_summary(result.id, summary)
        
        return {
            "result_id": result.id,
            "summary": summary,
            "generated_now": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.post("/report")
async def create_report_from_result(
    request: CreateReportFromResultRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    쿼리 결과로부터 리포트 생성
    
    이 엔드포인트는 쿼리 결과 데이터로부터 리포트를 생성합니다. 리포트 생성은
    백그라운드 작업으로 수행되며, 상태는 /report-status/{task_id} 엔드포인트를 통해
    확인할 수 있습니다.
    """
    try:
        # Get current user ID
        user_id = await get_current_user_id(token)
        
        # Get result from database
        result = await get_query_result_by_id(request.result_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Result with ID {request.result_id} not found")
        
        # Check if user has permission to access this result
        # In a real implementation, we would check if the result belongs to the user
        # For now, we'll assume the user has permission
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        report_generation_tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Report generation task created",
            "report_id": None,
            "error": None
        }
        
        # Add background task
        background_tasks.add_task(
            _generate_report_background_task,
            task_id=task_id,
            result=result,
            title=request.title,
            description=request.description,
            author=request.author,
            template_type=request.template_type,
            include_summary=request.include_summary,
            include_visualizations=request.include_visualizations
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Report generation started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.get("/report-status/{task_id}")
async def get_report_generation_status(
    task_id: str = Path(..., description="The ID of the report generation task"),
    token: str = Depends(oauth2_scheme)
) -> ReportGenerationStatusResponse:
    """
    리포트 생성 작업 상태 조회
    
    이 엔드포인트는 리포트 생성 작업의 상태를 조회합니다.
    """
    try:
        # Get current user ID
        user_id = await get_current_user_id(token)
        
        # Check if task exists
        if task_id not in report_generation_tasks:
            raise HTTPException(status_code=404, detail=f"Report generation task {task_id} not found")
        
        # Get task status
        task_status = report_generation_tasks[task_id]
        
        return ReportGenerationStatusResponse(
            task_id=task_id,
            status=task_status["status"],
            report_id=task_status["report_id"],
            progress=task_status["progress"],
            message=task_status["message"],
            error=task_status["error"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report generation status: {str(e)}")


async def _generate_report_background_task(
    task_id: str,
    result: Any,
    title: str,
    description: Optional[str],
    author: Optional[str],
    template_type: str,
    include_summary: bool,
    include_visualizations: bool
) -> None:
    """
    Background task for generating a report from a query result
    
    Args:
        task_id: Task ID
        result: Query result
        title: Report title
        description: Report description
        author: Report author
        template_type: Report template type
        include_summary: Whether to include summary
        include_visualizations: Whether to include visualizations
    """
    try:
        # Update task status
        report_generation_tasks[task_id]["status"] = "processing"
        report_generation_tasks[task_id]["progress"] = 10.0
        report_generation_tasks[task_id]["message"] = "Processing query result data"
        
        # Prepare data for report
        columns = result.columns
        rows = result.rows
        
        # Generate summary if needed and not already available
        summary = result.summary
        if include_summary and not summary:
            report_generation_tasks[task_id]["progress"] = 20.0
            report_generation_tasks[task_id]["message"] = "Generating result summary"
            
            summary = await result_summary_service.generate_summary(
                columns=columns,
                rows=rows,
                summary_type="detailed",
                include_insights=True
            )
            
            # Update result with summary
            await update_query_result_summary(result.id, summary)
        
        # Generate visualizations if needed
        visualizations = []
        if include_visualizations:
            report_generation_tasks[task_id]["progress"] = 40.0
            report_generation_tasks[task_id]["message"] = "Generating visualizations"
            
            # In a real implementation, we would generate visualizations here
            # For now, we'll skip this step
        
        # Create report
        report_generation_tasks[task_id]["progress"] = 60.0
        report_generation_tasks[task_id]["message"] = "Creating report"
        
        # Prepare analysis result for report generation
        analysis_result = {
            "summary": summary,
            "plots": visualizations
        }
        
        # Create report
        report = ReportGenerator.create_report_from_analysis(
            title=title,
            analysis_result={
                "summary": summary,
                "plots": visualizations,
                "error": None
            },
            template_type=template_type,
            description=description,
            author=author
        )
        
        # Save report
        report_generation_tasks[task_id]["progress"] = 80.0
        report_generation_tasks[task_id]["message"] = "Saving report"
        
        report_id = report_storage_service.save_report(report)
        
        # Update task status
        report_generation_tasks[task_id]["status"] = "completed"
        report_generation_tasks[task_id]["progress"] = 100.0
        report_generation_tasks[task_id]["message"] = "Report generation completed"
        report_generation_tasks[task_id]["report_id"] = report.id
        
    except Exception as e:
        # Update task status with error
        report_generation_tasks[task_id]["status"] = "failed"
        report_generation_tasks[task_id]["error"] = str(e)
        report_generation_tasks[task_id]["message"] = f"Report generation failed: {str(e)}"