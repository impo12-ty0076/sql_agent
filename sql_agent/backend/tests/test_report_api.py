"""
Tests for the Report API

This module contains tests for the report API endpoints.
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
from fastapi.testclient import TestClient

# Add parent directory to path to import services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from services.report_generation import (
    ReportSection, Report, ReportTemplate, ReportGenerator, ReportStorageService
)


class TestReportAPI(unittest.TestCase):
    """Tests for the Report API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample base64 image
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
        self.analysis_result = {
            "success": True,
            "summary": {
                "shape": [4, 2],
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
            "plots": [
                {
                    "type": "line",
                    "title": "Test Plot",
                    "data": self.test_image_data,
                    "format": "png"
                }
            ]
        }
        
        # Create a sample execution result
        self.execution_result = {
            "execution_id": "test_id",
            "status": "completed",
            "output": "Test output",
            "error": None,
            "variables": {
                "df": {
                    "A": [1, 2, 3, 4],
                    "B": [10, 20, 25, 30]
                }
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
                        "shape": [4, 2]
                    },
                    "insights": ["Positive correlation between A and B"]
                }
            },
            "execution_time": 1.5,
            "memory_usage": 50.0
        }
        
        # Patch the ReportStorageService to use the test directory
        self.patcher = patch('api.report_api.report_storage_service', 
                            ReportStorageService(self.test_dir))
        self.mock_storage_service = self.patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop the patcher
        self.patcher.stop()
        
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_create_custom_report(self):
        """Test creating a custom report"""
        # Create a custom report request
        request_data = {
            "title": "Test Custom Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": [
                {
                    "title": "Test Section",
                    "content": "Test Content",
                    "visualizations": [
                        {
                            "title": "Test Visualization",
                            "chart_type": "bar",
                            "data": self.test_image_data,
                            "format": "png"
                        }
                    ]
                }
            ]
        }
        
        # Send request
        response = self.client.post("/api/reports/custom", json=request_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Custom Report")
        self.assertEqual(data["description"], "Test Description")
        self.assertEqual(data["author"], "Test Author")
        self.assertIn("id", data)
    
    def test_create_report_from_analysis(self):
        """Test creating a report from analysis results"""
        # Create a report from analysis request
        request_data = {
            "title": "Test Analysis Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "analysis_result": self.analysis_result
        }
        
        # Send request
        response = self.client.post("/api/reports/from-analysis", json=request_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Analysis Report")
        self.assertEqual(data["description"], "Test Description")
        self.assertEqual(data["author"], "Test Author")
        self.assertIn("id", data)
    
    def test_create_report_from_execution(self):
        """Test creating a report from execution results"""
        # Create a report from execution request
        request_data = {
            "title": "Test Execution Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "execution_result": self.execution_result
        }
        
        # Send request
        response = self.client.post("/api/reports/from-execution", json=request_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Execution Report")
        self.assertEqual(data["description"], "Test Description")
        self.assertEqual(data["author"], "Test Author")
        self.assertIn("id", data)
    
    def test_list_reports(self):
        """Test listing reports"""
        # Create a report first
        request_data = {
            "title": "Test Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": []
        }
        create_response = self.client.post("/api/reports/custom", json=request_data)
        self.assertEqual(create_response.status_code, 200)
        
        # List reports
        response = self.client.get("/api/reports/")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test Report")
    
    def test_get_report(self):
        """Test getting a report by ID"""
        # Create a report first
        request_data = {
            "title": "Test Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": [
                {
                    "title": "Test Section",
                    "content": "Test Content"
                }
            ]
        }
        create_response = self.client.post("/api/reports/custom", json=request_data)
        self.assertEqual(create_response.status_code, 200)
        report_id = create_response.json()["id"]
        
        # Get report
        response = self.client.get(f"/api/reports/{report_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], report_id)
        self.assertEqual(data["title"], "Test Report")
        self.assertEqual(data["description"], "Test Description")
        self.assertEqual(data["author"], "Test Author")
        self.assertEqual(len(data["sections"]), 1)
        self.assertEqual(data["sections"][0]["title"], "Test Section")
        self.assertEqual(data["sections"][0]["content"], "Test Content")
    
    def test_get_report_markdown(self):
        """Test getting a report as markdown"""
        # Create a report first
        request_data = {
            "title": "Test Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": [
                {
                    "title": "Test Section",
                    "content": "Test Content"
                }
            ]
        }
        create_response = self.client.post("/api/reports/custom", json=request_data)
        self.assertEqual(create_response.status_code, 200)
        report_id = create_response.json()["id"]
        
        # Get report markdown
        response = self.client.get(f"/api/reports/{report_id}/markdown")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("# Test Report", response.text)
        self.assertIn("## Test Section", response.text)
        self.assertIn("Test Content", response.text)
    
    def test_get_report_html(self):
        """Test getting a report as HTML"""
        # Create a report first
        request_data = {
            "title": "Test Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": [
                {
                    "title": "Test Section",
                    "content": "Test Content"
                }
            ]
        }
        create_response = self.client.post("/api/reports/custom", json=request_data)
        self.assertEqual(create_response.status_code, 200)
        report_id = create_response.json()["id"]
        
        # Get report HTML
        response = self.client.get(f"/api/reports/{report_id}/html")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/html; charset=utf-8")
        self.assertIn("<html>", response.text)
        self.assertIn("<title>Test Report</title>", response.text)
        self.assertIn("<h1>Test Report</h1>", response.text)
        self.assertIn("<h2", response.text)
        self.assertIn("Test Content", response.text)
    
    def test_delete_report(self):
        """Test deleting a report"""
        # Create a report first
        request_data = {
            "title": "Test Report",
            "description": "Test Description",
            "author": "Test Author",
            "template_type": "default",
            "sections": []
        }
        create_response = self.client.post("/api/reports/custom", json=request_data)
        self.assertEqual(create_response.status_code, 200)
        report_id = create_response.json()["id"]
        
        # Delete report
        response = self.client.delete(f"/api/reports/{report_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("deleted successfully", data["message"])
        
        # Try to get the deleted report
        get_response = self.client.get(f"/api/reports/{report_id}")
        self.assertEqual(get_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()