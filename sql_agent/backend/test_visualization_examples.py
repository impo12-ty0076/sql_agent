"""
Example script to demonstrate data visualization functionality
"""

import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os

from services.python_interpreter_enhanced import EnhancedPythonInterpreterService


async def main():
    """Run visualization examples"""
    print("Running visualization examples...")
    
    # Create interpreter service
    interpreter = EnhancedPythonInterpreterService()
    
    # Example 1: Basic Matplotlib visualization
    code1 = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create sample data
data = {
    'category': ['A', 'B', 'C', 'D', 'E'] * 5,
    'value1': np.random.normal(100, 15, 25),
    'value2': np.random.normal(50, 5, 25),
    'date': pd.date_range(start='2023-01-01', periods=25)
}
df = pd.DataFrame(data)

# Create a simple bar chart
plt.figure(figsize=(10, 6))
df.groupby('category')['value1'].mean().plot(kind='bar', color='skyblue')
plt.title('Average Value by Category')
plt.xlabel('Category')
plt.ylabel('Average Value')
plt.tight_layout()

print("Created a simple bar chart")
"""
    
    # Example 2: Using ChartGenerator
    code2 = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create sample data
data = {
    'category': ['A', 'B', 'C', 'D', 'E'] * 5,
    'value1': np.random.normal(100, 15, 25),
    'value2': np.random.normal(50, 5, 25),
    'date': pd.date_range(start='2023-01-01', periods=25)
}
df = pd.DataFrame(data)

# Use ChartGenerator for bar chart
df_grouped = df.groupby('category')['value1'].mean().reset_index()
fig1 = ChartGenerator.bar_chart(
    df=df_grouped,
    x_column='category',
    y_column='value1',
    title="Bar Chart Example"
)

# Use ChartGenerator for line chart
df_sorted = df.sort_values('date')
fig2 = ChartGenerator.line_chart(
    df=df_sorted,
    x_column='date',
    y_columns=['value1', 'value2'],
    title="Line Chart Example"
)

# Use ChartGenerator for scatter plot
fig3 = ChartGenerator.scatter_plot(
    df=df,
    x_column='value1',
    y_column='value2',
    title="Scatter Plot Example"
)

print("Created charts using ChartGenerator")
"""
    
    # Example 3: Using PlotlyChartGenerator (if available)
    code3 = """
import pandas as pd
import numpy as np

# Create sample data
data = {
    'category': ['A', 'B', 'C', 'D', 'E'] * 5,
    'value1': np.random.normal(100, 15, 25),
    'value2': np.random.normal(50, 5, 25),
    'date': pd.date_range(start='2023-01-01', periods=25)
}
df = pd.DataFrame(data)

# Check if PlotlyChartGenerator is available
if 'PlotlyChartGenerator' in globals():
    # Use PlotlyChartGenerator for bar chart
    df_grouped = df.groupby('category')['value1'].mean().reset_index()
    plotly_fig1 = PlotlyChartGenerator.bar_chart(
        df=df_grouped,
        x_column='category',
        y_column='value1',
        title="Plotly Bar Chart Example"
    )
    
    # Use PlotlyChartGenerator for line chart
    df_sorted = df.sort_values('date')
    plotly_fig2 = PlotlyChartGenerator.line_chart(
        df=df_sorted,
        x_column='date',
        y_columns=['value1', 'value2'],
        title="Plotly Line Chart Example"
    )
    
    print("Created charts using PlotlyChartGenerator")
else:
    print("PlotlyChartGenerator is not available")
"""
    
    # Example 4: Saving visualizations
    code4 = """
import pandas as pd
import numpy as np
import os

# Create sample data
data = {
    'category': ['A', 'B', 'C', 'D', 'E'] * 5,
    'value1': np.random.normal(100, 15, 25),
    'value2': np.random.normal(50, 5, 25),
    'date': pd.date_range(start='2023-01-01', periods=25)
}
df = pd.DataFrame(data)

# Create a visualization
df_grouped = df.groupby('category')['value1'].mean().reset_index()
fig = ChartGenerator.bar_chart(
    df=df_grouped,
    x_column='category',
    y_column='value1',
    title="Bar Chart for Saving"
)

# Create visualization object
vis = VisualizationService.create_matplotlib_visualization(
    title="Bar Chart for Saving",
    description="A bar chart showing average values by category",
    fig=fig
)

# Create output directory
os.makedirs('output', exist_ok=True)

# Save visualization
filepath = VisualizationService.save_visualization(
    visualization=vis,
    directory='output',
    filename="bar_chart_example"
)

print(f"Saved visualization to {filepath}")
"""
    
    # Run examples
    print("\n--- Example 1: Basic Matplotlib visualization ---")
    result1 = await interpreter.execute_code(code1)
    print(f"Status: {result1.status.value}")
    print(f"Output: {result1.output}")
    print(f"Number of plots: {len(result1.plots)}")
    
    print("\n--- Example 2: Using ChartGenerator ---")
    result2 = await interpreter.execute_code(code2)
    print(f"Status: {result2.status.value}")
    print(f"Output: {result2.output}")
    print(f"Number of plots: {len(result2.plots)}")
    
    print("\n--- Example 3: Using PlotlyChartGenerator ---")
    result3 = await interpreter.execute_code(code3)
    print(f"Status: {result3.status.value}")
    print(f"Output: {result3.output}")
    print(f"Number of plots: {len(result3.plots)}")
    
    print("\n--- Example 4: Saving visualizations ---")
    result4 = await interpreter.execute_code(code4)
    print(f"Status: {result4.status.value}")
    print(f"Output: {result4.output}")
    print(f"Number of plots: {len(result4.plots)}")
    
    # Save plot data to file for inspection
    with open('visualization_results.json', 'w') as f:
        json.dump({
            'example1_plots': [
                {'type': p['type'], 'format': p['format']} 
                for p in result1.plots
            ],
            'example2_plots': [
                {'type': p['type'], 'format': p['format']} 
                for p in result2.plots
            ],
            'example3_plots': [
                {'type': p['type'], 'format': p['format']} 
                for p in result3.plots
            ],
            'example4_plots': [
                {'type': p['type'], 'format': p['format']} 
                for p in result4.plots
            ]
        }, f, indent=2)
    
    print("\nVisualization examples completed.")


if __name__ == "__main__":
    asyncio.run(main())