import pytest
from datetime import datetime
from pydantic import ValidationError

from sql_agent.backend.models.query import (
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
    
    assert query.id == "query123"
    assert query.user_id == "user456"
    assert query.db_id == "db789"
    assert query.natural_language == "Show me all sales from last month"
    assert query.generated_sql == "SELECT * FROM sales WHERE date >= '2023-06-01' AND date <= '2023-06-30'"
    assert query.status == "completed"
    assert query.start_time == now
    assert query.end_time == now
    assert query.created_at == now
    
    # Test with invalid end_time (before start_time)
    earlier = datetime(2023, 1, 1)
    later = datetime(2023, 1, 2)
    
    with pytest.raises(ValidationError):
        Query(
            id="query123",
            user_id="user456",
            db_id="db789",
            natural_language="Show me all sales from last month",
            generated_sql="SELECT * FROM sales WHERE date >= '2023-06-01' AND date <= '2023-06-30'",
            status=QueryStatus.COMPLETED,
            start_time=later,
            end_time=earlier,  # Invalid: end_time before start_time
            created_at=now
        )

def test_result_column():
    # Valid result column
    column = ResultColumn(name="product_id", type="int")
    assert column.name == "product_id"
    assert column.type == "int"
    
    # Test with empty name
    with pytest.raises(ValidationError):
        ResultColumn(name="", type="int")
    
    # Test with empty type
    with pytest.raises(ValidationError):
        ResultColumn(name="product_id", type="")

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
    
    assert result.id == "result123"
    assert result.query_id == "query456"
    assert len(result.columns) == 2
    assert result.columns[0].name == "id"
    assert result.columns[1].type == "varchar"
    assert len(result.rows) == 2
    assert result.row_count == 2
    assert result.truncated is False
    assert result.created_at == now
    
    # Test with mismatched row_count
    with pytest.raises(ValidationError):
        QueryResult(
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
            row_count=3,  # Incorrect row count
            truncated=False,
            created_at=now
        )
    
    # Test with empty columns
    with pytest.raises(ValidationError):
        QueryResult(
            id="result123",
            query_id="query456",
            columns=[],  # Empty columns
            rows=[],
            row_count=0,
            truncated=False,
            created_at=now
        )

def test_visualization():
    # Valid visualization
    viz = Visualization(
        id="viz123",
        type=VisualizationType.BAR,
        title="Sales by Region",
        description="Bar chart showing sales distribution by region",
        image_data="base64encodedimagedata..."
    )
    
    assert viz.id == "viz123"
    assert viz.type == "bar"
    assert viz.title == "Sales by Region"
    assert viz.description == "Bar chart showing sales distribution by region"
    assert viz.image_data == "base64encodedimagedata..."
    
    # Test with empty image data
    with pytest.raises(ValidationError):
        Visualization(
            id="viz123",
            type=VisualizationType.BAR,
            title="Sales by Region",
            description="Bar chart showing sales distribution by region",
            image_data=""  # Empty image data
        )

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
    
    assert report.id == "report123"
    assert report.result_id == "result456"
    assert "import pandas" in report.python_code
    assert len(report.visualizations) == 1
    assert report.visualizations[0].type == "bar"
    assert len(report.insights) == 2
    assert report.created_at == now
    
    # Test with empty python code
    with pytest.raises(ValidationError):
        Report(
            id="report123",
            result_id="result456",
            python_code="",  # Empty python code
            visualizations=[],
            insights=[],
            created_at=now
        )

def test_query_history():
    # Valid query history
    now = datetime.now()
    history = QueryHistory(
        id="history123",
        user_id="user456",
        query_id="query789",
        favorite=True,
        tags=["sales", "monthly"],
        notes="Important query for monthly report",
        created_at=now,
        updated_at=now
    )
    
    assert history.id == "history123"
    assert history.user_id == "user456"
    assert history.query_id == "query789"
    assert history.favorite is True
    assert "sales" in history.tags
    assert history.notes == "Important query for monthly report"
    assert history.created_at == now
    assert history.updated_at == now

def test_shared_query():
    # Valid shared query
    now = datetime.now()
    later = datetime(now.year + 1, now.month, now.day)  # One year later
    
    shared = SharedQuery(
        id="shared123",
        query_id="query456",
        shared_by="user789",
        access_token="abc123token",
        expires_at=later,
        allowed_users=["user001", "user002"],
        created_at=now
    )
    
    assert shared.id == "shared123"
    assert shared.query_id == "query456"
    assert shared.shared_by == "user789"
    assert shared.access_token == "abc123token"
    assert shared.expires_at == later
    assert "user001" in shared.allowed_users
    assert shared.created_at == now
    
    # Test with invalid expiration (before creation)
    earlier = datetime(now.year - 1, now.month, now.day)  # One year earlier
    
    with pytest.raises(ValidationError):
        SharedQuery(
            id="shared123",
            query_id="query456",
            shared_by="user789",
            access_token="abc123token",
            expires_at=earlier,  # Invalid: expires before creation
            allowed_users=["user001", "user002"],
            created_at=now
        )