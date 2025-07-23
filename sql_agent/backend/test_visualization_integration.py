"""
Integration test for data visualization functionality
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import base64
from io import BytesIO

from services.data_visualization import (
    VisualizationService, ChartGenerator, PlotlyChartGenerator, Visualization
)

def main():
    """Test visualization functionality"""
    print("Testing visualization functionality...")
    
    # Create sample data
    data = {
        'category': ['A', 'B', 'C', 'D', 'E'] * 5,
        'value1': np.random.normal(100, 15, 25),
        'value2': np.random.normal(50, 5, 25),
        'date': pd.date_range(start='2023-01-01', periods=25)
    }
    df = pd.DataFrame(data)
    
    # Test bar chart
    print("Creating bar chart...")
    df_grouped = df.groupby('category')['value1'].mean().reset_index()
    bar_fig = ChartGenerator.bar_chart(
        df=df_grouped,
        x_column='category',
        y_column='value1',
        title="Bar Chart Example"
    )
    
    # Create visualization from figure
    bar_vis = VisualizationService.create_matplotlib_visualization(
        title="Bar Chart Example",
        description="A bar chart showing average values by category",
        fig=bar_fig
    )
    
    print(f"Created visualization: {bar_vis.title}")
    print(f"- Format: {bar_vis.format}")
    print(f"- Data length: {len(bar_vis.data)} characters")
    
    # Test line chart
    print("\nCreating line chart...")
    df_sorted = df.sort_values('date')
    line_fig = ChartGenerator.line_chart(
        df=df_sorted,
        x_column='date',
        y_columns=['value1', 'value2'],
        title="Line Chart Example"
    )
    
    # Create visualization from figure
    line_vis = VisualizationService.create_matplotlib_visualization(
        title="Line Chart Example",
        description="A line chart showing values over time",
        fig=line_fig
    )
    
    print(f"Created visualization: {line_vis.title}")
    print(f"- Format: {line_vis.format}")
    print(f"- Data length: {len(line_vis.data)} characters")
    
    # Save visualizations
    print("\nSaving visualizations...")
    os.makedirs('output', exist_ok=True)
    
    bar_path = VisualizationService.save_visualization(
        visualization=bar_vis,
        directory='output',
        filename="bar_chart_example"
    )
    
    line_path = VisualizationService.save_visualization(
        visualization=line_vis,
        directory='output',
        filename="line_chart_example"
    )
    
    print(f"Saved bar chart to: {bar_path}")
    print(f"Saved line chart to: {line_path}")
    
    # Test Plotly if available
    if hasattr(PlotlyChartGenerator, 'HAS_PLOTLY') and PlotlyChartGenerator.HAS_PLOTLY:
        print("\nTesting Plotly charts...")
        
        plotly_bar = PlotlyChartGenerator.bar_chart(
            df=df_grouped,
            x_column='category',
            y_column='value1',
            title="Plotly Bar Chart Example"
        )
        
        if plotly_bar:
            plotly_vis = VisualizationService.create_plotly_visualization(
                title="Plotly Bar Chart Example",
                fig=plotly_bar
            )
            
            if plotly_vis:
                print(f"Created Plotly visualization: {plotly_vis.title}")
                print(f"- Format: {plotly_vis.format}")
                print(f"- Data length: {len(plotly_vis.data)} characters")
                
                plotly_path = VisualizationService.save_visualization(
                    visualization=plotly_vis,
                    directory='output',
                    filename="plotly_bar_chart_example"
                )
                
                print(f"Saved Plotly chart to: {plotly_path}")
            else:
                print("Failed to create Plotly visualization")
        else:
            print("Failed to create Plotly chart")
    else:
        print("\nPlotly is not available")
    
    print("\nVisualization tests completed successfully!")


if __name__ == "__main__":
    main()