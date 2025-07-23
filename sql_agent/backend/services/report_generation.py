"""
Report Generation Service

This module provides utilities for creating, formatting, and managing reports
that combine data analysis results, visualizations, and insights.
"""

import os
import time
import uuid
import json
import base64
from typing import Dict, Any, List, Union, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO, StringIO
import matplotlib.pyplot as plt

from .data_visualization import Visualization, VisualizationService
from .data_analysis import AnalysisResult


@dataclass
class ReportSection:
    """Represents a section in a report"""
    title: str
    content: str
    visualizations: List[Visualization] = field(default_factory=list)
    subsections: List['ReportSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Represents a complete report with metadata and sections"""
    id: str
    title: str
    description: Optional[str]
    created_at: float
    updated_at: float
    author: Optional[str]
    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, title: str, description: Optional[str] = None, author: Optional[str] = None):
        """Create a new report"""
        now = time.time()
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            created_at=now,
            updated_at=now,
            author=author,
            sections=[],
            metadata={}
        )


class ReportTemplate:
    """Base class for report templates"""
    
    @staticmethod
    def create_default_template() -> Dict[str, Any]:
        """Create a default report template structure"""
        return {
            "title_format": "{title}",
            "description_format": "{description}",
            "section_title_format": "## {title}",
            "subsection_title_format": "### {title}",
            "visualization_format": "![{title}](data:{format};base64,{data})",
            "metadata_format": "*{key}: {value}*",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "include_table_of_contents": True,
            "include_metadata": True,
            "include_timestamp": True,
            "css_styles": """
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h1 { color: #2c3e50; }
                h2 { color: #3498db; margin-top: 20px; }
                h3 { color: #2980b9; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                img { max-width: 100%; height: auto; }
                .metadata { color: #7f8c8d; font-size: 0.9em; }
                .toc { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
                .toc ul { list-style-type: none; }
                .toc a { text-decoration: none; color: #3498db; }
                .toc a:hover { text-decoration: underline; }
            """
        }
    
    @staticmethod
    def create_minimal_template() -> Dict[str, Any]:
        """Create a minimal report template structure"""
        return {
            "title_format": "# {title}",
            "description_format": "{description}",
            "section_title_format": "## {title}",
            "subsection_title_format": "### {title}",
            "visualization_format": "![{title}](data:{format};base64,{data})",
            "metadata_format": "*{key}: {value}*",
            "date_format": "%Y-%m-%d",
            "include_table_of_contents": False,
            "include_metadata": False,
            "include_timestamp": True,
            "css_styles": """
                body { font-family: Arial, sans-serif; }
                h1 { margin-bottom: 20px; }
                img { max-width: 100%; }
            """
        }
    
    @staticmethod
    def create_technical_template() -> Dict[str, Any]:
        """Create a technical report template structure"""
        template = ReportTemplate.create_default_template()
        template.update({
            "title_format": "# Technical Report: {title}",
            "section_title_format": "## {title}",
            "include_table_of_contents": True,
            "include_metadata": True,
            "css_styles": """
                body { font-family: 'Courier New', monospace; line-height: 1.6; max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
                h2 { color: #0066cc; margin-top: 30px; border-bottom: 1px solid #ccc; }
                h3 { color: #0099cc; }
                pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
                code { font-family: 'Courier New', monospace; background-color: #f5f5f5; padding: 2px 4px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                img { max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }
                .metadata { color: #666; font-size: 0.9em; background-color: #f9f9f9; padding: 10px; border-radius: 5px; }
                .toc { background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .toc ul { list-style-type: none; }
                .toc a { text-decoration: none; color: #0066cc; }
                .toc a:hover { text-decoration: underline; }
            """
        })
        return template
    
    @staticmethod
    def create_executive_template() -> Dict[str, Any]:
        """Create an executive summary report template structure"""
        template = ReportTemplate.create_default_template()
        template.update({
            "title_format": "# Executive Summary: {title}",
            "description_format": "**{description}**",
            "section_title_format": "## {title}",
            "include_table_of_contents": False,
            "css_styles": """
                body { font-family: 'Arial', sans-serif; line-height: 1.8; max-width: 1000px; margin: 0 auto; color: #333; }
                h1 { color: #1a5276; text-align: center; margin: 30px 0; }
                h2 { color: #2874a6; margin-top: 40px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
                h3 { color: #3498db; }
                p { margin-bottom: 20px; }
                img { max-width: 100%; height: auto; display: block; margin: 20px auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; color: #2874a6; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .highlight { background-color: #ffffcc; padding: 2px; }
                .metadata { color: #7f8c8d; font-size: 0.9em; text-align: right; margin-top: 40px; }
            """
        })
        return template


