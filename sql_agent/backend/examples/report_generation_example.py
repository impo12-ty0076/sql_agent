"""
Report Generation Example

This script demonstrates how to use the report generation functionality.
"""

import os
import sys
import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.python_interpreter_enhanced import EnhancedPythonInterpreterService
from services.report_generation import (
    ReportGenerator, ReportStorageService, Report, ReportSection
)


async def generate_sample_report():
    """Generate a sample report from Python code execution"""
    print("Generating sample report...")
    
    # Create Python interpreter service
    interpreter_service = EnhancedPythonInterpreterService()
    
    # Create report storage service
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    storage_service = ReportStorageService(reports_dir)
    
    # Define Python code that generates visualizations and performs analysis
    code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Create a sample dataset of sales data
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=365, freq='D')
products = ['Product A', 'Product B', 'Product C', 'Product D']
regions = ['North', 'South', 'East', 'West']

# Generate random sales data
data = []
for date in dates:
    for product in products:
        for region in regions:
            # Create seasonal pattern with some randomness
            month = date.month
            season_factor = 1.0 + 0.3 * np.sin((month - 1) * np.pi / 6)
            
            # Product-specific factors
            if product == 'Product A':
                product_factor = 1.2
            elif product == 'Product B':
                product_factor = 0.9
            elif product == 'Product C':
                product_factor = 1.5
            else:
                product_factor = 0.7
                
            # Region-specific factors
            if region == 'North':
                region_factor = 0.8
            elif region == 'South':
                region_factor = 1.1
            elif region == 'East':
                region_factor = 1.3
            else:
                region_factor = 0.9
                
            # Calculate sales with some randomness
            sales = 100 * season_factor * product_factor * region_factor
            sales = sales * (1 + 0.2 * np.random.randn())
            
            # Add to data
            data.append({
                'Date': date,
                'Product': product,
                'Region': region,
                'Sales': sales
            })

# Create DataFrame
sales_df = pd.DataFrame(data)

# Perform some analysis
print("Sales Data Analysis")
print("-----------------")
print(f"Total records: {len(sales_df)}")
print(f"Date range: {sales_df['Date'].min()} to {sales_df['Date'].max()}")
print(f"Total sales: ${sales_df['Sales'].sum():,.2f}")
print()

# Monthly sales trend
monthly_sales = sales_df.groupby(sales_df['Date'].dt.strftime('%Y-%m')).agg({'Sales': 'sum'}).reset_index()
monthly_sales['Month'] = pd.to_datetime(monthly_sales['Date'] + '-01')

plt.figure(figsize=(12, 6))
plt.plot(monthly_sales['Month'], monthly_sales['Sales'], marker='o', linestyle='-')
plt.title('Monthly Sales Trend')
plt.xlabel('Month')
plt.ylabel('Total Sales ($)')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Sales by product
product_sales = sales_df.groupby('Product').agg({'Sales': 'sum'}).reset_index()
product_sales = product_sales.sort_values('Sales', ascending=False)

plt.figure(figsize=(10, 6))
plt.bar(product_sales['Product'], product_sales['Sales'], color='skyblue')
plt.title('Total Sales by Product')
plt.xlabel('Product')
plt.ylabel('Total Sales ($)')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Sales by region
region_sales = sales_df.groupby('Region').agg({'Sales': 'sum'}).reset_index()
region_sales = region_sales.sort_values('Sales', ascending=False)

plt.figure(figsize=(10, 6))
plt.bar(region_sales['Region'], region_sales['Sales'], color='lightgreen')
plt.title('Total Sales by Region')
plt.xlabel('Region')
plt.ylabel('Total Sales ($)')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Product sales by region
product_region_sales = sales_df.groupby(['Product', 'Region']).agg({'Sales': 'sum'}).reset_index()
pivot_table = product_region_sales.pivot(index='Product', columns='Region', values='Sales')

plt.figure(figsize=(12, 8))
sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlGnBu')
plt.title('Sales by Product and Region')
plt.tight_layout()

# Monthly sales by product
monthly_product_sales = sales_df.groupby([sales_df['Date'].dt.strftime('%Y-%m'), 'Product']).agg({'Sales': 'sum'}).reset_index()
monthly_product_sales['Month'] = pd.to_datetime(monthly_product_sales['Date'] + '-01')
pivot_table = monthly_product_sales.pivot(index='Month', columns='Product', values='Sales')

plt.figure(figsize=(14, 8))
pivot_table.plot(marker='o', ax=plt.gca())
plt.title('Monthly Sales by Product')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.grid(True, alpha=0.3)
plt.legend(title='Product')
plt.tight_layout()

# Calculate key metrics
top_month = monthly_sales.loc[monthly_sales['Sales'].idxmax()]
top_product = product_sales.iloc[0]
top_region = region_sales.iloc[0]

print("Key Insights:")
print(f"- Best performing month: {top_month['Month'].strftime('%B %Y')} with ${top_month['Sales']:,.2f} in sales")
print(f"- Top product: {top_product['Product']} with ${top_product['Sales']:,.2f} in sales")
print(f"- Top region: {top_region['Region']} with ${top_region['Sales']:,.2f} in sales")

# Calculate growth rates
monthly_sales['Growth'] = monthly_sales['Sales'].pct_change() * 100
avg_growth = monthly_sales['Growth'].mean()
print(f"- Average month-over-month growth rate: {avg_growth:.2f}%")

# Identify seasonal patterns
quarterly_sales = sales_df.groupby(sales_df['Date'].dt.quarter).agg({'Sales': 'sum'})
best_quarter = quarterly_sales.idxmax()[0]
print(f"- Best performing quarter: Q{best_quarter}")
"""
    
    # Execute the code
    print("Executing Python code...")
    execution_result = await interpreter_service.execute_code(code)
    
    # Check that execution was successful
    if execution_result.status.value != "completed":
        print(f"Execution failed: {execution_result.error}")
        return
    
    print("Python code executed successfully.")
    print(f"Generated {len(execution_result.plots)} visualizations.")
    
    # Generate report from execution result
    print("Generating report...")
    report = ReportGenerator.create_report_from_execution_result(
        title="Sales Data Analysis Report",
        execution_result=execution_result.__dict__,
        description="Analysis of sales data across products and regions",
        template_type="executive",
        author="SQL Agent System"
    )
    
    # Save report
    print("Saving report...")
    report_id = storage_service.save_report(report)
    
    # Get report file paths
    report_dir = os.path.join(reports_dir, report_id)
    markdown_path = os.path.join(report_dir, "report.md")
    html_path = os.path.join(report_dir, "report.html")
    
    print(f"Report generated successfully!")
    print(f"Report ID: {report_id}")
    print(f"Markdown report: {markdown_path}")
    print(f"HTML report: {html_path}")
    
    # Open the HTML report in the default browser
    try:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
        print("Opened report in browser.")
    except Exception as e:
        print(f"Could not open report in browser: {str(e)}")


if __name__ == "__main__":
    asyncio.run(generate_sample_report())