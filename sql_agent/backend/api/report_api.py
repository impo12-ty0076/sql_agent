"""
Report Generation API

This module provides API endpoints for report generation, management, and retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import FileResponse, HTMLResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import time
import json
from datetime import datetime

from ..services.report_generation import (
    Report, ReportSection, ReportGenerator, ReportStorageService, 
    report_storage_service
)
from ..services.data_analysis import AnalysisResult
from ..services.data_visualization import Visualization
from ..services.python_interpreter_enhanced import ExecutionResult, ExecutionStatus


# Pydantic models for API
class VisualizationModel(BaseModel):
    """API model for visualization data"""
    title: str
    chart_type: str
    data: str
    format: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReportSectionModel(BaseModel):
    """API model for report section data"""
    title: str
    content: str
    visualizations: List[VisualizationModel] = Field(default_factory=list)
    subsections: List['ReportSectionModel'] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateReportRequest(BaseModel):
    """API model for creating a custom report"""
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    template_type: str = "default"
    sections: List[ReportSectionModel] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReportFromAnalysisRequest(BaseModel):
    """API model for creating a report from analysis results"""
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    template_type: str = "default"
    analysis_result: Dict[str, Any]


class ReportFromExecutionRequest(BaseModel):
    """API model for creating a report from execution results"""
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    template_type: str = "default"
    execution_result: Dict[str, Any]


class ReportMetadataResponse(BaseModel):
    """API model for report metadata response"""
    id: str
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: float
    updated_at: float


class ReportResponse(BaseModel):
    """API model for full report response"""
    id: str
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: float
    updated_at: float
    sections: List[ReportSectionModel]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Create router
router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)


@router.post("/custom", response_model=ReportMetadataResponse)
async def create_custom_report(request: CreateReportRequest):
    """Create a custom report"""
    try:
        # Convert API models to service models
        sections = []
        for section_model in request.sections:
            section = _convert_section_model_to_section(section_model)
            sections.append(section)
        
        # Create report
        report = ReportGenerator.create_custom_report(
            title=request.title,
            sections=[_section_to_dict(section) for section in sections],
            template_type=request.template_type,
            description=request.description,
            author=request.author,
            metadata=request.metadata
        )
        
        # Save report
        report_id = report_storage_service.save_report(report)
        
        return {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "author": report.author,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.post("/from-analysis", response_model=ReportMetadataResponse)
async def create_report_from_analysis(request: ReportFromAnalysisRequest):
    """Create a report from analysis results"""
    try:
        # Convert dictionary to AnalysisResult
        analysis_result = AnalysisResult(
            success=True,
            data=None,  # We don't need the actual DataFrame for report generation
            summary=request.analysis_result.get("summary"),
            plots=request.analysis_result.get("plots", []),
            error=request.analysis_result.get("error")
        )
        
        # Create report
        report = ReportGenerator.create_report_from_analysis(
            title=request.title,
            analysis_result=analysis_result,
            template_type=request.template_type,
            description=request.description,
            author=request.author
        )
        
        # Save report
        report_id = report_storage_service.save_report(report)
        
        return {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "author": report.author,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.post("/from-execution", response_model=ReportMetadataResponse)
async def create_report_from_execution(request: ReportFromExecutionRequest):
    """Create a report from execution results"""
    try:
        # Create report
        report = ReportGenerator.create_report_from_execution_result(
            title=request.title,
            execution_result=request.execution_result,
            template_type=request.template_type,
            description=request.description,
            author=request.author
        )
        
        # Save report
        report_id = report_storage_service.save_report(report)
        
        return {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "author": report.author,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.get("/", response_model=List[ReportMetadataResponse])
async def list_reports():
    """List all reports"""
    try:
        reports = report_storage_service.list_reports()
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str = Path(..., description="The ID of the report to retrieve")):
    """Get a report by ID"""
    try:
        report = report_storage_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Convert to API response model
        sections = []
        for section in report.sections:
            sections.append(_convert_section_to_model(section))
        
        return {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "author": report.author,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "sections": sections,
            "metadata": report.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/{report_id}/markdown")
async def get_report_markdown(
    report_id: str = Path(..., description="The ID of the report to retrieve"),
    download: bool = Query(False, description="Whether to download the file")
):
    """Get a report as markdown"""
    try:
        report = report_storage_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Get markdown file path
        report_dir = os.path.join(report_storage_service.storage_dir, report_id)
        markdown_path = os.path.join(report_dir, "report.md")
        
        if not os.path.exists(markdown_path):
            # Generate markdown if file doesn't exist
            markdown_content = ReportGenerator.render_report_markdown(
                report, report.metadata.get("template_type", "default")
            )
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        # Return file
        filename = f"{report.title.replace(' ', '_')}.md" if download else None
        return FileResponse(
            path=markdown_path,
            media_type="text/markdown",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report markdown: {str(e)}")


@router.get("/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(
    report_id: str = Path(..., description="The ID of the report to retrieve"),
    download: bool = Query(False, description="Whether to download the file")
):
    """Get a report as HTML"""
    try:
        report = report_storage_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # Get HTML file path
        report_dir = os.path.join(report_storage_service.storage_dir, report_id)
        html_path = os.path.join(report_dir, "report.html")
        
        if not os.path.exists(html_path):
            # Generate HTML if file doesn't exist
            html_content = ReportGenerator.render_report_html(
                report, report.metadata.get("template_type", "default")
            )
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        # Return file
        if download:
            filename = f"{report.title.replace(' ', '_')}.html"
            return FileResponse(
                path=html_path,
                media_type="text/html",
                filename=filename
            )
        else:
            # Read and return HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report HTML: {str(e)}")


@router.delete("/{report_id}")
async def delete_report(report_id: str = Path(..., description="The ID of the report to delete")):
    """Delete a report"""
    try:
        success = report_storage_service.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        return {"message": f"Report {report_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


# Helper functions
def _convert_section_model_to_section(model: ReportSectionModel) -> ReportSection:
    """Convert a section model to a section object"""
    section = ReportSection(
        title=model.title,
        content=model.content,
        metadata=model.metadata
    )
    
    # Add visualizations
    for viz_model in model.visualizations:
        section.visualizations.append(
            Visualization.create(
                title=viz_model.title,
                chart_type=viz_model.chart_type,
                data=viz_model.data,
                format=viz_model.format,
                description=viz_model.description,
                metadata=viz_model.metadata
            )
        )
    
    # Add subsections
    for subsection_model in model.subsections:
        section.subsections.append(_convert_section_model_to_section(subsection_model))
    
    return section


def _convert_section_to_model(section: ReportSection) -> ReportSectionModel:
    """Convert a section object to a section model"""
    visualizations = []
    for viz in section.visualizations:
        visualizations.append(
            VisualizationModel(
                title=viz.title,
                chart_type=viz.chart_type,
                data=viz.data,
                format=viz.format,
                description=viz.description,
                metadata=viz.metadata
            )
        )
    
    subsections = []
    for subsection in section.subsections:
        subsections.append(_convert_section_to_model(subsection))
    
    return ReportSectionModel(
        title=section.title,
        content=section.content,
        visualizations=visualizations,
        subsections=subsections,
        metadata=section.metadata
    )


def _section_to_dict(section: ReportSection) -> Dict[str, Any]:
    """Convert a section object to a dictionary"""
    return {
        "title": section.title,
        "content": section.content,
        "visualizations": [
            {
                "title": viz.title,
                "chart_type": viz.chart_type,
                "data": viz.data,
                "format": viz.format,
                "description": viz.description,
                "metadata": viz.metadata
            }
            for viz in section.visualizations
        ],
        "subsections": [_section_to_dict(subsection) for subsection in section.subsections],
        "metadata": section.metadata
    }