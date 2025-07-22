from fastapi.testclient import TestClient
import pytest

from ..main import app

client = TestClient(app)

def test_root_endpoint():
    """
    루트 엔드포인트 테스트
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "SQL DB LLM Agent API"

def test_health_endpoint():
    """
    헬스 체크 엔드포인트 테스트
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_docs_endpoint():
    """
    API 문서 엔드포인트 테스트
    """
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_openapi_endpoint():
    """
    OpenAPI 스키마 엔드포인트 테스트
    """
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    
    # OpenAPI 스키마 기본 필드 확인
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema