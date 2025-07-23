"""
Unit tests for RAG response generation functionality.

Tests the enhanced RAG response generation implementation including:
- Context construction from search results
- LLM-based response generation
- Source citation and reference functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.rag import Document, DocumentType, SearchQuery, SearchResult, RagResponse
from models.database import DatabaseSchema, Schema, Table, Column
from rag.rag_service import RagService
from llm.base import LLMService, LLMConfig, LLMProvider


class MockLLMService(LLMService):
    """Mock LLM service for testing."""
    
    def __init__(self):
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key"
        )
        super().__init__(config)
        self.generate_rag_response = AsyncMock(return_value="Mock LLM response")
        self.get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    
    async def generate_sql(self, *args, **kwargs):
        return {"sql": "SELECT * FROM test"}
    
    async def summarize_results(self, *args, **kwargs):
        return {"summary": "Test summary"}
    
    async def generate_python_code(self, *args, **kwargs):
        return {"code": "print('test')"}
    
    async def validate_and_fix_sql(self, *args, **kwargs):
        return "SELECT * FROM test", False
    
    async def get_model_info(self):
        return {"provider": "openai", "model": "gpt-3.5-turbo"}
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    return MockLLMService()


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            id="doc1",
            db_id="test_db",
            doc_type=DocumentType.TABLE,
            content="Users table with columns: id (int), name (varchar), email (varchar)",
            metadata={"table_name": "Users", "schema_name": "dbo"},
            embedding=[0.1, 0.2, 0.3]
        ),
        Document(
            id="doc2", 
            db_id="test_db",
            doc_type=DocumentType.COLUMN,
            content="Column: id, Type: int, Primary Key: true",
            metadata={"table_name": "Users", "column_name": "id"},
            embedding=[0.2, 0.3, 0.4]
        ),
        Document(
            id="doc3",
            db_id="test_db", 
            doc_type=DocumentType.FOREIGN_KEY,
            content="Foreign key from Orders.user_id to Users.id",
            metadata={"from_table": "Orders", "to_table": "Users"},
            embedding=[0.3, 0.4, 0.5]
        )
    ]


@pytest.fixture
def sample_search_results(sample_documents):
    """Create sample search results."""
    return [
        SearchResult(document=sample_documents[0], score=0.95),
        SearchResult(document=sample_documents[1], score=0.87),
        SearchResult(document=sample_documents[2], score=0.72)
    ]


@pytest.fixture
def rag_service(mock_llm_service):
    """Create RAG service with mock LLM service."""
    return RagService(llm_service=mock_llm_service)


class TestRagResponseGeneration:
    """Test cases for RAG response generation."""
    
    def test_search_with_fallback_success(self, rag_service, sample_search_results):
        """Test successful search with primary search type."""
        search_query = SearchQuery(query="test query", db_id="test_db", top_k=3)
        
        with patch.object(rag_service, 'search', return_value=sample_search_results):
            results = rag_service._search_with_fallback(search_query, "hybrid")
            
            assert len(results) == 3
            assert results[0].score == 0.95
    
    def test_search_with_fallback_fallback_success(self, rag_service, sample_search_results):
        """Test fallback search when primary search fails."""
        search_query = SearchQuery(query="test query", db_id="test_db", top_k=3)
        
        # Mock primary search to return empty, fallback to return results
        def mock_search(query, search_type):
            if search_type == "hybrid":
                return []
            elif search_type == "keyword":
                return sample_search_results
            return []
        
        with patch.object(rag_service, 'search', side_effect=mock_search):
            results = rag_service._search_with_fallback(search_query, "hybrid")
            
            assert len(results) == 3
            assert results[0].score == 0.95
    
    def test_search_with_fallback_no_results(self, rag_service):
        """Test fallback search when no results found."""
        search_query = SearchQuery(query="test query", db_id="test_db", top_k=3)
        
        with patch.object(rag_service, 'search', return_value=[]):
            results = rag_service._search_with_fallback(search_query, "hybrid")
            
            assert len(results) == 0
    
    def test_build_enhanced_context_basic(self, rag_service, sample_search_results):
        """Test basic enhanced context building."""
        query = "사용자 테이블에 대해 알려주세요"
        context = rag_service._build_enhanced_context(
            query, sample_search_results, 2000, False
        )
        
        assert "사용자 질문: 사용자 테이블에 대해 알려주세요" in context
        assert "데이터베이스 스키마에서 관련된 정보:" in context
        assert "테이블 정보" in context
        assert "컬럼 정보" in context
        assert "외래키 정보" in context
        assert "관련도: 0.95" in context
    
    def test_build_enhanced_context_with_citations(self, rag_service, sample_search_results):
        """Test enhanced context building with citations."""
        query = "사용자 테이블에 대해 알려주세요"
        context = rag_service._build_enhanced_context(
            query, sample_search_results, 2000, True
        )
        
        assert "[1]" in context
        assert "[2]" in context
        assert "[3]" in context
    
    def test_build_enhanced_context_window_limit(self, rag_service, sample_search_results):
        """Test context building with window size limit."""
        query = "사용자 테이블에 대해 알려주세요"
        # Very small context window to test truncation
        context = rag_service._build_enhanced_context(
            query, sample_search_results, 200, False
        )
        
        # Should still contain the query and basic structure
        assert "사용자 질문:" in context
        assert len(context) <= 300  # Allow some buffer for formatting
    
    def test_format_document_for_context_table(self, rag_service, sample_documents):
        """Test document formatting for table document."""
        doc = sample_documents[0]  # Table document
        formatted = rag_service._format_document_for_context(doc, 0.95, 1, True)
        
        assert "테이블 정보 [1]" in formatted
        assert "관련도: 0.95" in formatted
        assert "메타데이터: table_name: Users, schema_name: dbo" in formatted
        assert "Users table with columns" in formatted
    
    def test_format_document_for_context_column(self, rag_service, sample_documents):
        """Test document formatting for column document."""
        doc = sample_documents[1]  # Column document
        formatted = rag_service._format_document_for_context(doc, 0.87, 2, False)
        
        assert "컬럼 정보" in formatted
        assert "관련도: 0.87" in formatted
        assert "[2]" not in formatted  # No citations
        assert "Column: id, Type: int" in formatted
    
    def test_format_document_for_context_long_content(self, rag_service):
        """Test document formatting with long content truncation."""
        long_content = "A" * 600  # Content longer than 500 chars
        doc = Document(
            id="long_doc",
            db_id="test_db",
            doc_type=DocumentType.CUSTOM,
            content=long_content
        )
        
        formatted = rag_service._format_document_for_context(doc, 0.5, 1, False)
        
        assert "..." in formatted
        assert len(formatted) < len(long_content) + 200  # Should be truncated
    
    def test_add_source_citations(self, rag_service, sample_search_results):
        """Test adding source citations to response."""
        response = "사용자 테이블에는 id, name, email 컬럼이 있습니다."
        
        response_with_citations = rag_service._add_source_citations(response, sample_search_results)
        
        assert "--- 참고 자료 ---" in response_with_citations
        assert "[1] 테이블 - Users (dbo)" in response_with_citations
        assert "[2] 컬럼 - Users" in response_with_citations
        assert "[3] 외래키" in response_with_citations
        assert "관련도: 0.95" in response_with_citations
    
    def test_add_source_citations_empty_results(self, rag_service):
        """Test adding citations with empty search results."""
        response = "테스트 응답입니다."
        
        response_with_citations = rag_service._add_source_citations(response, [])
        
        assert response_with_citations == response  # Should be unchanged
    
    def test_generate_response_success(self, rag_service, sample_search_results):
        """Test successful response generation."""
        with patch.object(rag_service, '_search_with_fallback', return_value=sample_search_results):
            with patch.object(rag_service, '_generate_llm_response', return_value="Generated response"):
                response = rag_service.generate_response(
                    db_id="test_db",
                    query="사용자 테이블에 대해 알려주세요",
                    top_k=3,
                    search_type="hybrid",
                    include_citations=True
                )
                
                assert isinstance(response, RagResponse)
                assert response.query == "사용자 테이블에 대해 알려주세요"
                assert "Generated response" in response.response
                assert "--- 참고 자료 ---" in response.response
                assert len(response.sources) == 3
    
    def test_generate_response_no_results(self, rag_service):
        """Test response generation when no search results found."""
        with patch.object(rag_service, '_search_with_fallback', return_value=[]):
            response = rag_service.generate_response(
                db_id="test_db",
                query="존재하지 않는 테이블",
                top_k=3
            )
            
            assert isinstance(response, RagResponse)
            assert "관련 정보를 찾을 수 없습니다" in response.response
            assert len(response.sources) == 0
    
    def test_generate_response_llm_error(self, rag_service, sample_search_results):
        """Test response generation when LLM fails."""
        with patch.object(rag_service, '_search_with_fallback', return_value=sample_search_results):
            with patch.object(rag_service, '_generate_llm_response', side_effect=Exception("LLM error")):
                response = rag_service.generate_response(
                    db_id="test_db",
                    query="테스트 쿼리",
                    top_k=3
                )
                
                assert isinstance(response, RagResponse)
                assert "오류가 발생했습니다" in response.response
                assert len(response.sources) == 3
    
    @pytest.mark.asyncio
    async def test_generate_response_async_success(self, rag_service, sample_search_results):
        """Test successful async response generation."""
        with patch.object(rag_service, '_search_with_fallback', return_value=sample_search_results):
            response = await rag_service.generate_response_async(
                db_id="test_db",
                query="사용자 테이블에 대해 알려주세요",
                top_k=3,
                search_type="hybrid",
                include_citations=True
            )
            
            assert isinstance(response, RagResponse)
            assert response.query == "사용자 테이블에 대해 알려주세요"
            assert "Mock LLM response" in response.response
            assert "--- 참고 자료 ---" in response.response
            assert len(response.sources) == 3
    
    @pytest.mark.asyncio
    async def test_generate_response_async_no_results(self, rag_service):
        """Test async response generation when no search results found."""
        with patch.object(rag_service, '_search_with_fallback', return_value=[]):
            response = await rag_service.generate_response_async(
                db_id="test_db",
                query="존재하지 않는 테이블",
                top_k=3
            )
            
            assert isinstance(response, RagResponse)
            assert "관련 정보를 찾을 수 없습니다" in response.response
            assert len(response.sources) == 0
    
    @pytest.mark.asyncio
    async def test_generate_llm_response_async(self, rag_service):
        """Test async LLM response generation."""
        query = "테스트 쿼리"
        context = "테스트 컨텍스트"
        
        response = await rag_service._generate_llm_response_async(query, context, True)
        
        assert response == "Mock LLM response"
        # Verify the LLM service was called with enhanced prompt
        rag_service.llm_service.generate_rag_response.assert_called_once()
        call_args = rag_service.llm_service.generate_rag_response.call_args
        assert query in call_args[0][1]  # Query should be in the prompt
        assert "답변 지침:" in call_args[0][1]  # Enhanced prompt should contain guidelines
    
    def test_generate_llm_response_sync(self, rag_service):
        """Test sync LLM response generation."""
        query = "테스트 쿼리"
        context = "테스트 컨텍스트"
        
        # Mock the async method to avoid actual async execution
        with patch.object(rag_service.llm_service, 'generate_rag_response', 
                         new_callable=AsyncMock, return_value="Sync mock response"):
            response = rag_service._generate_llm_response(query, context, True)
            
            assert response == "Sync mock response"
    
    def test_backward_compatibility_build_context(self, rag_service, sample_search_results):
        """Test backward compatibility of legacy _build_context method."""
        query = "테스트 쿼리"
        context = rag_service._build_context(query, sample_search_results)
        
        # Should call the enhanced version with default parameters
        assert "사용자 질문:" in context
        assert "데이터베이스 스키마에서 관련된 정보:" in context


class TestRagResponseIntegration:
    """Integration tests for RAG response generation."""
    
    def test_full_rag_pipeline(self, rag_service, sample_documents):
        """Test the full RAG pipeline from indexing to response generation."""
        # Create a mock database schema
        db_schema = DatabaseSchema(
            db_id="test_db",
            schemas=[
                Schema(
                    name="dbo",
                    tables=[
                        Table(
                            name="Users",
                            columns=[
                                Column(name="id", type="int", nullable=False),
                                Column(name="name", type="varchar", nullable=False),
                                Column(name="email", type="varchar", nullable=True)
                            ],
                            primary_key=["id"],
                            foreign_keys=[]
                        )
                    ]
                )
            ],
            last_updated=None
        )
        
        # Index the schema
        with patch.object(rag_service.document_store, 'add_documents', return_value=["doc1", "doc2", "doc3"]):
            with patch.object(rag_service.document_indexer, 'index_database_schema', return_value=sample_documents):
                doc_ids = rag_service.index_database_schema(db_schema)
                assert len(doc_ids) == 3
        
        # Generate response
        with patch.object(rag_service, 'search', return_value=[
            SearchResult(document=sample_documents[0], score=0.95)
        ]):
            with patch.object(rag_service, '_generate_llm_response', return_value="Integration test response"):
                response = rag_service.generate_response(
                    db_id="test_db",
                    query="사용자 테이블의 구조를 알려주세요"
                )
                
                assert isinstance(response, RagResponse)
                assert "Integration test response" in response.response
                assert len(response.sources) == 1


if __name__ == "__main__":
    pytest.main([__file__])