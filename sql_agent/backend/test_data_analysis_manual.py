"""
Manual test script for Data Analysis utilities
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from pprint import pprint

# Check for optional dependencies
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("Warning: seaborn not installed. Some visualizations will be simplified.")

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed. Some statistical tests will be skipped.")

# Add parent directory to path to make imports work
sys.path.append('..')

try:
    from sql_agent.backend.services.data_analysis import (
        DataLoader, DataPreprocessor, StatisticalAnalysis, 
        DataAnalysisService, AnalysisResult
    )
    from sql_agent.backend.services.python_interpreter_enhanced import EnhancedPythonInterpreterService
except ImportError:
    # Try relative import
    try:
        from services.data_analysis import (
            DataLoader, DataPreprocessor, StatisticalAnalysis, 
            DataAnalysisService, AnalysisResult
        )
        from services.python_interpreter_enhanced import EnhancedPythonInterpreterService
    except ImportError:
        print("Error: Could not import required modules. Make sure you're running this script from the correct directory.")
        sys.exit(1)


def create_sample_dataframe():
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
    
    # Add some outliers
    df.loc[0, 'value1'] = 200  # Far above mean
    df.loc[1, 'value2'] = 10   # Far below mean
    
    return df


def test_data_preprocessing():
    """Test data preprocessing utilities"""
    print("\n=== Testing Data Preprocessing ===\n")
    
    df = create_sample_dataframe()
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Missing values: {df.isna().sum().sum()}")
    
    # Handle missing values
    df_clean = DataPreprocessor.handle_missing_values(df, strategy='mean')
    print(f"\nAfter handling missing values:")
    print(f"Missing numeric values: {df_clean[['value1', 'value2']].isna().sum().sum()}")
    print(f"Missing categorical values: {df_clean['category'].isna().sum()}")
    
    # Detect outliers
    outliers = DataPreprocessor.detect_outliers(df, method='zscore', threshold=3.0)
    print(f"\nOutliers detected (Z-score method):")
    for col in outliers.columns:
        count = outliers[col].sum()
        if count > 0:
            print(f"  {col}: {count} outliers")
    
    # Normalize data
    df_norm = DataPreprocessor.normalize(df, method='minmax')
    print(f"\nAfter min-max normalization:")
    print(f"  value1 range: [{df_norm['value1'].min():.2f}, {df_norm['value1'].max():.2f}]")
    print(f"  value2 range: [{df_norm['value2'].min():.2f}, {df_norm['value2'].max():.2f}]")
    
    # Encode categorical data
    df_encoded = DataPreprocessor.encode_categorical(df, method='onehot')
    print(f"\nAfter one-hot encoding:")
    print(f"  New columns: {[col for col in df_encoded.columns if col.startswith('category_')]}")


def test_statistical_analysis():
    """Test statistical analysis utilities"""
    print("\n=== Testing Statistical Analysis ===\n")
    
    df = create_sample_dataframe()
    
    # Descriptive statistics
    print("Generating descriptive statistics...")
    stats = StatisticalAnalysis.descriptive_stats(df)
    
    print("\nBasic statistics for 'value1':")
    if 'value1' in stats:
        for stat, value in stats['value1'].items():
            if stat != 'count':  # Skip count which is a nested dictionary
                print(f"  {stat}: {value}")
    
    print("\nAdditional statistics for 'value1':")
    if 'additional' in stats and 'value1' in stats['additional']:
        for stat, value in stats['additional']['value1'].items():
            print(f"  {stat}: {value}")
    
    # Correlation analysis
    print("\nPerforming correlation analysis...")
    corr_result = StatisticalAnalysis.correlation_analysis(df)
    
    if 'top_correlations' in corr_result:
        print("\nTop correlations:")
        for corr in corr_result['top_correlations'][:3]:  # Show top 3
            print(f"  {corr['column1']} - {corr['column2']}: {corr['correlation']:.3f}")
    
    # Distribution analysis
    print("\nAnalyzing distribution of 'value1'...")
    dist_result = StatisticalAnalysis.distribution_analysis(df, 'value1')
    
    if 'statistics' in dist_result:
        print("\nDistribution statistics:")
        for stat, value in dist_result['statistics'].items():
            print(f"  {stat}: {value}")
    
    if 'normality_test' in dist_result and dist_result['normality_test']:
        print("\nNormality test:")
        print(f"  Test: {dist_result['normality_test']['test']}")
        print(f"  p-value: {dist_result['normality_test']['p_value']:.4f}")
        print(f"  Is normal: {dist_result['normality_test']['is_normal']}")


def test_data_analysis_service():
    """Test comprehensive data analysis service"""
    print("\n=== Testing Data Analysis Service ===\n")
    
    df = create_sample_dataframe()
    
    # Analyze DataFrame
    print("Performing comprehensive analysis...")
    result = DataAnalysisService.analyze_dataframe(df)
    
    print(f"\nAnalysis success: {result.success}")
    
    if result.success:
        print(f"\nDataFrame shape: {result.summary['shape']['rows']} rows, {result.summary['shape']['columns']} columns")
        
        print("\nColumn types:")
        for type_name, cols in result.summary['column_types'].items():
            if cols:
                print(f"  {type_name}: {cols}")
        
        print(f"\nMissing values: {result.summary['missing_values']['total']} ({result.summary['missing_values']['percentage']:.2f}%)")
        
        print(f"\nGenerated {len(result.plots)} visualizations")
        
        # Generate insights
        print("\nGenerating insights...")
        insights = DataAnalysisService.generate_insights(df)
        
        print("\nInsights:")
        for i, insight in enumerate(insights, 1):
            print(f"  {i}. {insight}")


async def test_enhanced_python_interpreter():
    """Test enhanced Python interpreter with data analysis integration"""
    print("\n=== Testing Enhanced Python Interpreter ===\n")
    
    service = EnhancedPythonInterpreterService()
    
    code = """
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

