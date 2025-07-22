import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import only the query module
    from models.query import (
        Query, QueryStatus, QueryResult, ResultColumn, 
        Report, Visualization, VisualizationType,
        QueryHistory, SharedQuery
    )
    print("Successfully imported query models!")
    print(f"Available query statuses: {[status.value for status in QueryStatus]}")
    print(f"Available visualization types: {[viz_type.value for viz_type in VisualizationType]}")
except Exception as e:
    print(f"Error importing query models: {e}")