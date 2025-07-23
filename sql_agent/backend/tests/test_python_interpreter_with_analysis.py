"""
Unit tests for Enhanced Python Interpreter with Data Analysis Integration
"""

import pytest
import asyncio
import pandas as pd
import numpy as np
import json
import time
from unittest.mock import patch, MagicMock

from services.python_interpreter_enhanced import (
    EnhancedPythonInterpreterService,
    ExecutionConfig,
    ExecutionStatus,
    ExecutionResult
)


@pytest.fixture
def sample_dataframe_code():
    """Python code that creates a sample DataFrame"""
    return """
import pandas as pd
import numpy as np

# Create a sample DataFrame
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

# Print basic info
print(f"DataFrame shape: {df.shape}")
print(f"DataFrame columns: {df.columns.tolist()}")
print(f"Missing values: {df.isna().sum().sum()}")
"""


@pytest.fixture
def data_analysis_code():
    """Python code that performs data analysis"""
    return """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Create a sample DataFrame
data = {
    'id': range(1, 101),
    'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
    'value1': np.random.normal(100, 15, 100),
    'value2': np.random.normal(50, 5, 100),
    'date': pd.date_range(start='2023-01-01', periods=100)
}
df = pd.DataFrame(data)

# Use data preprocessing utilities
df_clean = DataPreprocessor.handle_missing_values(df, strategy='mean')
df_norm = DataPreprocessor.normalize(df_clean, method='minmax')

# Create a correlation plot
plt.figure(figsize=(8, 6))
sns.heatmap(df[['value1', 'value2']].corr(), annot=True, cmap='coolwarm')
plt.title('Correlation Heatmap')

# Create a distribution plot
plt.figure(figsize=(10, 6))
sns.histplot(df['value1'], kde=True)
plt.title('Distribution of value1')

# Use statistical analysis utilities
corr_result = StatisticalAnalysis.correlation_analysis(df)
dist_result = StatisticalAnalysis.distribution_analysis(df, 'value1')

# Generate insights
insights = DataAnalysisService.generate_insights(df)
print("Generated insights:")
for i, insight in enumerate(insights, 1):
    print(f"{i}. {insight}")
"""


@pytest.mark.asyncio
async def test_execute_dataframe_creation(sample_dataframe_code):
    """Test executing code that creates a DataFrame"""
    service = EnhancedPythonInterpreterService()
    
    result = await service.execute_code(sample_dataframe_code)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert "DataFrame shape: (100, 5)" in result.output
    assert "df" in result.variables
    assert isinstance(result.variables["df"], pd.DataFrame)
    
    # Check that analysis results were generated
    assert "df" in result.analysis_results
    assert "summary" in result.analysis_results["df"]
    assert "insights" in result.analysis_results["df"]
    assert "plots" in result.analysis_results["df"]
    
    # Check summary structure
    summary = result.analysis_results["df"]["summary"]
    assert "shape" in summary
    assert "column_types" in summary
    assert "missing_values" in summary
    assert "statistics" in summary
    
    # Check that insights were generated
    insights = result.analysis_results["df"]["insights"]
    assert isinstance(insights, list)
    assert len(insights) > 0


@pytest.mark.asyncio
async def test_execute_data_analysis(data_analysis_code):
    """Test executing code that performs data analysis"""
    service = EnhancedPythonInterpreterService()
    
    result = await service.execute_code(data_analysis_code)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert "Generated insights:" in result.output
    assert "df" in result.variables
    assert "df_clean" in result.variables
    assert "df_norm" in result.variables
    assert "corr_result" in result.variables
    assert "dist_result" in result.variables
    assert "insights" in result.variables
    
    # Check that plots were captured
    assert len(result.plots) >= 2  # Should have at least 2 plots
    
    # Check that analysis results were generated
    assert "df" in result.analysis_results
    assert "df_clean" in result.analysis_results
    assert "df_norm" in result.analysis_results


@pytest.mark.asyncio
async def test_data_analysis_utilities_available():
    """Test that data analysis utilities are available in execution environment"""
    service = EnhancedPythonInterpreterService()
    
    code = """
# Check if data analysis utilities are available
utilities = [
    'DataLoader', 'DataPreprocessor', 'StatisticalAnalysis', 'DataAnalysisService'
]

available = {}
for util in utilities:
    try:
        available[util] = util in globals() and globals()[util] is not None
    except:
        available[util] = False

print(f"Available utilities: {available}")
"""
    
    result = await service.execute_code(code)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert "Available utilities:" in result.output
    
    # All utilities should be available
    for util in ['DataLoader', 'DataPreprocessor', 'StatisticalAnalysis', 'DataAnalysisService']:
        assert f"'{util}': True" in result.output


@pytest.mark.asyncio
async def test_analyze_dataframes_method():
    """Test the _analyze_dataframes method directly"""
    service = EnhancedPythonInterpreterService()
    
    # Create test variables with DataFrames
    variables = {
        "df1": pd.DataFrame({
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50]
        }),
        "df2": pd.DataFrame({
            "X": ["a", "b", "c"],
            "Y": [True, False, True]
        }),
        "not_df": "This is not a DataFrame",
        "empty_df": pd.DataFrame()
    }
    
    analysis_results = service._analyze_dataframes(variables)
    
    # Check that both DataFrames were analyzed
    assert "df1" in analysis_results
    assert "df2" in analysis_results
    assert "not_df" not in analysis_results
    
    # Check that empty DataFrame was not analyzed
    assert "empty_df" not in analysis_results
    
    # Check analysis results structure
    assert "summary" in analysis_results["df1"]
    assert "plots" in analysis_results["df1"]
    assert "insights" in analysis_results["df1"]


@pytest.mark.asyncio
async def test_large_dataframe_analysis_skipped():
    """Test that analysis is skipped for very large DataFrames"""
    service = EnhancedPythonInterpreterService()
    
    code = """
import pandas as pd
import numpy as np

# Create a large DataFrame (1M+ cells)
large_df = pd.DataFrame(np.random.rand(2000, 1000))
print(f"Large DataFrame shape: {large_df.shape}")

# Create a small DataFrame for comparison
small_df = pd.DataFrame(np.random.rand(10, 5))
print(f"Small DataFrame shape: {small_df.shape}")
"""
    
    result = await service.execute_code(code)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert "large_df" in result.variables
    assert "small_df" in result.variables
    
    # Check that analysis was skipped for large DataFrame
    assert "large_df" in result.analysis_results
    assert "skipped" in result.analysis_results["large_df"]
    assert result.analysis_results["large_df"]["skipped"] is True
    
    # Check that small DataFrame was analyzed
    assert "small_df" in result.analysis_results
    assert "summary" in result.analysis_results["small_df"]


if __name__ == "__main__":
    pytest.main([__file__])