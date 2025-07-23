"""
Data Analysis Utilities

This module provides utilities for data loading, preprocessing, and statistical analysis
using pandas, numpy, and other data analysis libraries.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union, Optional, Tuple
import json
from io import StringIO, BytesIO
import base64
import matplotlib.pyplot as plt
import warnings
from dataclasses import dataclass

# Optional imports with fallbacks
try:
    import seaborn as sns
except ImportError:
    sns = None

try:
    from scipy import stats
except ImportError:
    stats = None


@dataclass
class AnalysisResult:
    """Result of a data analysis operation"""
    success: bool
    data: Optional[pd.DataFrame] = None
    summary: Optional[Dict[str, Any]] = None
    plots: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DataLoader:
    """Utilities for loading data from various sources into pandas DataFrames"""
    
    @staticmethod
    def from_query_result(data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert SQL query result to pandas DataFrame
        
        Args:
            data: Dictionary containing 'columns' and 'rows' from SQL query result
            
        Returns:
            pandas DataFrame
        """
        try:
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
                
            if 'columns' not in data or 'rows' not in data:
                raise ValueError("Data must contain 'columns' and 'rows' keys")
                
            columns = [col['name'] for col in data['columns']]
            df = pd.DataFrame(data['rows'], columns=columns)
            
            # Try to convert numeric columns
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails
                    
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to convert query result to DataFrame: {str(e)}")
    
    @staticmethod
    def from_csv(csv_data: str, **kwargs) -> pd.DataFrame:
        """
        Load data from CSV string
        
        Args:
            csv_data: CSV data as string
            **kwargs: Additional arguments to pass to pd.read_csv
            
        Returns:
            pandas DataFrame
        """
        try:
            return pd.read_csv(StringIO(csv_data), **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to load CSV data: {str(e)}")
    
    @staticmethod
    def from_json(json_data: str, **kwargs) -> pd.DataFrame:
        """
        Load data from JSON string
        
        Args:
            json_data: JSON data as string
            **kwargs: Additional arguments to pass to pd.read_json
            
        Returns:
            pandas DataFrame
        """
        try:
            return pd.read_json(json_data, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to load JSON data: {str(e)}")
    
    @staticmethod
    def from_excel(excel_data: bytes, **kwargs) -> pd.DataFrame:
        """
        Load data from Excel bytes
        
        Args:
            excel_data: Excel data as bytes
            **kwargs: Additional arguments to pass to pd.read_excel
            
        Returns:
            pandas DataFrame
        """
        try:
            return pd.read_excel(BytesIO(excel_data), **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to load Excel data: {str(e)}")

class DataPreprocessor:
    """Utilities for preprocessing and cleaning data"""
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop', 
                             fill_value: Any = None) -> pd.DataFrame:
        """
        Handle missing values in DataFrame
        
        Args:
            df: Input DataFrame
            strategy: Strategy for handling missing values ('drop', 'fill', 'mean', 'median', 'mode')
            fill_value: Value to use for filling if strategy is 'fill'
            
        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df
            
        if strategy == 'drop':
            return df.dropna()
        elif strategy == 'fill' and fill_value is not None:
            return df.fillna(fill_value)
        elif strategy == 'mean':
            return df.fillna(df.mean(numeric_only=True))
        elif strategy == 'median':
            return df.fillna(df.median(numeric_only=True))
        elif strategy == 'mode':
            # For each column, fill with the most frequent value
            result = df.copy()
            for col in df.columns:
                if df[col].isna().any():
                    mode_value = df[col].mode()
                    if not mode_value.empty:
                        result[col] = result[col].fillna(mode_value[0])
            return result
        else:
            raise ValueError(f"Unsupported missing value strategy: {strategy}")
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, method: str = 'zscore', 
                       threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect outliers in numeric columns
        
        Args:
            df: Input DataFrame
            method: Method for outlier detection ('zscore', 'iqr')
            threshold: Threshold for outlier detection
            
        Returns:
            DataFrame with boolean mask indicating outliers
        """
        if df.empty:
            return pd.DataFrame()
            
        result = pd.DataFrame(index=df.index)
        
        for col in df.select_dtypes(include=np.number).columns:
            if method == 'zscore':
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    z_scores = np.abs(stats.zscore(df[col], nan_policy='omit'))
                    result[col] = z_scores > threshold
            elif method == 'iqr':
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                result[col] = (df[col] < lower_bound) | (df[col] > upper_bound)
            else:
                raise ValueError(f"Unsupported outlier detection method: {method}")
                
        return result
    
    @staticmethod
    def remove_outliers(df: pd.DataFrame, method: str = 'zscore', 
                       threshold: float = 3.0) -> pd.DataFrame:
        """
        Remove outliers from numeric columns
        
        Args:
            df: Input DataFrame
            method: Method for outlier detection ('zscore', 'iqr')
            threshold: Threshold for outlier detection
            
        Returns:
            DataFrame with outliers removed
        """
        outliers = DataPreprocessor.detect_outliers(df, method, threshold)
        
        if outliers.empty:
            return df
            
        # Create a mask where True means keep the row (not an outlier in any column)
        mask = ~outliers.any(axis=1)
        return df[mask]
    
    @staticmethod
    def normalize(df: pd.DataFrame, method: str = 'minmax', 
                 columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Normalize numeric columns in DataFrame
        
        Args:
            df: Input DataFrame
            method: Normalization method ('minmax', 'zscore')
            columns: List of columns to normalize (None for all numeric)
            
        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df
            
        result = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=np.number).columns
        else:
            # Filter to only include numeric columns from the provided list
            columns = [col for col in columns if col in df.select_dtypes(include=np.number).columns]
            
        for col in columns:
            if method == 'minmax':
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:  # Avoid division by zero
                    result[col] = (df[col] - min_val) / (max_val - min_val)
            elif method == 'zscore':
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:  # Avoid division by zero
                    result[col] = (df[col] - mean) / std
            else:
                raise ValueError(f"Unsupported normalization method: {method}")
                
        return result
    
    @staticmethod
    def encode_categorical(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                          method: str = 'onehot') -> pd.DataFrame:
        """
        Encode categorical columns
        
        Args:
            df: Input DataFrame
            columns: List of columns to encode (None for all object/category)
            method: Encoding method ('onehot', 'label')
            
        Returns:
            DataFrame with encoded categorical columns
        """
        if df.empty:
            return df
            
        result = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=['object', 'category']).columns
        
        if method == 'onehot':
            # One-hot encode each specified column
            for col in columns:
                if col in result.columns:
                    dummies = pd.get_dummies(result[col], prefix=col)
                    result = pd.concat([result.drop(col, axis=1), dummies], axis=1)
        elif method == 'label':
            # Label encode each specified column
            for col in columns:
                if col in result.columns:
                    categories = result[col].astype('category').cat.categories
                    result[col] = result[col].astype('category').cat.codes
                    # Store category mapping as attribute
                    result[f"{col}_categories"] = list(categories)
        else:
            raise ValueError(f"Unsupported encoding method: {method}")
            
        return result
class StatisticalAnalysis:
    """Statistical analysis utilities"""
    
    @staticmethod
    def descriptive_stats(df: pd.DataFrame, include_percentiles: bool = True) -> Dict[str, Any]:
        """
        Generate descriptive statistics for DataFrame
        
        Args:
            df: Input DataFrame
            include_percentiles: Whether to include percentiles in the statistics
            
        Returns:
            Dictionary of descriptive statistics
        """
        if df.empty:
            return {"error": "Empty DataFrame"}
            
        try:
            # Basic statistics
            stats_df = df.describe(include='all', percentiles=[.01, .05, .25, .5, .75, .95, .99] 
                                  if include_percentiles else None)
            
            # Additional statistics for numeric columns
            numeric_cols = df.select_dtypes(include=np.number).columns
            additional_stats = {}
            
            for col in numeric_cols:
                col_stats = {
                    'skewness': float(df[col].skew()),
                    'kurtosis': float(df[col].kurtosis()),
                    'iqr': float(df[col].quantile(0.75) - df[col].quantile(0.25)),
                    'missing_count': int(df[col].isna().sum()),
                    'missing_percent': float(df[col].isna().mean() * 100)
                }
                additional_stats[col] = col_stats
                
            # Convert to dictionary
            result = json.loads(stats_df.to_json())
            result['additional'] = additional_stats
            
            # Add categorical column statistics
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            cat_stats = {}
            
            for col in cat_cols:
                value_counts = df[col].value_counts()
                unique_count = len(value_counts)
                
                cat_stats[col] = {
                    'unique_count': unique_count,
                    'top_values': value_counts.head(5).to_dict(),
                    'missing_count': int(df[col].isna().sum()),
                    'missing_percent': float(df[col].isna().mean() * 100)
                }
                
            result['categorical'] = cat_stats
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to generate descriptive statistics: {str(e)}"}
    
    @staticmethod
    def correlation_analysis(df: pd.DataFrame, method: str = 'pearson') -> Dict[str, Any]:
        """
        Perform correlation analysis on numeric columns
        
        Args:
            df: Input DataFrame
            method: Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Dictionary with correlation matrix and visualization
        """
        if df.empty:
            return {"error": "Empty DataFrame"}
            
        try:
            # Select numeric columns
            numeric_df = df.select_dtypes(include=np.number)
            
            if numeric_df.empty:
                return {"error": "No numeric columns for correlation analysis"}
                
            # Calculate correlation matrix
            corr_matrix = numeric_df.corr(method=method)
            
            # Generate correlation heatmap
            plt.figure(figsize=(10, 8))
            if sns is not None:
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
            else:
                # Fallback if seaborn is not available
                plt.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
                plt.colorbar()
                for i in range(len(corr_matrix.columns)):
                    for j in range(len(corr_matrix.columns)):
                        plt.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}", 
                                ha="center", va="center", color="black")
            plt.title(f'{method.capitalize()} Correlation Matrix')
            plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45)
            plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)
            plt.tight_layout()
            
            # Save figure to bytes
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            img_buffer.seek(0)
            
            # Encode as base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close()
            
            # Find strongest correlations
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]
                    corr_pairs.append((col1, col2, corr_value))
            
            # Sort by absolute correlation value
            corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            # Get top correlations
            top_correlations = [
                {"column1": str(col1), "column2": str(col2), "correlation": float(corr)}
                for col1, col2, corr in corr_pairs[:10]  # Top 10
            ]
            
            return {
                "correlation_matrix": json.loads(corr_matrix.to_json()),
                "visualization": {
                    "type": "heatmap",
                    "data": img_base64,
                    "format": "png"
                },
                "top_correlations": top_correlations
            }
            
        except Exception as e:
            return {"error": f"Failed to perform correlation analysis: {str(e)}"}
    
    @staticmethod
    def time_series_analysis(df: pd.DataFrame, date_column: str, 
                            value_column: str) -> Dict[str, Any]:
        """
        Perform time series analysis
        
        Args:
            df: Input DataFrame
            date_column: Name of the date/time column
            value_column: Name of the value column to analyze
            
        Returns:
            Dictionary with time series analysis results
        """
        if df.empty:
            return {"error": "Empty DataFrame"}
            
        try:
            # Check if columns exist
            if date_column not in df.columns:
                return {"error": f"Date column '{date_column}' not found"}
                
            if value_column not in df.columns:
                return {"error": f"Value column '{value_column}' not found"}
                
            # Convert date column to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                try:
                    df[date_column] = pd.to_datetime(df[date_column])
                except:
                    return {"error": f"Could not convert '{date_column}' to datetime"}
            
            # Sort by date
            df = df.sort_values(by=date_column)
            
            # Set date as index for resampling
            ts_df = df[[date_column, value_column]].set_index(date_column)
            
            # Determine appropriate frequency
            date_range = df[date_column].max() - df[date_column].min()
            
            if date_range.days > 365*2:  # More than 2 years
                freq = 'M'  # Monthly
                freq_name = "Monthly"
            elif date_range.days > 60:  # More than 2 months
                freq = 'W'  # Weekly
                freq_name = "Weekly"
            elif date_range.days > 5:  # More than 5 days
                freq = 'D'  # Daily
                freq_name = "Daily"
            else:
                freq = 'H'  # Hourly
                freq_name = "Hourly"
                
            # Resample to regular frequency
            try:
                resampled = ts_df.resample(freq).mean()
            except:
                # If resampling fails, just use original data
                resampled = ts_df
                freq_name = "Original"
            
            # Calculate rolling statistics
            window_size = max(3, len(resampled) // 10)  # At least 3, or 10% of data points
            rolling_mean = resampled[value_column].rolling(window=window_size).mean()
            rolling_std = resampled[value_column].rolling(window=window_size).std()
            
            # Plot time series with rolling statistics
            plt.figure(figsize=(12, 6))
            plt.plot(resampled.index, resampled[value_column], label='Original')
            plt.plot(resampled.index, rolling_mean, label=f'{window_size}-period Rolling Mean')
            plt.plot(resampled.index, rolling_std, label=f'{window_size}-period Rolling Std')
            plt.title(f'Time Series Analysis: {value_column} over Time')
            plt.xlabel('Date')
            plt.ylabel(value_column)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            
            # Save figure to bytes
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            img_buffer.seek(0)
            
            # Encode as base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close()
            
            # Calculate basic time series statistics
            ts_stats = {
                "start_date": df[date_column].min().isoformat(),
                "end_date": df[date_column].max().isoformat(),
                "duration_days": (df[date_column].max() - df[date_column].min()).days,
                "data_points": len(df),
                "resampling_frequency": freq_name,
                "min_value": float(df[value_column].min()),
                "max_value": float(df[value_column].max()),
                "mean_value": float(df[value_column].mean()),
                "trend": "increasing" if resampled[value_column].iloc[-1] > resampled[value_column].iloc[0] else "decreasing"
            }
            
            # Try to detect seasonality if enough data points
            seasonality = None
            if len(resampled) >= 12:
                try:
                    # Simple autocorrelation to detect seasonality
                    autocorr = pd.Series(resampled[value_column]).autocorr(lag=1)
                    seasonality = {
                        "autocorrelation": float(autocorr),
                        "has_seasonality": abs(autocorr) > 0.5
                    }
                except:
                    pass
            
            return {
                "time_series_stats": ts_stats,
                "seasonality": seasonality,
                "visualization": {
                    "type": "time_series",
                    "data": img_base64,
                    "format": "png"
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to perform time series analysis: {str(e)}"}
    @staticmethod
    def distribution_analysis(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Analyze the distribution of a column
        
        Args:
            df: Input DataFrame
            column: Column to analyze
            
        Returns:
            Dictionary with distribution analysis results
        """
        if df.empty:
            return {"error": "Empty DataFrame"}
            
        try:
            # Check if column exists
            if column not in df.columns:
                return {"error": f"Column '{column}' not found"}
                
            # Get column data
            data = df[column].dropna()
            
            if len(data) == 0:
                return {"error": f"Column '{column}' contains only NaN values"}
                
            # Determine if numeric or categorical
            is_numeric = pd.api.types.is_numeric_dtype(data)
            
            if is_numeric:
                # Numeric distribution analysis
                
                # Calculate statistics
                stats = {
                    "mean": float(data.mean()),
                    "median": float(data.median()),
                    "std": float(data.std()),
                    "min": float(data.min()),
                    "max": float(data.max()),
                    "skewness": float(data.skew()),
                    "kurtosis": float(data.kurtosis()),
                    "q1": float(data.quantile(0.25)),
                    "q3": float(data.quantile(0.75)),
                }
                
                # Create histogram and KDE plot
                plt.figure(figsize=(12, 6))
                
                # Left subplot: Histogram with KDE
                plt.subplot(1, 2, 1)
                if sns is not None:
                    sns.histplot(data, kde=True)
                else:
                    # Fallback if seaborn is not available
                    plt.hist(data, bins=30, alpha=0.7)
                    # We can't do KDE without seaborn or scipy easily
                plt.title(f'Distribution of {column}')
                plt.xlabel(column)
                plt.ylabel('Frequency')
                
                # Right subplot: Box plot
                plt.subplot(1, 2, 2)
                if sns is not None:
                    sns.boxplot(x=data)
                else:
                    # Fallback if seaborn is not available
                    plt.boxplot(data)
                plt.title(f'Box Plot of {column}')
                plt.xlabel(column)
                
                plt.tight_layout()
                
                # Save figure to bytes
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
                img_buffer.seek(0)
                
                # Encode as base64
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                plt.close()
                
                # Test for normality
                normality_test = None
                if stats is not None:
                    try:
                        shapiro_test = stats.shapiro(data)
                        normality_test = {
                            "test": "Shapiro-Wilk",
                            "statistic": float(shapiro_test[0]),
                            "p_value": float(shapiro_test[1]),
                            "is_normal": shapiro_test[1] > 0.05
                        }
                    except:
                        pass
                
                return {
                    "type": "numeric",
                    "statistics": stats,
                    "normality_test": normality_test,
                    "visualization": {
                        "type": "distribution",
                        "data": img_base64,
                        "format": "png"
                    }
                }
                
            else:
                # Categorical distribution analysis
                
                # Get value counts
                value_counts = data.value_counts()
                
                # Calculate statistics
                stats = {
                    "unique_values": int(len(value_counts)),
                    "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    "most_common_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    "most_common_percentage": float(value_counts.iloc[0] / len(data) * 100) if len(value_counts) > 0 else 0,
                }
                
                # Create bar plot
                plt.figure(figsize=(12, 6))
                
                # Limit to top 20 categories if there are too many
                if len(value_counts) > 20:
                    value_counts = value_counts.head(20)
                    plt.title(f'Top 20 Categories in {column}')
                else:
                    plt.title(f'Distribution of {column}')
                
                if sns is not None:
                    sns.barplot(x=value_counts.index, y=value_counts.values)
                else:
                    # Fallback if seaborn is not available
                    plt.bar(range(len(value_counts)), value_counts.values)
                    plt.xticks(range(len(value_counts)), value_counts.index)
                plt.xlabel(column)
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                # Save figure to bytes
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
                img_buffer.seek(0)
                
                # Encode as base64
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                plt.close()
                
                return {
                    "type": "categorical",
                    "statistics": stats,
                    "value_counts": value_counts.head(20).to_dict(),
                    "visualization": {
                        "type": "bar_chart",
                        "data": img_base64,
                        "format": "png"
                    }
                }
                
        except Exception as e:
            return {"error": f"Failed to analyze distribution: {str(e)}"}


class DataAnalysisService:
    """Service for performing data analysis operations"""
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> AnalysisResult:
        """
        Perform comprehensive analysis on a DataFrame
        
        Args:
            df: Input DataFrame
            
        Returns:
            AnalysisResult with analysis results
        """
        if df is None or df.empty:
            return AnalysisResult(
                success=False,
                error="Empty or None DataFrame provided"
            )
            
        try:
            # Generate descriptive statistics
            stats = StatisticalAnalysis.descriptive_stats(df)
            
            # Generate plots
            plots = []
            
            # 1. Correlation heatmap for numeric columns
            if len(df.select_dtypes(include=np.number).columns) >= 2:
                corr_result = StatisticalAnalysis.correlation_analysis(df)
                if 'error' not in corr_result:
                    plots.append(corr_result['visualization'])
            
            # 2. Distribution plots for key numeric columns (up to 3)
            numeric_cols = df.select_dtypes(include=np.number).columns[:3]  # Limit to 3
            for col in numeric_cols:
                dist_result = StatisticalAnalysis.distribution_analysis(df, col)
                if 'error' not in dist_result:
                    plots.append(dist_result['visualization'])
            
            # 3. Time series plot if datetime column exists
            datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if datetime_cols and len(df.select_dtypes(include=np.number).columns) > 0:
                date_col = datetime_cols[0]
                value_col = df.select_dtypes(include=np.number).columns[0]
                ts_result = StatisticalAnalysis.time_series_analysis(df, date_col, value_col)
                if 'error' not in ts_result:
                    plots.append(ts_result['visualization'])
            
            # Create summary
            summary = {
                "shape": {
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1])
                },
                "column_types": {
                    "numeric": list(df.select_dtypes(include=np.number).columns),
                    "categorical": list(df.select_dtypes(include=['object', 'category']).columns),
                    "datetime": datetime_cols,
                    "boolean": list(df.select_dtypes(include=bool).columns)
                },
                "missing_values": {
                    "total": int(df.isna().sum().sum()),
                    "percentage": float(df.isna().mean().mean() * 100),
                    "by_column": df.isna().sum().to_dict()
                },
                "statistics": stats
            }
            
            return AnalysisResult(
                success=True,
                data=df,
                summary=summary,
                plots=plots
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )
    
    @staticmethod
    def generate_insights(df: pd.DataFrame) -> List[str]:
        """
        Generate insights from DataFrame
        
        Args:
            df: Input DataFrame
            
        Returns:
            List of insight strings
        """
        if df is None or df.empty:
            return ["No data available for insights"]
            
        insights = []
        
        try:
            # Basic dataset insights
            insights.append(f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns")
            
            # Missing values
            missing_count = df.isna().sum().sum()
            if missing_count > 0:
                missing_pct = missing_count / (df.shape[0] * df.shape[1]) * 100
                insights.append(f"Dataset contains {missing_count} missing values ({missing_pct:.1f}% of all values)")
                
                # Columns with most missing values
                missing_by_col = df.isna().sum()
                missing_cols = missing_by_col[missing_by_col > 0].sort_values(ascending=False)
                if not missing_cols.empty:
                    col = missing_cols.index[0]
                    pct = missing_cols.iloc[0] / df.shape[0] * 100
                    insights.append(f"Column '{col}' has the most missing values: {missing_cols.iloc[0]} ({pct:.1f}%)")
            
            # Numeric columns insights
            num_cols = df.select_dtypes(include=np.number).columns
            if len(num_cols) > 0:
                # Find column with highest variance
                variances = df[num_cols].var()
                if not variances.empty:
                    max_var_col = variances.idxmax()
                    insights.append(f"Column '{max_var_col}' has the highest variance")
                
                # Find outliers
                for col in num_cols[:3]:  # Check up to 3 columns
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    outlier_count = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
                    if outlier_count > 0:
                        outlier_pct = outlier_count / df.shape[0] * 100
                        insights.append(f"Column '{col}' contains {outlier_count} outliers ({outlier_pct:.1f}% of values)")
            
            # Correlation insights
            if len(num_cols) >= 2:
                corr_matrix = df[num_cols].corr()
                # Get the highest correlation (excluding self-correlations)
                np.fill_diagonal(corr_matrix.values, 0)
                max_corr = corr_matrix.max().max()
                if max_corr > 0.7:  # Strong positive correlation
                    # Find which columns have this correlation
                    for i, col1 in enumerate(corr_matrix.columns):
                        for j, col2 in enumerate(corr_matrix.columns):
                            if i != j and corr_matrix.iloc[i, j] == max_corr:
                                insights.append(f"Strong positive correlation ({max_corr:.2f}) between '{col1}' and '{col2}'")
                                break
                
                min_corr = corr_matrix.min().min()
                if min_corr < -0.7:  # Strong negative correlation
                    # Find which columns have this correlation
                    for i, col1 in enumerate(corr_matrix.columns):
                        for j, col2 in enumerate(corr_matrix.columns):
                            if i != j and corr_matrix.iloc[i, j] == min_corr:
                                insights.append(f"Strong negative correlation ({min_corr:.2f}) between '{col1}' and '{col2}'")
                                break
            
            # Categorical columns insights
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                for col in cat_cols[:3]:  # Check up to 3 columns
                    value_counts = df[col].value_counts()
                    if len(value_counts) > 0:
                        top_value = value_counts.index[0]
                        top_count = value_counts.iloc[0]
                        top_pct = top_count / df.shape[0] * 100
                        insights.append(f"Most frequent value in '{col}' is '{top_value}' with {top_count} occurrences ({top_pct:.1f}%)")
                        
                        # Check for imbalance
                        if top_pct > 90:
                            insights.append(f"Column '{col}' is highly imbalanced with '{top_value}' representing {top_pct:.1f}% of values")
            
            # Time series insights
            datetime_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
            if datetime_cols and len(num_cols) > 0:
                date_col = datetime_cols[0]
                # Find min and max dates
                min_date = df[date_col].min()
                max_date = df[date_col].max()
                date_range = max_date - min_date
                insights.append(f"Time series data spans {date_range.days} days from {min_date.date()} to {max_date.date()}")
                
                # Check for time series patterns with a numeric column
                value_col = num_cols[0]
                df_sorted = df.sort_values(by=date_col)
                first_value = df_sorted[value_col].iloc[0]
                last_value = df_sorted[value_col].iloc[-1]
                change_pct = (last_value - first_value) / first_value * 100 if first_value != 0 else float('inf')
                
                if change_pct > 0:
                    insights.append(f"'{value_col}' shows an overall increase of {change_pct:.1f}% over the time period")
                elif change_pct < 0:
                    insights.append(f"'{value_col}' shows an overall decrease of {abs(change_pct):.1f}% over the time period")
            
            return insights
            
        except Exception as e:
            return [f"Error generating insights: {str(e)}"]