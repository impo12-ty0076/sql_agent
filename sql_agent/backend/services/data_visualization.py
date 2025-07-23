"""
Data Visualization Service

This module provides utilities for creating, rendering, and managing data visualizations
using matplotlib, plotly, and other visualization libraries.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
import json
from io import StringIO, BytesIO
import base64
import uuid
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from dataclasses import dataclass
import time

# Optional imports with fallbacks
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    sns = None
    HAS_SEABORN = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.io import to_image
    HAS_PLOTLY = True
except ImportError:
    go = None
    px = None
    to_image = None
    HAS_PLOTLY = False


@dataclass
class Visualization:
    """Represents a data visualization"""
    id: str
    title: str
    description: Optional[str]
    chart_type: str
    data: str  # Base64 encoded image data
    format: str  # Image format (png, svg, etc.)
    metadata: Dict[str, Any]
    timestamp: float
    
    @classmethod
    def create(cls, title: str, chart_type: str, data: str, format: str, 
              description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Create a new visualization"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            chart_type=chart_type,
            data=data,
            format=format,
            metadata=metadata or {},
            timestamp=time.time()
        )


class VisualizationService:
    """Service for creating and managing data visualizations"""
    
    @staticmethod
    def create_matplotlib_visualization(
        title: str,
        description: Optional[str] = None,
        fig: Optional[plt.Figure] = None,
        dpi: int = 100,
        format: str = 'png'
    ) -> Visualization:
        """
        Create a visualization from a matplotlib figure
        
        Args:
            title: Title of the visualization
            description: Optional description
            fig: Matplotlib figure (uses current figure if None)
            dpi: Resolution in dots per inch
            format: Image format (png, svg, etc.)
            
        Returns:
            Visualization object
        """
        if fig is None:
            fig = plt.gcf()
            
        # Save figure to bytes
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format=format, bbox_inches='tight', dpi=dpi)
        img_buffer.seek(0)
        
        # Encode as base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Get figure size and other metadata
        metadata = {
            'figsize': fig.get_size_inches().tolist(),
            'dpi': dpi,
            'num_axes': len(fig.axes)
        }
        
        # Create visualization
        return Visualization.create(
            title=title,
            description=description,
            chart_type='matplotlib',
            data=img_base64,
            format=format,
            metadata=metadata
        )
    
    @staticmethod
    def create_plotly_visualization(
        title: str,
        fig: Union['go.Figure', 'px.Figure'],
        description: Optional[str] = None,
        format: str = 'png',
        width: int = 800,
        height: int = 600
    ) -> Optional[Visualization]:
        """
        Create a visualization from a plotly figure
        
        Args:
            title: Title of the visualization
            fig: Plotly figure
            description: Optional description
            format: Image format (png, svg, etc.)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Visualization object or None if plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            # Convert to image
            img_bytes = to_image(fig, format=format, width=width, height=height)
            
            # Encode as base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Get metadata
            metadata = {
                'width': width,
                'height': height
            }
            
            # Create visualization
            return Visualization.create(
                title=title,
                description=description,
                chart_type='plotly',
                data=img_base64,
                format=format,
                metadata=metadata
            )
        except Exception as e:
            print(f"Error creating plotly visualization: {str(e)}")
            return None
    
    @staticmethod
    def save_visualization(
        visualization: Visualization,
        directory: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save visualization to file
        
        Args:
            visualization: Visualization object
            directory: Directory to save to
            filename: Optional filename (uses visualization ID if None)
            
        Returns:
            Path to saved file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            filename = f"{visualization.id}.{visualization.format}"
        elif not filename.endswith(f".{visualization.format}"):
            filename = f"{filename}.{visualization.format}"
            
        # Full path
        filepath = os.path.join(directory, filename)
        
        # Decode base64 and write to file
        img_data = base64.b64decode(visualization.data)
        with open(filepath, 'wb') as f:
            f.write(img_data)
            
        return filepath


class ChartGenerator:
    """Utilities for generating common chart types"""
    
    @staticmethod
    def bar_chart(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "Bar Chart",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        color: str = 'skyblue',
        figsize: Tuple[int, int] = (10, 6),
        use_seaborn: bool = True
    ) -> plt.Figure:
        """
        Generate a bar chart
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_column: Column for y-axis
            title: Chart title
            xlabel: X-axis label (uses x_column if None)
            ylabel: Y-axis label (uses y_column if None)
            color: Bar color
            figsize: Figure size (width, height) in inches
            use_seaborn: Whether to use seaborn for styling
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set labels
        if xlabel is None:
            xlabel = x_column
        if ylabel is None:
            ylabel = y_column
            
        # Create chart
        if use_seaborn and HAS_SEABORN:
            sns.barplot(x=x_column, y=y_column, data=df, ax=ax, color=color)
        else:
            df.plot.bar(x=x_column, y=y_column, ax=ax, color=color)
            
        # Set title and labels
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Rotate x-axis labels if there are many categories
        if len(df[x_column].unique()) > 5:
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        return fig
    
    @staticmethod
    def line_chart(
        df: pd.DataFrame,
        x_column: str,
        y_columns: Union[str, List[str]],
        title: str = "Line Chart",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        use_seaborn: bool = True,
        include_markers: bool = False
    ) -> plt.Figure:
        """
        Generate a line chart
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_columns: Column(s) for y-axis
            title: Chart title
            xlabel: X-axis label (uses x_column if None)
            ylabel: Y-axis label
            figsize: Figure size (width, height) in inches
            use_seaborn: Whether to use seaborn for styling
            include_markers: Whether to include markers on lines
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set labels
        if xlabel is None:
            xlabel = x_column
            
        # Apply seaborn styling if available
        if use_seaborn and HAS_SEABORN:
            sns.set_style("whitegrid")
            
        # Convert y_columns to list if it's a string
        if isinstance(y_columns, str):
            y_columns = [y_columns]
            
        # Create chart
        for y_col in y_columns:
            if include_markers:
                ax.plot(df[x_column], df[y_col], marker='o', label=y_col)
            else:
                ax.plot(df[x_column], df[y_col], label=y_col)
                
        # Set title and labels
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
            
        # Add legend if multiple y columns
        if len(y_columns) > 1:
            ax.legend()
            
        plt.tight_layout()
        return fig
    
    @staticmethod
    def scatter_plot(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None,
        size_column: Optional[str] = None,
        title: str = "Scatter Plot",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        use_seaborn: bool = True
    ) -> plt.Figure:
        """
        Generate a scatter plot
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_column: Column for y-axis
            color_column: Optional column for point colors
            size_column: Optional column for point sizes
            title: Chart title
            xlabel: X-axis label (uses x_column if None)
            ylabel: Y-axis label (uses y_column if None)
            figsize: Figure size (width, height) in inches
            use_seaborn: Whether to use seaborn for styling
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set labels
        if xlabel is None:
            xlabel = x_column
        if ylabel is None:
            ylabel = y_column
            
        # Create chart
        if use_seaborn and HAS_SEABORN:
            if color_column is not None:
                sns.scatterplot(x=x_column, y=y_column, hue=color_column, 
                               size=size_column, data=df, ax=ax)
            else:
                sns.scatterplot(x=x_column, y=y_column, size=size_column, data=df, ax=ax)
        else:
            if color_column is not None and size_column is not None:
                scatter = ax.scatter(df[x_column], df[y_column], 
                                   c=df[color_column], s=df[size_column])
                plt.colorbar(scatter, ax=ax, label=color_column)
            elif color_column is not None:
                scatter = ax.scatter(df[x_column], df[y_column], c=df[color_column])
                plt.colorbar(scatter, ax=ax, label=color_column)
            elif size_column is not None:
                ax.scatter(df[x_column], df[y_column], s=df[size_column])
            else:
                ax.scatter(df[x_column], df[y_column])
                
        # Set title and labels
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def histogram(
        df: pd.DataFrame,
        column: str,
        bins: int = 30,
        title: str = None,
        xlabel: Optional[str] = None,
        ylabel: str = "Frequency",
        color: str = 'skyblue',
        figsize: Tuple[int, int] = (10, 6),
        kde: bool = True,
        use_seaborn: bool = True
    ) -> plt.Figure:
        """
        Generate a histogram
        
        Args:
            df: Input DataFrame
            column: Column to plot
            bins: Number of bins
            title: Chart title (uses column name if None)
            xlabel: X-axis label (uses column name if None)
            ylabel: Y-axis label
            color: Bar color
            figsize: Figure size (width, height) in inches
            kde: Whether to include KDE curve
            use_seaborn: Whether to use seaborn for styling
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set title and labels
        if title is None:
            title = f"Distribution of {column}"
        if xlabel is None:
            xlabel = column
            
        # Create chart
        if use_seaborn and HAS_SEABORN:
            sns.histplot(df[column], bins=bins, kde=kde, color=color, ax=ax)
        else:
            ax.hist(df[column], bins=bins, color=color, alpha=0.7)
            
            # Add KDE if requested and scipy is available
            if kde:
                try:
                    from scipy import stats
                    density = stats.gaussian_kde(df[column].dropna())
                    x_range = np.linspace(df[column].min(), df[column].max(), 1000)
                    ax.plot(x_range, density(x_range) * len(df[column]) * (df[column].max() - df[column].min()) / bins, 
                           color='darkblue')
                except ImportError:
                    pass
                
        # Set title and labels
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def pie_chart(
        df: pd.DataFrame,
        column: str,
        title: str = None,
        figsize: Tuple[int, int] = (10, 6),
        colors: Optional[List[str]] = None,
        autopct: str = '%1.1f%%',
        max_categories: int = 10
    ) -> plt.Figure:
        """
        Generate a pie chart
        
        Args:
            df: Input DataFrame
            column: Column to plot
            title: Chart title (uses column name if None)
            figsize: Figure size (width, height) in inches
            colors: List of colors for pie slices
            autopct: Format string for percentage labels
            max_categories: Maximum number of categories to show (others grouped as 'Other')
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set title
        if title is None:
            title = f"Distribution of {column}"
            
        # Get value counts
        value_counts = df[column].value_counts()
        
        # Limit categories if needed
        if len(value_counts) > max_categories:
            top_categories = value_counts.iloc[:max_categories-1]
            other_sum = value_counts.iloc[max_categories-1:].sum()
            
            # Create new series with 'Other' category
            value_counts = pd.concat([top_categories, pd.Series({'Other': other_sum})])
            
        # Create chart
        ax.pie(value_counts, labels=value_counts.index, autopct=autopct, colors=colors)
        ax.set_title(title)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def heatmap(
        df: pd.DataFrame,
        title: str = "Heatmap",
        figsize: Tuple[int, int] = (10, 8),
        cmap: str = 'viridis',
        annot: bool = True,
        use_seaborn: bool = True
    ) -> plt.Figure:
        """
        Generate a heatmap
        
        Args:
            df: Input DataFrame (should be a correlation matrix or similar)
            title: Chart title
            figsize: Figure size (width, height) in inches
            cmap: Colormap name
            annot: Whether to annotate cells with values
            use_seaborn: Whether to use seaborn for styling
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create chart
        if use_seaborn and HAS_SEABORN:
            sns.heatmap(df, annot=annot, cmap=cmap, ax=ax)
        else:
            im = ax.imshow(df, cmap=cmap)
            plt.colorbar(im, ax=ax)
            
            # Add annotations if requested
            if annot:
                for i in range(len(df)):
                    for j in range(len(df.columns)):
                        text = ax.text(j, i, f"{df.iloc[i, j]:.2f}", 
                                     ha="center", va="center", color="black")
                        
            # Set tick labels
            ax.set_xticks(np.arange(len(df.columns)))
            ax.set_yticks(np.arange(len(df.index)))
            ax.set_xticklabels(df.columns)
            ax.set_yticklabels(df.index)
            
            # Rotate x-axis labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            
        # Set title
        ax.set_title(title)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def box_plot(
        df: pd.DataFrame,
        column: Union[str, List[str]],
        by: Optional[str] = None,
        title: str = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        use_seaborn: bool = True
    ) -> plt.Figure:
        """
        Generate a box plot
        
        Args:
            df: Input DataFrame
            column: Column(s) to plot
            by: Optional grouping column
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size (width, height) in inches
            use_seaborn: Whether to use seaborn for styling
            
        Returns:
            Matplotlib figure
        """
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set title
        if title is None:
            if isinstance(column, str):
                title = f"Box Plot of {column}"
            else:
                title = "Box Plot"
                
        # Create chart
        if use_seaborn and HAS_SEABORN:
            if by is not None:
                sns.boxplot(x=by, y=column, data=df, ax=ax)
            else:
                if isinstance(column, list):
                    # Melt the DataFrame for multiple columns
                    melted_df = pd.melt(df[column])
                    sns.boxplot(x='variable', y='value', data=melted_df, ax=ax)
                else:
                    sns.boxplot(y=column, data=df, ax=ax)
        else:
            if by is not None:
                df.boxplot(column=column, by=by, ax=ax)
            else:
                df.boxplot(column=column, ax=ax)
                
        # Set title and labels
        ax.set_title(title)
        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
            
        plt.tight_layout()
        return fig


class PlotlyChartGenerator:
    """Utilities for generating Plotly charts"""
    
    @staticmethod
    def bar_chart(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "Bar Chart",
        color_column: Optional[str] = None
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly bar chart
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_column: Column for y-axis
            title: Chart title
            color_column: Optional column for bar colors
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            if color_column:
                fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
            else:
                fig = px.bar(df, x=x_column, y=y_column, title=title)
                
            fig.update_layout(
                title=title,
                xaxis_title=x_column,
                yaxis_title=y_column
            )
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly bar chart: {str(e)}")
            return None
    
    @staticmethod
    def line_chart(
        df: pd.DataFrame,
        x_column: str,
        y_columns: Union[str, List[str]],
        title: str = "Line Chart",
        color_column: Optional[str] = None
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly line chart
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_columns: Column(s) for y-axis
            title: Chart title
            color_column: Optional column for line colors
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            if isinstance(y_columns, str):
                if color_column:
                    fig = px.line(df, x=x_column, y=y_columns, color=color_column, title=title)
                else:
                    fig = px.line(df, x=x_column, y=y_columns, title=title)
            else:
                # For multiple y columns, melt the DataFrame
                id_vars = [x_column]
                if color_column and color_column not in y_columns:
                    id_vars.append(color_column)
                    
                melted_df = pd.melt(df, id_vars=id_vars, value_vars=y_columns, 
                                   var_name='variable', value_name='value')
                
                fig = px.line(melted_df, x=x_column, y='value', color='variable', title=title)
                
            fig.update_layout(
                title=title,
                xaxis_title=x_column,
                yaxis_title='Value' if isinstance(y_columns, list) else y_columns
            )
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly line chart: {str(e)}")
            return None
    
    @staticmethod
    def scatter_plot(
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str = "Scatter Plot",
        color_column: Optional[str] = None,
        size_column: Optional[str] = None
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly scatter plot
        
        Args:
            df: Input DataFrame
            x_column: Column for x-axis
            y_column: Column for y-axis
            title: Chart title
            color_column: Optional column for point colors
            size_column: Optional column for point sizes
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            fig = px.scatter(
                df, 
                x=x_column, 
                y=y_column, 
                color=color_column,
                size=size_column,
                title=title
            )
            
            fig.update_layout(
                title=title,
                xaxis_title=x_column,
                yaxis_title=y_column
            )
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly scatter plot: {str(e)}")
            return None
    
    @staticmethod
    def histogram(
        df: pd.DataFrame,
        column: str,
        title: str = None,
        color_column: Optional[str] = None,
        nbins: int = 30
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly histogram
        
        Args:
            df: Input DataFrame
            column: Column to plot
            title: Chart title (uses column name if None)
            color_column: Optional column for bar colors
            nbins: Number of bins
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            if title is None:
                title = f"Distribution of {column}"
                
            fig = px.histogram(
                df, 
                x=column, 
                color=color_column,
                nbins=nbins,
                title=title
            )
            
            fig.update_layout(
                title=title,
                xaxis_title=column,
                yaxis_title="Count"
            )
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly histogram: {str(e)}")
            return None
    
    @staticmethod
    def pie_chart(
        df: pd.DataFrame,
        column: str,
        title: str = None,
        values_column: Optional[str] = None
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly pie chart
        
        Args:
            df: Input DataFrame
            column: Column for pie segments
            title: Chart title (uses column name if None)
            values_column: Optional column for segment sizes (uses counts if None)
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            if title is None:
                title = f"Distribution of {column}"
                
            if values_column:
                fig = px.pie(df, names=column, values=values_column, title=title)
            else:
                # Count occurrences of each category
                value_counts = df[column].value_counts().reset_index()
                value_counts.columns = [column, 'count']
                fig = px.pie(value_counts, names=column, values='count', title=title)
                
            fig.update_layout(title=title)
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly pie chart: {str(e)}")
            return None
    
    @staticmethod
    def heatmap(
        df: pd.DataFrame,
        title: str = "Heatmap"
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly heatmap
        
        Args:
            df: Input DataFrame (should be a correlation matrix or similar)
            title: Chart title
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            fig = go.Figure(data=go.Heatmap(
                z=df.values,
                x=df.columns,
                y=df.index,
                colorscale='Viridis',
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title="",
                yaxis_title=""
            )
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly heatmap: {str(e)}")
            return None
    
    @staticmethod
    def box_plot(
        df: pd.DataFrame,
        column: Union[str, List[str]],
        by: Optional[str] = None,
        title: str = None
    ) -> Optional[Union['go.Figure', 'px.Figure']]:
        """
        Generate a Plotly box plot
        
        Args:
            df: Input DataFrame
            column: Column(s) to plot
            by: Optional grouping column
            title: Chart title
            
        Returns:
            Plotly figure or None if Plotly is not available
        """
        if not HAS_PLOTLY:
            return None
            
        try:
            if title is None:
                if isinstance(column, str):
                    title = f"Box Plot of {column}"
                else:
                    title = "Box Plot"
                    
            if by is not None:
                fig = px.box(df, x=by, y=column, title=title)
            else:
                if isinstance(column, list):
                    # Melt the DataFrame for multiple columns
                    melted_df = pd.melt(df[column])
                    fig = px.box(melted_df, x='variable', y='value', title=title)
                else:
                    fig = px.box(df, y=column, title=title)
                    
            fig.update_layout(title=title)
            
            return fig
        except Exception as e:
            print(f"Error creating Plotly box plot: {str(e)}")
            return None


# Global service instance
visualization_service = VisualizationService()