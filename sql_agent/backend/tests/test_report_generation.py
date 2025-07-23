"""
Tests for the Report Generation Service

This module contains tests for the report generation functionality.
"""

import os
import json
import time
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Add parent directory to path to import services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_generation import (
    ReportSection, Report, ReportTemplate, ReportGenerator, ReportStorageService
)
from services.data_visualization import Visualization
from services.data_analysis import AnalysisResult


class TestReportSection(unittest.TestCase):
    """Tests for the ReportSection class"""
    
    def test_report_section_creation(self):
        """Test creating a report section"""
        section = ReportSection(
            title="Test Section",
            content="This is a test section"
        )
        
        self.assertEqual(section.title, "Test Section")
        self.assertEqual(section.content, "This is a test section")
        self.assertEqual(len(section.visualizations), 0)
        self.assertEqual(len(section.subsections), 0)
        self.assertEqual(len(section.metadata), 0)
    
    def test_report_section_with_visualizations(self):
        """Test creating a report section with visualizations"""
        viz = Visualization.create(
            title="Test Visualization",
            chart_type="bar",
            data="test_data",
            format="png"
        )
        
        section = ReportSection(
            title="Test Section",
            content="This is a test section",
            visualizations=[viz]
        )
        
        self.assertEqual(len(section.visualizations), 1)
        self.assertEqual(section.visualizations[0].title, "Test Visualization")
    
    def test_report_section_with_subsections(self):
        """Test creating a report section with subsections"""
        subsection = ReportSection(
            title="Test Subsection",
            content="This is a test subsection"
        )
        
        section = ReportSection(
            title="Test Section",
            content="This is a test section",
            subsections=[subsection]
        )
        
        self.assertEqual(len(section.subsections), 1)
        self.assertEqual(section.subsections[0].title, "Test Subsection")


class TestReport(unittest.TestCase):
    """Tests for the Report class"""
    
    def test_report_creation(self):
        """Test creating a report"""
        report = Report.create(
            title="Test Report",
            description="This is a test report",
            author="Test Author"
        )
        
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.description, "This is a test report")
        self.assertEqual(report.author, "Test Author")
        self.assertEqual(len(report.sections), 0)
        self.assertEqual(len(report.metadata), 0)
        self.assertIsNotNone(report.id)
        self.assertIsNotNone(report.created_at)
        self.assertIsNotNone(report.updated_at)
    
    def test_report_with_sections(self):
        """Test creating a report with sections"""
        section = ReportSection(
            title="Test Section",
            content="This is a test section"
        )
        
        report = Report.create(
            title="Test Report",
            description="This is a test report"
        )
        report.sections.append(section)
        
        self.assertEqual(len(report.sections), 1)
        self.assertEqual(report.sections[0].title, "Test Section")


class TestReportTemplate(unittest.TestCase):
    """Tests for the ReportTemplate class"""
    
    def test_default_template(self):
        """Test creating a default template"""
        template = ReportTemplate.create_default_template()
        
        self.assertIn("title_format", template)
        self.assertIn("section_title_format", template)
        self.assertIn("css_styles", template)
        self.assertTrue(template["include_table_of_contents"])
    
    def test_minimal_template(self):
        """Test creating a minimal template"""
        template = ReportTemplate.create_minimal_template()
        
        self.assertIn("title_format", template)
        self.assertIn("section_title_format", template)
        self.assertIn("css_styles", template)
        self.assertFalse(template["include_table_of_contents"])
    
    def test_technical_template(self):
        """Test creating a technical template"""
        template = ReportTemplate.create_technical_template()
        
        self.assertIn("title_format", template)
        self.assertTrue("Technical Report" in template["title_format"])
        self.assertTrue(template["include_table_of_contents"])
    
    def test_executive_template(self):
        """Test creating an executive template"""
        template = ReportTemplate.create_executive_template()
        
        self.assertIn("title_format", template)
        self.assertTrue("Executive Summary" in template["title_format"])
        self.assertFalse(template["include_table_of_contents"])


