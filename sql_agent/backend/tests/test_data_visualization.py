"""
Unit tests for Data Visualization Service
"""

import pytest
import pandas as pd
import numpy as np
import base64
import matplotlib.pyplot as plt
import os
import tempfile
from io import BytesIO

from services.data_visualization import (
    VisualizationService, ChartGenerator, PlotlyChartGenerator, Visualization
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing"""
    data = {
        'category': ['A', 'B', 'C', 'D', 'E'] * 5,
        'value1': np.random.normal(100, 15, 25),
        'value2': np.random.normal(50, 5, 25),
        'date': pd.date_range(start='2023-01-01', periods=25)
    }
    return pd.DataFrame(data)


def test_visualization_create():
    """Test creating a visualization object"""
    vis = Visualization.create(
        title="Test Visualization",
        chart_type="test_chart",
        data="base64data",
        format="png",
        description="Test description",
        metadata={"test": "metadata"}
    )
    
    assert vis.title == "Test Visualization"
    assert vis.chart_type == "test_chart"
    assert vis.data == "base64data"
    assert vis.format == "png"
    assert vis.description == "Test description"
    assert vis.metadata == {"test": "metadata"}
    assert vis.id is not None
    assert vis.timestamp is not None


def test_create_matplotlib_visualization():
    """Test creating a visualization from matplotlib figure"""
    # Create a simple figure
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    
    # Create visualization
    vis = VisualizationService.create_matplotlib_visualization(
        title="Test Plot",
        description="A test plot",
        fig=fig
    )
    
    assert vis.title == "Test Plot"
    assert vis.description == "A test plot"
    assert vis.chart_type == "matplotlib"
    assert vis.format == "png"
    
    # Verify base64 data
    try:
        img_data = base64.b64decode(vis.data)
        assert len(img_data) > 0
    except:
        pytest.fail("Visualization data is not valid base64")
    
    # Check metadata
    assert 'figsize' in vis.metadata
    assert 'dpi' in vis.metadata
    assert vis.metadata['dpi'] == 100


def test_save_visualization():
    """Test saving visualization to file"""
    # Create a simple figure
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    
    # Create visualization
    vis = VisualizationService.create_matplotlib_visualization(
        title="Test Plot",
        fig=fig
    )
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save visualization
        filepath = VisualizationService.save_visualization(
            visualization=vis,
            directory=temp_dir,
            filename="test_plot"
        )
        
        # Check that file exists
        assert os.path.exists(filepath)
        assert os.path.basename(filepath) == "test_plot.png"
        
        # Check file content
        with open(filepath, 'rb') as f:
            file_data = f.read()
            assert len(file_data) > 0


def test_bar_chart(sample_dataframe):
    """Test bar chart generation"""
    # Group by category and calculate mean
    df_grouped = sample_dataframe.groupby('category')['value1'].mean().reset_index()
    
    # Generate bar chart
    fig = ChartGenerator.bar_chart(
        df=df_grouped,
        x_column='category',
        y_column='value1',
        title="Test Bar Chart"
    )
    
    assert isinstance(fig, plt.Figure)
    assert fig.axes[0].get_title() == "Test Bar Chart"
    assert fig.axes[0].get_xlabel() == "category"
    assert fig.axes[0].get_ylabel() == "value1"


def test_line_chart(sample_dataframe):
    """Test line chart generation"""
    # Sort by date for line chart
    df_sorted = sample_dataframe.sort_values('date')
    
    # Generate line chart with single y column
    fig1 = ChartGenerator.line_chart(
        df=df_sorted,
        x_column='date',
        y_columns='value1',
        title="Test Line Chart"
    )
    
    assert isinstance(fig1, plt.Figure)
    assert fig1.axes[0].get_title() == "Test Line Chart"
    
    # Generate line chart with multiple y columns
    fig2 = ChartGenerator.line_chart(
        df=df_sorted,
        x_column='date',
        y_columns=['value1', 'value2'],
        title="Test Multi-Line Chart"
    )
    
    assert isinstance(fig2, plt.Figure)
    assert fig2.axes[0].get_title() == "Test Multi-Line Chart"
    assert len(fig2.axes[0].get_legend().get_texts()) == 2  # Two legend entries


def test_scatter_plot(sample_dataframe):
    """Test scatter plot generation"""
    fig = ChartGenerator.scatter_plot(
        df=sample_dataframe,
        x_column='value1',
        y_column='value2',
        title="Test Scatter Plot"
    )
    
    assert isinstance(fig, plt.Figure)
    assert fig.axes[0].get_title() == "Test Scatter Plot"
    assert fig.axes[0].get_xlabel() == "value1"
    assert fig.axes[0].get_ylabel() == "value2"


def test_histogram(sample_dataframe):
    """Test histogram generation"""
    fig = ChartGenerator.histogram(
        df=sample_dataframe,
        column='value1',
        bins=10,
        title="Test Histogram"
    )
    
    assert isinstance(fig, plt.Figure)
    assert fig.axes[0].get_title() == "Test Histogram"
    assert fig.axes[0].get_xlabel() == "value1"
    assert fig.axes[0].get_ylabel() == "Frequency"


def test_pie_chart(sample_dataframe):
    """Test pie chart generation"""
    fig = ChartGenerator.pie_chart(
        df=sample_dataframe,
        column='category',
        title="Test Pie Chart"
    )
    
    assert isinstance(fig, plt.Figure)
    assert fig.axes[0].get_title() == "Test Pie Chart"


def test_heatmap(sample_dataframe):
    """Test heatmap generation"""
    # Create correlation matrix
    corr_matrix = sample_dataframe[['value1', 'value2']].corr()
    
    fig = ChartGenerator.heatmap(
        df=corr_matrix,
        title="Test Heatmap"
    )
    
    assert isinstance(fig, plt.Figure)
    assert fig.axes[0].get_title() == "Test Heatmap"


def test_box_plot(sample_dataframe):
    """Test box plot generation"""
    # Single column box plot
    fig1 = ChartGenerator.box_plot(
        df=sample_dataframe,
        column='value1',
        title="Test Box Plot"
    )
    
    assert isinstance(fig1, plt.Figure)
    assert fig1.axes[0].get_title() == "Test Box Plot"
    
    # Box plot grouped by category
    fig2 = ChartGenerator.box_plot(
        df=sample_dataframe,
        column='value1',
        by='category',
        title="Test Grouped Box Plot"
    )
    
    assert isinstance(fig2, plt.Figure)
    assert fig2.axes[0].get_title() == "Test Grouped Box Plot"


def test_plotly_chart_generators(sample_dataframe):
    """Test Plotly chart generators"""
    # Skip tests if Plotly is not available
    plotly_available = hasattr(PlotlyChartGenerator, 'HAS_PLOTLY') and PlotlyChartGenerator.HAS_PLOTLY
    if not plotly_available:
        pytest.skip("Plotly is not available")
    
    # Group by category and calculate mean for bar chart
    df_grouped = sample_dataframe.groupby('category')['value1'].mean().reset_index()
    
    # Test bar chart
    bar_fig = PlotlyChartGenerator.bar_chart(
        df=df_grouped,
        x_column='category',
        y_column='value1',
        title="Test Plotly Bar Chart"
    )
    assert bar_fig is not None
    
    # Test line chart
    df_sorted = sample_dataframe.sort_values('date')
    line_fig = PlotlyChartGenerator.line_chart(
        df=df_sorted,
        x_column='date',
        y_columns='value1',
        title="Test Plotly Line Chart"
    )
    assert line_fig is not None
    
    # Test scatter plot
    scatter_fig = PlotlyChartGenerator.scatter_plot(
        df=sample_dataframe,
        x_column='value1',
        y_column='value2',
        title="Test Plotly Scatter Plot"
    )
    assert scatter_fig is not None
    
    # Test histogram
    hist_fig = PlotlyChartGenerator.histogram(
        df=sample_dataframe,
        column='value1',
        title="Test Plotly Histogram"
    )
    assert hist_fig is not None
    
    # Test pie chart
    pie_fig = PlotlyChartGenerator.pie_chart(
        df=sample_dataframe,
        column='category',
        title="Test Plotly Pie Chart"
    )
    assert pie_fig is not None
    
    # Test heatmap
    corr_matrix = sample_dataframe[['value1', 'value2']].corr()
    heatmap_fig = PlotlyChartGenerator.heatmap(
        df=corr_matrix,
        title="Test Plotly Heatmap"
    )
    assert heatmap_fig is not None
    
    # Test box plot
    box_fig = PlotlyChartGenerator.box_plot(
        df=sample_dataframe,
        column='value1',
        title="Test Plotly Box Plot"
    )
    assert box_fig is not None


if __name__ == "__main__":
    pytest.main([__file__])