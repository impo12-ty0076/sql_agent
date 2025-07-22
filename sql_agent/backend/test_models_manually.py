from datetime import datetime
from models.query import (
    Query, QueryStatus, QueryResult, ResultColumn, 
    Report, Visualization, VisualizationType,
    QueryHistory, SharedQuery
)

def test_query_model():
    # Valid query
    now = datetime.now()
    query = Query(
        id="query123",
        user_id="user456",
        db_id="db789",
        natural_language="Show me all sales from last month",
        generated_sql="SELECT * FROM sales WHERE date >= '2023-06-01' AND date <= '2023-06-30'",
        status=QueryStatus.COMPLETED,
        start_time=now,
        end_time=now,
        created_at=now
    )
    
    print("Query test passed!")
    return query

def test_query_result():
    # Valid query result
    now = datetime.now()
    result = QueryResult(
        id="result123",
        query_id="query456",
        columns=[
            ResultColumn(name="id", type="int"),
            ResultColumn(name="name", type="varchar")
        ],
        rows=[
            [1, "Product A"],
            [2, "Product B"]
        ],
        row_count=2,
        truncated=False,
        created_at=now
    )
    
    print("QueryResult test passed!")
    return result

def test_report():
    # Valid report
    now = datetime.now()
    report = Report(
        id="report123",
        result_id="result456",
        python_code="import pandas as pd\nimport matplotlib.pyplot as plt\n# Analysis code here",
        visualizations=[
            Visualization(
                id="viz123",
                type=VisualizationType.BAR,
                title="Sales by Region",
                image_data="base64encodedimagedata..."
            )
        ],
        insights=["Region A has the highest sales", "Sales are trending upward"],
        created_at=now
    )
    
    print("Report test passed!")
    return report

if __name__ == "__main__":
    print("Testing Query models...")
    query = test_query_model()
    result = test_query_result()
    report = test_report()
    print("All tests passed!")
    
    print("\nQuery details:")
    print(f"ID: {query.id}")
    print(f"Natural language: {query.natural_language}")
    print(f"Status: {query.status}")
    
    print("\nQueryResult details:")
    print(f"ID: {result.id}")
    print(f"Columns: {[col.name for col in result.columns]}")
    print(f"Row count: {result.row_count}")
    
    print("\nReport details:")
    print(f"ID: {report.id}")
    print(f"Visualizations: {len(report.visualizations)}")
    print(f"Visualization type: {report.visualizations[0].type}")
    print(f"Insights: {report.insights}")