# Add some outliers
df.loc[0, 'value1'] = 200  # Far above mean
df.loc[1, 'value2'] = 10   # Far below mean

# Print basic info
print(f"DataFrame shape: {df.shape}")
print(f"DataFrame columns: {df.columns.tolist()}")

# Use data preprocessing utilities
print("\\nPreprocessing data...")
df_clean = DataPreprocessor.handle_missing_values(df, strategy='mean')
df_norm = DataPreprocessor.normalize(df_clean, method='minmax')

# Create a correlation plot
print("\\nCreating correlation plot...")
plt.figure(figsize=(8, 6))
sns.heatmap(df[['value1', 'value2']].corr(), annot=True, cmap='coolwarm')
plt.title('Correlation Heatmap')

# Create a distribution plot
print("\\nCreating distribution plot...")
plt.figure(figsize=(10, 6))
sns.histplot(df['value1'], kde=True)
plt.title('Distribution of value1')

# Use statistical analysis utilities
print("\\nPerforming statistical analysis...")
corr_result = StatisticalAnalysis.correlation_analysis(df)
dist_result = StatisticalAnalysis.distribution_analysis(df, 'value1')

# Generate insights
print("\\nGenerating insights...")
insights = DataAnalysisService.generate_insights(df)
print("\\nTop 3 insights:")
for i, insight in enumerate(insights[:3], 1):
    print(f"{i}. {insight}")
"""
    
    print("Executing Python code with data analysis capabilities...")
    result = await service.execute_code(code)
    
    print(f"\nExecution status: {result.status}")
    print(f"Execution time: {result.execution_time:.2f} seconds")
    print(f"Memory usage: {result.memory_usage:.2f} MB")
    
    print("\nOutput:")
    print(result.output)
    
    print(f"\nGenerated {len(result.plots)} plots")
    
    print("\nAutomatic DataFrame analysis results:")
    for var_name, analysis in result.analysis_results.items():
        print(f"\n  DataFrame: {var_name}")
        if "summary" in analysis:
            print(f"    Rows: {analysis['summary']['shape']['rows']}")
            print(f"    Columns: {analysis['summary']['shape']['columns']}")
            print(f"    Plots: {len(analysis['plots'])}")
            print(f"    Insights: {len(analysis['insights'])}")


async def main():
    """Run all tests"""
    print("=== Data Analysis Utilities Manual Tests ===\n")
    
    test_data_preprocessing()
    test_statistical_analysis()
    test_data_analysis_service()
    await test_enhanced_python_interpreter()
    
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())