class TestReportGenerator(unittest.TestCase):
    """Tests for the ReportGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a sample visualization
        plt.figure(figsize=(6, 4))
        plt.plot([1, 2, 3, 4], [10, 20, 25, 30])
        plt.title("Test Plot")
        plt.xlabel("X")
        plt.ylabel("Y")
        
        # Save figure to bytes
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        # Encode as base64
        self.test_image_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Create a sample analysis result
        self.analysis_result = AnalysisResult(
            success=True,
            data=pd.DataFrame({
                'A': [1, 2, 3, 4],
                'B': [10, 20, 25, 30]
            }),
            summary={
                "shape": (4, 2),
                "columns": {
                    "A": {"type": "int", "missing_percent": 0},
                    "B": {"type": "int", "missing_percent": 0}
                },
                "correlations": {
                    "top_correlations": [
                        {"column1": "A", "column2": "B", "correlation": 0.95}
                    ]
                }
            },
            plots=[
                {
                    "type": "line",
                    "title": "Test Plot",
                    "data": self.test_image_data,
                    "format": "png"
                }
            ]
        )
        
        # Create a sample execution result
        self.execution_result = {
            "execution_id": "test_id",
            "status": "completed",
            "output": "Test output",
            "error": None,
            "variables": {
                "df": pd.DataFrame({
                    'A': [1, 2, 3, 4],
                    'B': [10, 20, 25, 30]
                })
            },
            "plots": [
                {
                    "type": "matplotlib",
                    "title": "Test Plot",
                    "data": self.test_image_data,
                    "format": "png"
                }
            ],
            "analysis_results": {
                "df": {
                    "summary": {
                        "shape": (4, 2)
                    },
                    "insights": ["Positive correlation between A and B"]
                }
            },
            "execution_time": 1.5,
            "memory_usage": 50.0
        }
    
    def test_create_report_from_analysis(self):
        """Test creating a report from analysis result"""
        report = ReportGenerator.create_report_from_analysis(
            title="Analysis Report",
            analysis_result=self.analysis_result
        )
        
        self.assertEqual(report.title, "Analysis Report")
        self.assertGreaterEqual(len(report.sections), 1)
        self.assertEqual(report.metadata["analysis_type"], "automated")
    
    def test_create_report_from_execution_result(self):
        """Test creating a report from execution result"""
        report = ReportGenerator.create_report_from_execution_result(
            title="Execution Report",
            execution_result=self.execution_result
        )
        
        self.assertEqual(report.title, "Execution Report")
        self.assertGreaterEqual(len(report.sections), 1)
        self.assertEqual(report.metadata["execution_time"], 1.5)
    
    def test_create_custom_report(self):
        """Test creating a custom report"""
        sections = [
            {
                "title": "Section 1",
                "content": "Content 1",
                "visualizations": [
                    {
                        "title": "Viz 1",
                        "chart_type": "bar",
                        "data": self.test_image_data,
                        "format": "png"
                    }
                ]
            },
            {
                "title": "Section 2",
                "content": "Content 2",
                "subsections": [
                    {
                        "title": "Subsection 2.1",
                        "content": "Subcontent 2.1"
                    }
                ]
            }
        ]
        
        report = ReportGenerator.create_custom_report(
            title="Custom Report",
            sections=sections,
            description="Custom description"
        )
        
        self.assertEqual(report.title, "Custom Report")
        self.assertEqual(report.description, "Custom description")
        self.assertEqual(len(report.sections), 2)
        self.assertEqual(len(report.sections[0].visualizations), 1)
        self.assertEqual(len(report.sections[1].subsections), 1)
    
    def test_render_report_markdown(self):
        """Test rendering a report as markdown"""
        report = ReportGenerator.create_custom_report(
            title="Test Report",
            sections=[
                {
                    "title": "Section 1",
                    "content": "Content 1"
                }
            ]
        )
        
        markdown = ReportGenerator.render_report_markdown(report)
        
        self.assertIn("# Test Report", markdown)
        self.assertIn("## Section 1", markdown)
        self.assertIn("Content 1", markdown)
    
    def test_render_report_html(self):
        """Test rendering a report as HTML"""
        report = ReportGenerator.create_custom_report(
            title="Test Report",
            sections=[
                {
                    "title": "Section 1",
                    "content": "Content 1"
                }
            ]
        )
        
        html = ReportGenerator.render_report_html(report)
        
        self.assertIn("<html>", html)
        self.assertIn("<title>Test Report</title>", html)
        self.assertIn("<h1>Test Report</h1>", html)
        self.assertIn("<h2", html)
        self.assertIn("Content 1", html)


class TestReportStorageService(unittest.TestCase):
    """Tests for the ReportStorageService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage_service = ReportStorageService(self.test_dir)
        
        # Create a sample report
        self.report = Report.create(
            title="Test Report",
            description="Test Description",
            author="Test Author"
        )
        self.report.sections.append(
            ReportSection(
                title="Test Section",
                content="Test Content"
            )
        )
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_save_and_get_report(self):
        """Test saving and retrieving a report"""
        # Save the report
        report_id = self.storage_service.save_report(self.report)
        
        # Check that the report files were created
        report_dir = os.path.join(self.test_dir, report_id)
        self.assertTrue(os.path.exists(report_dir))
        self.assertTrue(os.path.exists(os.path.join(report_dir, "report.json")))
        self.assertTrue(os.path.exists(os.path.join(report_dir, "report.md")))
        self.assertTrue(os.path.exists(os.path.join(report_dir, "report.html")))
        
        # Get the report
        retrieved_report = self.storage_service.get_report(report_id)
        
        # Check that the retrieved report matches the original
        self.assertEqual(retrieved_report.id, self.report.id)
        self.assertEqual(retrieved_report.title, self.report.title)
        self.assertEqual(retrieved_report.description, self.report.description)
        self.assertEqual(retrieved_report.author, self.report.author)
        self.assertEqual(len(retrieved_report.sections), 1)
        self.assertEqual(retrieved_report.sections[0].title, "Test Section")
        self.assertEqual(retrieved_report.sections[0].content, "Test Content")
    
    def test_list_reports(self):
        """Test listing reports"""
        # Save multiple reports
        self.storage_service.save_report(self.report)
        
        report2 = Report.create(
            title="Test Report 2",
            description="Test Description 2"
        )
        self.storage_service.save_report(report2)
        
        # List reports
        reports = self.storage_service.list_reports()
        
        # Check that both reports are listed
        self.assertEqual(len(reports), 2)
        self.assertTrue(any(r["title"] == "Test Report" for r in reports))
        self.assertTrue(any(r["title"] == "Test Report 2" for r in reports))
    
    def test_delete_report(self):
        """Test deleting a report"""
        # Save the report
        report_id = self.storage_service.save_report(self.report)
        
        # Delete the report
        result = self.storage_service.delete_report(report_id)
        
        # Check that the report was deleted
        self.assertTrue(result)
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, report_id)))
        
        # Check that the report is no longer retrievable
        retrieved_report = self.storage_service.get_report(report_id)
        self.assertIsNone(retrieved_report)
    
    def test_delete_nonexistent_report(self):
        """Test deleting a nonexistent report"""
        result = self.storage_service.delete_report("nonexistent_id")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()