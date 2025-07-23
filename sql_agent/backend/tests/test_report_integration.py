"""
Integration Tests for Report Generation with Python Interpreter

This module contains integration tests for the report generation functionality
with the Python interpreter service.
"""

import os
import json
import time
import unittest
import tempfile
import shutil
import asyncio
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path to import services
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.python_interpreter_enhanced import EnhancedPythonInterpreterService
from services.report_generation import (
    ReportGenerator, ReportStorageService, Report, ReportSection
)


class TestReportIntegration(unittest.TestCase):
    """Integration tests for report generation with Python interpreter"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage_service = ReportStorageService(self.test_dir)
        
        # Create Python interpreter service
        self.interpreter_service = EnhancedPythonInterpreterService()
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_generate_report_from_python_execution(self):
        """Test generating a report from Python execution results"""
        # Define Python code that generates visualizations
        code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create a sample DataFrame
data = {
    'Category': ['A', 'B', 'C', 'D', 'E'],
    'Values': [10, 25, 15, 30, 20]
}
df = pd.DataFrame(data)

# Create a bar chart
plt.figure(figsize=(8, 5))
plt.bar(df['Category'], df['Values'], color='skyblue')
plt.title('Sample Bar Chart')
plt.xlabel('Category')
plt.ylabel('Values')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Create a second visualization - pie chart
plt.figure(figsize=(8, 5))
plt.pie(df['Values'], labels=df['Category'], autopct='%1.1f%%', 
        startangle=90, shadow=True)
plt.title('Sample Pie Chart')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

# Print some analysis
print("Data Analysis:")
print(f"Total value: {df['Values'].sum()}")
print(f"Average value: {df['Values'].mean():.2f}")
print(f"Maximum value: {df['Values'].max()} (Category {df.loc[df['Values'].idxmax(), 'Category']})")
"""
        
        # Execute the code
        loop = asyncio.get_event_loop()
        execution_result = loop.run_until_complete(
            self.interpreter_service.execute_code(code)
        )
        
        # Check that execution was successful
        self.assertEqual(execution_result.status.value, "completed")
        self.assertIn("df", execution_result.variables)
        self.assertGreaterEqual(len(execution_result.plots), 2)
        
        # Generate report from execution result
        report = ReportGenerator.create_report_from_execution_result(
            title="Python Execution Report",
            execution_result=execution_result.__dict__,
            description="Report generated from Python code execution",
            template_type="technical"
        )
        
        # Save report
        report_id = self.storage_service.save_report(report)
        
        # Retrieve report
        retrieved_report = self.storage_service.get_report(report_id)
        
        # Check report content
        self.assertEqual(retrieved_report.title, "Python Execution Report")
        self.assertEqual(retrieved_report.description, "Report generated from Python code execution")
        
        # Check that report has sections
        self.assertGreaterEqual(len(retrieved_report.sections), 2)  # At least output and visualizations
        
        # Check that visualizations were included
        has_viz_section = False
        for section in retrieved_report.sections:
            if section.title == "Visualizations":
                has_viz_section = True
                self.assertGreaterEqual(len(section.visualizations), 2)
        
        self.assertTrue(has_viz_section, "Report should have a Visualizations section")
        
        # Check that report can be rendered as markdown and HTML
        markdown = ReportGenerator.render_report_markdown(retrieved_report)
        self.assertIn("# Python Execution Report", markdown)
        self.assertIn("Sample Bar Chart", markdown)
        
        html = ReportGenerator.render_report_html(retrieved_report)
        self.assertIn("<html>", html)
        self.assertIn("Python Execution Report", html)
    
    def test_generate_report_with_data_analysis(self):
        """Test generating a report with data analysis"""
        # Define Python code that performs data analysis
        code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Create a sample DataFrame with time series data
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=100, freq='D')
values = np.cumsum(np.random.randn(100)) + 100
df = pd.DataFrame({'Date': dates, 'Value': values})

# Add some seasonal pattern
df['Value'] = df['Value'] + 10 * np.sin(np.arange(100) * 2 * np.pi / 30)

# Add a categorical column
df['Category'] = pd.cut(df['Value'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])

# Create a time series plot
plt.figure(figsize=(10, 6))
plt.plot(df['Date'], df['Value'], marker='o', linestyle='-', alpha=0.7)
plt.title('Time Series Data')
plt.xlabel('Date')
plt.ylabel('Value')
plt.grid(True, alpha=0.3)

# Create a box plot by category
plt.figure(figsize=(10, 6))
sns.boxplot(x='Category', y='Value', data=df)
plt.title('Value Distribution by Category')
plt.xticks(rotation=45)
plt.tight_layout()

# Perform some analysis
print("Data Analysis Results:")
print(f"Data range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Value statistics:")
print(df['Value'].describe())

# Calculate rolling statistics
df['Rolling_Mean'] = df['Value'].rolling(window=7).mean()
df['Rolling_Std'] = df['Value'].rolling(window=7).std()

# Plot rolling statistics
plt.figure(figsize=(10, 6))
plt.plot(df['Date'], df['Value'], label='Original')
plt.plot(df['Date'], df['Rolling_Mean'], label='7-day Rolling Mean', linewidth=2)
plt.fill_between(
    df['Date'], 
    df['Rolling_Mean'] - df['Rolling_Std'],
    df['Rolling_Mean'] + df['Rolling_Std'],
    alpha=0.2, label='±1 Std Dev'
)
plt.title('Time Series with Rolling Statistics')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
"""
        
        # Execute the code
        loop = asyncio.get_event_loop()
        execution_result = loop.run_until_complete(
            self.interpreter_service.execute_code(code)
        )
        
        # Check that execution was successful
        self.assertEqual(execution_result.status.value, "completed")
        self.assertIn("df", execution_result.variables)
        self.assertGreaterEqual(len(execution_result.plots), 3)
        
        # Generate report from execution result
        report = ReportGenerator.create_report_from_execution_result(
            title="Time Series Analysis Report",
            execution_result=execution_result.__dict__,
            description="Report generated from time series analysis",
            template_type="executive"
        )
        
        # Save report
        report_id = self.storage_service.save_report(report)
        
        # Retrieve report
        retrieved_report = self.storage_service.get_report(report_id)
        
        # Check report content
        self.assertEqual(retrieved_report.title, "Time Series Analysis Report")
        self.assertEqual(retrieved_report.description, "Report generated from time series analysis")
        
        # Check that report has sections
        self.assertGreaterEqual(len(retrieved_report.sections), 2)  # At least output and visualizations
        
        # Check that visualizations were included
        has_viz_section = False
        for section in retrieved_report.sections:
            if section.title == "Visualizations":
                has_viz_section = True
                self.assertGreaterEqual(len(section.visualizations), 3)
        
        self.assertTrue(has_viz_section, "Report should have a Visualizations section")
        
        # Check that report can be rendered as markdown and HTML
        markdown = ReportGenerator.render_report_markdown(retrieved_report, "executive")
        self.assertIn("# Executive Summary: Time Series Analysis Report", markdown)
        self.assertIn("Time Series Data", markdown)
        
        html = ReportGenerator.render_report_html(retrieved_report, "executive")
        self.assertIn("<html>", html)
        self.assertIn("Time Series Analysis Report", html)


if __name__ == "__main__":
    unittest.main()