class ReportGenerator:
    """Service for generating reports from data analysis results and visualizations"""
    
    @staticmethod
    def create_report_from_analysis(
        title: str,
        analysis_result: AnalysisResult,
        template_type: str = "default",
        description: Optional[str] = None,
        author: Optional[str] = None
    ) -> Report:
        """
        Create a report from a data analysis result
        
        Args:
            title: Report title
            analysis_result: Analysis result to include in the report
            template_type: Template type ('default', 'minimal', 'technical', 'executive')
            description: Optional report description
            author: Optional author name
            
        Returns:
            Report object
        """
        report = Report.create(title, description, author)
        
        # Add summary section if available
        if analysis_result.summary:
            summary_section = ReportSection(
                title="Summary",
                content=ReportGenerator._format_summary(analysis_result.summary)
            )
            report.sections.append(summary_section)
        
        # Add visualizations section if available
        if analysis_result.plots and len(analysis_result.plots) > 0:
            viz_section = ReportSection(
                title="Visualizations",
                content="",
                visualizations=[
                    Visualization.create(
                        title=plot.get("title", f"Plot {i+1}"),
                        chart_type=plot.get("type", "unknown"),
                        data=plot.get("data", ""),
                        format=plot.get("format", "png"),
                        description=plot.get("description", None),
                        metadata=plot.get("metadata", {})
                    )
                    for i, plot in enumerate(analysis_result.plots)
                ]
            )
            report.sections.append(viz_section)
        
        # Add metadata
        report.metadata["analysis_type"] = "automated"
        report.metadata["template_type"] = template_type
        
        return report
    
    @staticmethod
    def create_report_from_execution_result(
        title: str,
        execution_result: Dict[str, Any],
        template_type: str = "default",
        description: Optional[str] = None,
        author: Optional[str] = None
    ) -> Report:
        """
        Create a report from a Python execution result
        
        Args:
            title: Report title
            execution_result: Python execution result
            template_type: Template type ('default', 'minimal', 'technical', 'executive')
            description: Optional report description
            author: Optional author name
            
        Returns:
            Report object
        """
        report = Report.create(title, description, author)
        
        # Add code output section
        if execution_result.get("output"):
            output_section = ReportSection(
                title="Code Output",
                content=f"```\n{execution_result['output']}\n```"
            )
            report.sections.append(output_section)
        
        # Add visualizations section if available
        plots = execution_result.get("plots", [])
        if plots and len(plots) > 0:
            viz_section = ReportSection(
                title="Visualizations",
                content="",
                visualizations=[
                    Visualization.create(
                        title=plot.get("title", f"Plot {i+1}"),
                        chart_type=plot.get("type", "unknown"),
                        data=plot.get("data", ""),
                        format=plot.get("format", "png"),
                        description=plot.get("description", None),
                        metadata=plot.get("metadata", {})
                    )
                    for i, plot in enumerate(plots)
                ]
            )
            report.sections.append(viz_section)
        
        # Add analysis results section if available
        analysis_results = execution_result.get("analysis_results", {})
        if analysis_results:
            for var_name, analysis in analysis_results.items():
                if "error" in analysis or "skipped" in analysis:
                    continue
                    
                analysis_section = ReportSection(
                    title=f"Analysis of {var_name}",
                    content=ReportGenerator._format_analysis(analysis)
                )
                
                # Add visualizations from analysis
                if "plots" in analysis:
                    for i, plot in enumerate(analysis["plots"]):
                        analysis_section.visualizations.append(
                            Visualization.create(
                                title=plot.get("title", f"{var_name} Plot {i+1}"),
                                chart_type=plot.get("type", "unknown"),
                                data=plot.get("data", ""),
                                format=plot.get("format", "png"),
                                description=plot.get("description", None),
                                metadata=plot.get("metadata", {})
                            )
                        )
                
                report.sections.append(analysis_section)
        
        # Add error section if there was an error
        if execution_result.get("error"):
            error_section = ReportSection(
                title="Errors",
                content=f"```\n{execution_result['error']}\n```"
            )
            report.sections.append(error_section)
        
        # Add metadata
        report.metadata["execution_time"] = execution_result.get("execution_time", 0)
        report.metadata["memory_usage"] = execution_result.get("memory_usage", 0)
        report.metadata["status"] = execution_result.get("status", "unknown")
        report.metadata["template_type"] = template_type
        
        return report
    
    @staticmethod
    def create_custom_report(
        title: str,
        sections: List[Dict[str, Any]],
        template_type: str = "default",
        description: Optional[str] = None,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Report:
        """
        Create a custom report with specified sections
        
        Args:
            title: Report title
            sections: List of section dictionaries with 'title', 'content', and optional 'visualizations'
            template_type: Template type ('default', 'minimal', 'technical', 'executive')
            description: Optional report description
            author: Optional author name
            metadata: Optional metadata dictionary
            
        Returns:
            Report object
        """
        report = Report.create(title, description, author)
        
        # Add sections
        for section_data in sections:
            section = ReportSection(
                title=section_data["title"],
                content=section_data.get("content", "")
            )
            
            # Add visualizations if provided
            if "visualizations" in section_data:
                for viz_data in section_data["visualizations"]:
                    if isinstance(viz_data, Visualization):
                        section.visualizations.append(viz_data)
                    else:
                        section.visualizations.append(
                            Visualization.create(
                                title=viz_data.get("title", "Visualization"),
                                chart_type=viz_data.get("chart_type", "unknown"),
                                data=viz_data.get("data", ""),
                                format=viz_data.get("format", "png"),
                                description=viz_data.get("description", None),
                                metadata=viz_data.get("metadata", {})
                            )
                        )
            
            # Add subsections if provided
            if "subsections" in section_data:
                for subsection_data in section_data["subsections"]:
                    subsection = ReportSection(
                        title=subsection_data["title"],
                        content=subsection_data.get("content", "")
                    )
                    
                    # Add visualizations to subsection
                    if "visualizations" in subsection_data:
                        for viz_data in subsection_data["visualizations"]:
                            if isinstance(viz_data, Visualization):
                                subsection.visualizations.append(viz_data)
                            else:
                                subsection.visualizations.append(
                                    Visualization.create(
                                        title=viz_data.get("title", "Visualization"),
                                        chart_type=viz_data.get("chart_type", "unknown"),
                                        data=viz_data.get("data", ""),
                                        format=viz_data.get("format", "png"),
                                        description=viz_data.get("description", None),
                                        metadata=viz_data.get("metadata", {})
                                    )
                                )
                    
                    section.subsections.append(subsection)
            
            report.sections.append(section)
        
        # Add metadata
        if metadata:
            report.metadata.update(metadata)
        report.metadata["template_type"] = template_type
        
        return report
    
    @staticmethod
    def _format_summary(summary: Dict[str, Any]) -> str:
        """Format summary data as markdown text"""
        if not summary:
            return ""
            
        lines = []
        
        # Add basic statistics if available
        if "shape" in summary:
            rows, cols = summary["shape"]
            lines.append(f"**Dataset Size:** {rows} rows × {cols} columns\n")
        
        # Add column information if available
        if "columns" in summary:
            lines.append("**Columns:**\n")
            for col, info in summary["columns"].items():
                col_type = info.get("type", "unknown")
                missing = info.get("missing_percent", 0)
                lines.append(f"- **{col}** ({col_type}): {missing:.1f}% missing values")
            lines.append("")
        
        # Add correlation information if available
        if "correlations" in summary and "top_correlations" in summary["correlations"]:
            lines.append("**Top Correlations:**\n")
            for corr in summary["correlations"]["top_correlations"][:5]:  # Top 5
                col1 = corr["column1"]
                col2 = corr["column2"]
                corr_val = corr["correlation"]
                lines.append(f"- {col1} ↔ {col2}: {corr_val:.3f}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_analysis(analysis: Dict[str, Any]) -> str:
        """Format analysis data as markdown text"""
        if not analysis:
            return ""
            
        lines = []
        
        # Add summary if available
        if "summary" in analysis:
            lines.append(ReportGenerator._format_summary(analysis["summary"]))
        
        # Add insights if available
        if "insights" in analysis:
            lines.append("**Key Insights:**\n")
            for insight in analysis["insights"]:
                lines.append(f"- {insight}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def render_report_markdown(
        report: Report,
        template_type: str = "default"
    ) -> str:
        """
        Render a report as markdown
        
        Args:
            report: Report object
            template_type: Template type ('default', 'minimal', 'technical', 'executive')
            
        Returns:
            Markdown string
        """
        # Get template
        if template_type == "minimal":
            template = ReportTemplate.create_minimal_template()
        elif template_type == "technical":
            template = ReportTemplate.create_technical_template()
        elif template_type == "executive":
            template = ReportTemplate.create_executive_template()
        else:
            template = ReportTemplate.create_default_template()
        
        lines = []
        
        # Add title
        title_format = template.get("title_format", "# {title}")
        lines.append(title_format.format(title=report.title))
        lines.append("")
        
        # Add description if available
        if report.description:
            desc_format = template.get("description_format", "{description}")
            lines.append(desc_format.format(description=report.description))
            lines.append("")
        
        # Add timestamp if enabled
        if template.get("include_timestamp", True):
            date_format = template.get("date_format", "%Y-%m-%d %H:%M:%S")
            timestamp = datetime.fromtimestamp(report.created_at).strftime(date_format)
            lines.append(f"*Generated on: {timestamp}*")
            lines.append("")
        
        # Add metadata if enabled
        if template.get("include_metadata", True) and report.metadata:
            lines.append("**Metadata:**")
            metadata_format = template.get("metadata_format", "*{key}: {value}*")
            for key, value in report.metadata.items():
                if key != "template_type":  # Skip template type
                    lines.append(metadata_format.format(key=key, value=value))
            lines.append("")
        
        # Add table of contents if enabled
        if template.get("include_table_of_contents", True) and report.sections:
            lines.append("## Table of Contents")
            for i, section in enumerate(report.sections):
                lines.append(f"{i+1}. [{section.title}](#{section.title.lower().replace(' ', '-')})")
                for j, subsection in enumerate(section.subsections):
                    lines.append(f"   {i+1}.{j+1}. [{subsection.title}](#{subsection.title.lower().replace(' ', '-')})")
            lines.append("")
        
        # Add sections
        for section in report.sections:
            section_title_format = template.get("section_title_format", "## {title}")
            lines.append(section_title_format.format(title=section.title))
            lines.append("")
            
            # Add section content
            if section.content:
                lines.append(section.content)
                lines.append("")
            
            # Add section visualizations
            for viz in section.visualizations:
                viz_format = template.get("visualization_format", "![{title}](data:{format};base64,{data})")
                lines.append(viz_format.format(
                    title=viz.title,
                    format=viz.format,
                    data=viz.data
                ))
                if viz.description:
                    lines.append(f"*{viz.description}*")
                lines.append("")
            
            # Add subsections
            for subsection in section.subsections:
                subsection_title_format = template.get("subsection_title_format", "### {title}")
                lines.append(subsection_title_format.format(title=subsection.title))
                lines.append("")
                
                # Add subsection content
                if subsection.content:
                    lines.append(subsection.content)
                    lines.append("")
                
                # Add subsection visualizations
                for viz in subsection.visualizations:
                    viz_format = template.get("visualization_format", "![{title}](data:{format};base64,{data})")
                    lines.append(viz_format.format(
                        title=viz.title,
                        format=viz.format,
                        data=viz.data
                    ))
                    if viz.description:
                        lines.append(f"*{viz.description}*")
                    lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def render_report_html(
        report: Report,
        template_type: str = "default"
    ) -> str:
        """
        Render a report as HTML
        
        Args:
            report: Report object
            template_type: Template type ('default', 'minimal', 'technical', 'executive')
            
        Returns:
            HTML string
        """
        # First render as markdown
        markdown_content = ReportGenerator.render_report_markdown(report, template_type)
        
        # Get template
        if template_type == "minimal":
            template = ReportTemplate.create_minimal_template()
        elif template_type == "technical":
            template = ReportTemplate.create_technical_template()
        elif template_type == "executive":
            template = ReportTemplate.create_executive_template()
        else:
            template = ReportTemplate.create_default_template()
        
        # Get CSS styles
        css_styles = template.get("css_styles", "")
        
        # Convert markdown to HTML (simplified version)
        # For a real implementation, use a proper markdown to HTML converter like markdown2 or mistune
        html_lines = ["<!DOCTYPE html>", "<html>", "<head>", 
                     f"<title>{report.title}</title>",
                     "<meta charset=\"UTF-8\">",
                     "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
                     f"<style>{css_styles}</style>",
                     "</head>", 
                     "<body>"]
        
        # Very simple markdown to HTML conversion
        # This is a simplified version - in a real implementation, use a proper markdown library
        in_code_block = False
        in_list = False
        
        for line in markdown_content.split("\n"):
            # Headers
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2 id=\"{line[3:].lower().replace(' ', '-')}\">{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3 id=\"{line[4:].lower().replace(' ', '-')}\">{line[4:]}</h3>")
            # Code blocks
            elif line.startswith("```"):
                if in_code_block:
                    html_lines.append("</pre>")
                    in_code_block = False
                else:
                    html_lines.append("<pre>")
                    in_code_block = True
            # Lists
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line[2:]}</li>")
            # End of list
            elif in_list and line.strip() == "":
                html_lines.append("</ul>")
                in_list = False
                html_lines.append("<p></p>")
            # Images
            elif line.startswith("!["):
                # Extract image info using simple regex-like approach
                title_end = line.find("](")
                if title_end > 0:
                    title = line[2:title_end]
                    url_end = line.find(")", title_end)
                    if url_end > 0:
                        url = line[title_end+2:url_end]
                        html_lines.append(f"<img src=\"{url}\" alt=\"{title}\" title=\"{title}\">")
            # Bold text
            elif "**" in line:
                # Very simple bold text handling
                parts = line.split("**")
                html_line = ""
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd parts are bold
                        html_line += f"<strong>{part}</strong>"
                    else:
                        html_line += part
                html_lines.append(f"<p>{html_line}</p>")
            # Italic text
            elif "*" in line and not line.startswith("!["):
                # Very simple italic text handling
                parts = line.split("*")
                html_line = ""
                for i, part in enumerate(parts):
                    if i % 2 == 1 and part:  # Odd non-empty parts are italic
                        html_line += f"<em>{part}</em>"
                    else:
                        html_line += part
                html_lines.append(f"<p>{html_line}</p>")
            # Regular paragraph
            elif line.strip() and not in_code_block:
                html_lines.append(f"<p>{line}</p>")
            # Empty line
            elif not line.strip() and not in_code_block:
                html_lines.append("<p></p>")
            # Code block content
            elif in_code_block:
                html_lines.append(line)
        
        # Close any open tags
        if in_list:
            html_lines.append("</ul>")
        if in_code_block:
            html_lines.append("</pre>")
        
        html_lines.append("</body>")
        html_lines.append("</html>")
        
        return "\n".join(html_lines)
    
    @staticmethod
    def save_report(
        report: Report,
        directory: str,
        format: str = "markdown",
        filename: Optional[str] = None
    ) -> str:
        """
        Save a report to a file
        
        Args:
            report: Report object
            directory: Directory to save the report
            format: Output format ('markdown', 'html')
            filename: Optional filename (uses report ID if None)
            
        Returns:
            Path to the saved file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            extension = "md" if format.lower() == "markdown" else "html"
            filename = f"report_{report.id}.{extension}"
        elif not filename.endswith(".md") and not filename.endswith(".html"):
            extension = "md" if format.lower() == "markdown" else "html"
            filename = f"{filename}.{extension}"
            
        # Full path
        filepath = os.path.join(directory, filename)
        
        # Render report
        if format.lower() == "html":
            content = ReportGenerator.render_report_html(report, report.metadata.get("template_type", "default"))
        else:
            content = ReportGenerator.render_report_markdown(report, report.metadata.get("template_type", "default"))
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return filepath


class ReportStorageService:
    """Service for storing and retrieving reports"""
    
    def __init__(self, storage_dir: str = "reports"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
    def save_report(self, report: Report) -> str:
        """
        Save a report to storage
        
        Args:
            report: Report object
            
        Returns:
            Report ID
        """
        # Update timestamp
        report.updated_at = time.time()
        
        # Save report metadata and structure
        report_data = {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "author": report.author,
            "metadata": report.metadata,
            "sections": [self._serialize_section(section) for section in report.sections]
        }
        
        # Create report directory
        report_dir = os.path.join(self.storage_dir, report.id)
        os.makedirs(report_dir, exist_ok=True)
        
        # Save report data
        with open(os.path.join(report_dir, "report.json"), 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        # Save report as markdown
        markdown_content = ReportGenerator.render_report_markdown(
            report, report.metadata.get("template_type", "default")
        )
        with open(os.path.join(report_dir, "report.md"), 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save report as HTML
        html_content = ReportGenerator.render_report_html(
            report, report.metadata.get("template_type", "default")
        )
        with open(os.path.join(report_dir, "report.html"), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report.id
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """
        Get a report from storage
        
        Args:
            report_id: Report ID
            
        Returns:
            Report object or None if not found
        """
        report_dir = os.path.join(self.storage_dir, report_id)
        report_file = os.path.join(report_dir, "report.json")
        
        if not os.path.exists(report_file):
            return None
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Create report object
            report = Report(
                id=report_data["id"],
                title=report_data["title"],
                description=report_data.get("description"),
                created_at=report_data["created_at"],
                updated_at=report_data["updated_at"],
                author=report_data.get("author"),
                metadata=report_data.get("metadata", {})
            )
            
            # Add sections
            for section_data in report_data.get("sections", []):
                report.sections.append(self._deserialize_section(section_data))
            
            return report
            
        except Exception as e:
            print(f"Error loading report {report_id}: {str(e)}")
            return None
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """
        List all reports in storage
        
        Returns:
            List of report metadata dictionaries
        """
        reports = []
        
        for item in os.listdir(self.storage_dir):
            report_dir = os.path.join(self.storage_dir, item)
            report_file = os.path.join(report_dir, "report.json")
            
            if os.path.isdir(report_dir) and os.path.exists(report_file):
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                    
                    reports.append({
                        "id": report_data["id"],
                        "title": report_data["title"],
                        "description": report_data.get("description"),
                        "created_at": report_data["created_at"],
                        "updated_at": report_data["updated_at"],
                        "author": report_data.get("author")
                    })
                except Exception as e:
                    print(f"Error loading report metadata for {item}: {str(e)}")
        
        # Sort by updated_at (newest first)
        reports.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return reports
    
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report from storage
        
        Args:
            report_id: Report ID
            
        Returns:
            True if deleted, False if not found
        """
        report_dir = os.path.join(self.storage_dir, report_id)
        
        if not os.path.exists(report_dir):
            return False
        
        try:
            # Delete all files in the directory
            for item in os.listdir(report_dir):
                os.remove(os.path.join(report_dir, item))
            
            # Delete the directory
            os.rmdir(report_dir)
            
            return True
        except Exception as e:
            print(f"Error deleting report {report_id}: {str(e)}")
            return False
    
    def _serialize_section(self, section: ReportSection) -> Dict[str, Any]:
        """Serialize a section to a dictionary"""
        return {
            "title": section.title,
            "content": section.content,
            "visualizations": [
                {
                    "id": viz.id,
                    "title": viz.title,
                    "description": viz.description,
                    "chart_type": viz.chart_type,
                    "data": viz.data,
                    "format": viz.format,
                    "metadata": viz.metadata,
                    "timestamp": viz.timestamp
                }
                for viz in section.visualizations
            ],
            "subsections": [self._serialize_section(subsection) for subsection in section.subsections],
            "metadata": section.metadata
        }
    
    def _deserialize_section(self, data: Dict[str, Any]) -> ReportSection:
        """Deserialize a section from a dictionary"""
        section = ReportSection(
            title=data["title"],
            content=data["content"],
            metadata=data.get("metadata", {})
        )
        
        # Add visualizations
        for viz_data in data.get("visualizations", []):
            section.visualizations.append(
                Visualization(
                    id=viz_data["id"],
                    title=viz_data["title"],
                    description=viz_data.get("description"),
                    chart_type=viz_data["chart_type"],
                    data=viz_data["data"],
                    format=viz_data["format"],
                    metadata=viz_data.get("metadata", {}),
                    timestamp=viz_data.get("timestamp", time.time())
                )
            )
        
        # Add subsections
        for subsection_data in data.get("subsections", []):
            section.subsections.append(self._deserialize_section(subsection_data))
        
        return section


# Global service instance
report_storage_service = ReportStorageService()