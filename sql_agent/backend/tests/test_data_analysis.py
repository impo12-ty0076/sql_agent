"""
Unit tests for Data Analysis utilities
"""

import pytest
import pandas as pd
import numpy as np
import json
import base64
from io import StringIO
import matplotlib.pyplot as plt

from services.data_analysis import (
    DataLoader, DataPreprocessor, StatisticalAnalysis, 
    DataAnalysisService, AnalysisResult
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing"""
    data = {
        'id': range(1, 101),
        'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
        'value1': np.random.normal(100, 15, 100),
        'value2': np.random.normal(50, 5, 100),
        'date': pd.date_range(start='2023-01-01', periods=100)
    }
    df = pd.DataFrame(data)
    
    # Add some missing values
    df.loc[10:15, 'value1'] = np.nan
    df.loc[50:55, 'category'] = np.nan
    
    return df


@pytest.fixture
def query_result_data():
    """Create sample query result data for testing"""
    return {
        'columns': [
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'varchar'},
            {'name': 'amount', 'type': 'float'}
        ],
        'rows': [
            [1, 'Item 1', 10.5],
            [2, 'Item 2', 20.75],
            [3, 'Item 3', 15.25],
            [4, 'Item 4', 30.0],
            [5, 'Item 5', 25.5]
        ]
    }


def test_data_loader_from_query_result(query_result_data):
    """Test loading DataFrame from query result"""
    df = DataLoader.from_query_result(query_result_data)
    
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (5, 3)
    assert list(df.columns) == ['id', 'name', 'amount']
    assert df['id'].dtype == np.int64
    assert df['name'].dtype == object
    assert df['amount'].dtype == np.float64


def test_data_loader_from_csv():
    """Test loading DataFrame from CSV string"""
    csv_data = """id,name,amount
1,Item 1,10.5
2,Item 2,20.75
3,Item 3,15.25
4,Item 4,30.0
5,Item 5,25.5"""
    
    df = DataLoader.from_csv(csv_data)
    
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (5, 3)
    assert list(df.columns) == ['id', 'name', 'amount']


def test_data_loader_from_json():
    """Test loading DataFrame from JSON string"""
    json_data = """[
        {"id": 1, "name": "Item 1", "amount": 10.5},
        {"id": 2, "name": "Item 2", "amount": 20.75},
        {"id": 3, "name": "Item 3", "amount": 15.25},
        {"id": 4, "name": "Item 4", "amount": 30.0},
        {"id": 5, "name": "Item 5", "amount": 25.5}
    ]"""
    
    df = DataLoader.from_json(json_data)
    
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (5, 3)
    assert list(df.columns) == ['id', 'name', 'amount']


def test_data_preprocessor_handle_missing_values(sample_dataframe):
    """Test handling missing values"""
    # Count initial missing values
    initial_missing = sample_dataframe.isna().sum().sum()
    assert initial_missing > 0
    
    # Test drop strategy
    df_drop = DataPreprocessor.handle_missing_values(sample_dataframe, strategy='drop')
    assert df_drop.isna().sum().sum() == 0
    assert df_drop.shape[0] < sample_dataframe.shape[0]
    
    # Test fill strategy
    df_fill = DataPreprocessor.handle_missing_values(sample_dataframe, strategy='fill', fill_value=0)
    assert df_fill.isna().sum().sum() == 0
    assert df_fill.shape == sample_dataframe.shape
    
    # Test mean strategy
    df_mean = DataPreprocessor.handle_missing_values(sample_dataframe, strategy='mean')
    assert df_mean['value1'].isna().sum() == 0
    assert df_mean['value2'].isna().sum() == 0
    # Categorical columns should still have NaN
    assert df_mean['category'].isna().sum() > 0


def test_data_preprocessor_detect_outliers(sample_dataframe):
    """Test outlier detection"""
    # Add some outliers
    sample_dataframe.loc[0, 'value1'] = 200  # Far above mean
    sample_dataframe.loc[1, 'value2'] = 10   # Far below mean
    
    # Test Z-score method
    outliers_z = DataPreprocessor.detect_outliers(sample_dataframe, method='zscore', threshold=3.0)
    assert outliers_z['value1'].sum() >= 1
    assert outliers_z['value2'].sum() >= 1
    
    # Test IQR method
    outliers_iqr = DataPreprocessor.detect_outliers(sample_dataframe, method='iqr', threshold=1.5)
    assert outliers_iqr['value1'].sum() >= 1
    assert outliers_iqr['value2'].sum() >= 1


def test_data_preprocessor_normalize(sample_dataframe):
    """Test data normalization"""
    # Test min-max normalization
    df_minmax = DataPreprocessor.normalize(sample_dataframe, method='minmax')
    assert df_minmax['value1'].min() >= 0
    assert df_minmax['value1'].max() <= 1
    assert df_minmax['value2'].min() >= 0
    assert df_minmax['value2'].max() <= 1
    
    # Test z-score normalization
    df_zscore = DataPreprocessor.normalize(sample_dataframe, method='zscore')
    assert abs(df_zscore['value1'].mean()) < 0.1  # Close to 0
    assert abs(df_zscore['value2'].std() - 1.0) < 0.1  # Close to 1


def test_data_preprocessor_encode_categorical(sample_dataframe):
    """Test categorical encoding"""
    # Test one-hot encoding
    df_onehot = DataPreprocessor.encode_categorical(sample_dataframe, method='onehot')
    assert 'category_A' in df_onehot.columns
    assert 'category_B' in df_onehot.columns
    assert 'category_C' in df_onehot.columns
    assert 'category_D' in df_onehot.columns
    assert 'category' not in df_onehot.columns
    
    # Test label encoding
    df_label = DataPreprocessor.encode_categorical(sample_dataframe, method='label')
    assert 'category' in df_label.columns
    assert df_label['category'].dtype == np.int8  # Categorical codes are integers


def test_statistical_analysis_descriptive_stats(sample_dataframe):
    """Test descriptive statistics generation"""
    stats = StatisticalAnalysis.descriptive_stats(sample_dataframe)
    
    assert 'count' in stats
    assert 'mean' in stats
    assert 'std' in stats
    assert 'min' in stats
    assert 'max' in stats
    assert 'additional' in stats
    assert 'categorical' in stats
    
    # Check additional stats for numeric columns
    assert 'value1' in stats['additional']
    assert 'skewness' in stats['additional']['value1']
    assert 'kurtosis' in stats['additional']['value1']
    
    # Check categorical stats
    assert 'category' in stats['categorical']
    assert 'unique_count' in stats['categorical']['category']
    assert 'top_values' in stats['categorical']['category']


def test_statistical_analysis_correlation_analysis(sample_dataframe):
    """Test correlation analysis"""
    corr_result = StatisticalAnalysis.correlation_analysis(sample_dataframe)
    
    assert 'correlation_matrix' in corr_result
    assert 'visualization' in corr_result
    assert 'top_correlations' in corr_result
    
    # Check visualization
    assert corr_result['visualization']['type'] == 'heatmap'
    assert 'data' in corr_result['visualization']
    assert 'format' in corr_result['visualization']
    
    # Verify base64 encoding
    img_data = corr_result['visualization']['data']
    try:
        base64.b64decode(img_data)
    except:
        pytest.fail("Visualization data is not valid base64")


def test_statistical_analysis_time_series_analysis(sample_dataframe):
    """Test time series analysis"""
    ts_result = StatisticalAnalysis.time_series_analysis(
        sample_dataframe, date_column='date', value_column='value1'
    )
    
    assert 'time_series_stats' in ts_result
    assert 'visualization' in ts_result
    
    # Check time series stats
    stats = ts_result['time_series_stats']
    assert 'start_date' in stats
    assert 'end_date' in stats
    assert 'duration_days' in stats
    assert 'data_points' in stats
    assert 'trend' in stats
    
    # Check visualization
    assert ts_result['visualization']['type'] == 'time_series'
    assert 'data' in ts_result['visualization']
    assert 'format' in ts_result['visualization']


def test_statistical_analysis_distribution_analysis_numeric(sample_dataframe):
    """Test distribution analysis for numeric column"""
    dist_result = StatisticalAnalysis.distribution_analysis(sample_dataframe, 'value1')
    
    assert dist_result['type'] == 'numeric'
    assert 'statistics' in dist_result
    assert 'visualization' in dist_result
    
    # Check statistics
    stats = dist_result['statistics']
    assert 'mean' in stats
    assert 'median' in stats
    assert 'std' in stats
    assert 'skewness' in stats
    assert 'kurtosis' in stats
    
    # Check visualization
    assert dist_result['visualization']['type'] == 'distribution'
    assert 'data' in dist_result['visualization']
    assert 'format' in dist_result['visualization']


def test_statistical_analysis_distribution_analysis_categorical(sample_dataframe):
    """Test distribution analysis for categorical column"""
    dist_result = StatisticalAnalysis.distribution_analysis(sample_dataframe, 'category')
    
    assert dist_result['type'] == 'categorical'
    assert 'statistics' in dist_result
    assert 'value_counts' in dist_result
    assert 'visualization' in dist_result
    
    # Check statistics
    stats = dist_result['statistics']
    assert 'unique_values' in stats
    assert 'most_common' in stats
    assert 'most_common_count' in stats
    
    # Check visualization
    assert dist_result['visualization']['type'] == 'bar_chart'
    assert 'data' in dist_result['visualization']
    assert 'format' in dist_result['visualization']


def test_data_analysis_service_analyze_dataframe(sample_dataframe):
    """Test comprehensive DataFrame analysis"""
    result = DataAnalysisService.analyze_dataframe(sample_dataframe)
    
    assert isinstance(result, AnalysisResult)
    assert result.success is True
    assert result.data is not None
    assert result.summary is not None
    assert result.plots is not None
    
    # Check summary structure
    assert 'shape' in result.summary
    assert 'column_types' in result.summary
    assert 'missing_values' in result.summary
    assert 'statistics' in result.summary
    
    # Check plots
    assert len(result.plots) > 0
    for plot in result.plots:
        assert 'type' in plot
        assert 'data' in plot
        assert 'format' in plot


def test_data_analysis_service_generate_insights(sample_dataframe):
    """Test insight generation"""
    insights = DataAnalysisService.generate_insights(sample_dataframe)
    
    assert isinstance(insights, list)
    assert len(insights) > 0
    
    # Check for common insight types
    has_shape_insight = any('rows and' in insight for insight in insights)
    assert has_shape_insight, "Should include insight about DataFrame shape"
    
    # Add an outlier and check for outlier insight
    sample_dataframe.loc[0, 'value1'] = 500  # Extreme outlier
    insights = DataAnalysisService.generate_insights(sample_dataframe)
    has_outlier_insight = any('outlier' in insight.lower() for insight in insights)
    assert has_outlier_insight, "Should include insight about outliers"


if __name__ == "__main__":
    pytest.main([__file__])