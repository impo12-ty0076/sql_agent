import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

try:
    from ..models.database import DatabaseSchema
    from ..models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult, RagResponse
    from ..llm.base import LLMService
    from .document_indexer import DocumentIndexer
    from .document_store import DocumentStore
    from .text_utils import extract_keywords, normalize_text
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.database import DatabaseSchema
    from models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult, RagResponse
    from llm.base import LLMService
    from rag.document_indexer import DocumentIndexer
    from rag.document_store import DocumentStore
    from rag.text_utils import extract_keywords, normalize_text

logger = logging.getLogger(__name__)

class RagService:
    """
    Service for Retrieval-Augmented Generation (RAG).
    """
    
    def __init__(self, llm_service: LLMService, document_store: DocumentStore = None):
        """
        Initialize the RAG service.
        
        Args:
            llm_service: LLM service for generating embeddings and responses
            document_store: Optional document store, will create a new one if not provided
        """
        self.llm_service = llm_service
        self.document_indexer = DocumentIndexer(llm_service)
        self.document_store = document_store or DocumentStore()
    
    def index_database_schema(self, db_schema: DatabaseSchema) -> List[str]:
        """
        Index a database schema.
        
        Args:
            db_schema: Database schema to index
            
        Returns:
            List of document IDs
        """
        # Clear existing documents for this database
        self.document_store.clear_db(db_schema.db_id)
        
        # Index the database schema
        documents = self.document_indexer.index_database_schema(db_schema)
        
        # Process documents and chunks
        chunks_map = {}
        processed_docs = []
        
        for doc in documents:
            # Check if document needs chunking
            if len(doc.content) > 1000:  # Simple heuristic, in practice use token count
                parent_doc, chunks = self.document_indexer.chunk_document(doc)
                processed_docs.append(parent_doc)
                if chunks:
                    chunks_map[parent_doc.id] = chunks
            else:
                processed_docs.append(doc)
        
        # Add documents to the store
        doc_ids = self.document_store.add_documents(processed_docs, chunks_map)
        
        return doc_ids
    
    def index_query_history(
        self, db_id: str, query_text: str, sql: str, result_summary: Optional[str] = None
    ) -> str:
        """
        Index a query history entry.
        
        Args:
            db_id: Database ID
            query_text: Natural language query
            sql: Generated SQL
            result_summary: Optional summary of the query results
            
        Returns:
            Document ID
        """
        # Index the query history
        document = self.document_indexer.index_query_history(db_id, query_text, sql, result_summary)
        
        # Add to the document store
        doc_id = self.document_store.add_document(document)
        
        return doc_id
    
    def search(self, query: SearchQuery, search_type: str = "hybrid") -> List[SearchResult]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            search_type: Type of search ("keyword", "embedding", "hybrid", "fuzzy")
            
        Returns:
            List of search results
        """
        # Extract keywords from the query for debugging
        keywords = extract_keywords(query.query)
        logger.debug(f"Extracted keywords: {keywords}")
        
        # Get query embedding if needed for embedding or hybrid search
        query_embedding = None
        if search_type in ["embedding", "hybrid"]:
            try:
                # Generate embedding for the query
                query_embedding = self.llm_service.get_embeddings_sync([query.query])[0]
            except Exception as e:
                logger.warning(f"Failed to generate query embedding: {e}")
                # Fall back to keyword search if embedding generation fails
                if search_type == "embedding":
                    search_type = "keyword"
        
        # Perform the search
        results = self.document_store.search(query, query_embedding, search_type)
        
        return results
    
    def generate_response(
        self, db_id: str, query: str, top_k: int = 5, search_type: str = "hybrid",
        include_citations: bool = True, context_window_size: int = 2000
    ) -> RagResponse:
        """
        Generate a response to a query using RAG with enhanced context construction
        and source citation functionality.
        
        Args:
            db_id: Database ID
            query: User query
            top_k: Number of documents to retrieve
            search_type: Type of search to use
            include_citations: Whether to include source citations in response
            context_window_size: Maximum size of context window in characters
            
        Returns:
            RAG response with enhanced context and citations
        """
        logger.info(f"Generating RAG response for query: '{query}' in database: {db_id}")
        
        # Create a search query
        search_query = SearchQuery(
            query=query,
            db_id=db_id,
            top_k=top_k
        )
        
        # Search for relevant documents with fallback strategy
        search_results = self._search_with_fallback(search_query, search_type)
        
        if not search_results:
            logger.warning(f"No relevant documents found for query: '{query}'")
            return RagResponse(
                query=query,
                response="죄송합니다. 데이터베이스 스키마에서 관련 정보를 찾을 수 없습니다. "
                         "다른 질문을 시도하거나 더 구체적인 정보를 제공해 주세요.",
                sources=[]
            )
        
        logger.info(f"Found {len(search_results)} relevant documents")
        
        # Build enhanced context from search results
        context = self._build_enhanced_context(
            query, search_results, context_window_size, include_citations
        )
        
        # Generate response using LLM with enhanced prompting
        try:
            response_text = self._generate_llm_response(query, context, include_citations)
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            response_text = "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
        
        # Post-process response to add citations if needed
        if include_citations:
            response_text = self._add_source_citations(response_text, search_results)
        
        # Create enhanced RAG response
        rag_response = RagResponse(
            query=query,
            response=response_text,
            sources=search_results
        )
        
        logger.info("RAG response generated successfully")
        return rag_response
    
    def _search_with_fallback(self, search_query: SearchQuery, search_type: str) -> List[SearchResult]:
        """
        Search for documents with fallback strategy.
        
        Args:
            search_query: Search query
            search_type: Primary search type
            
        Returns:
            List of search results
        """
        # Primary search
        search_results = self.search(search_query, search_type)
        
        if not search_results:
            # Try different search types if the primary one fails
            fallback_types = ["keyword", "fuzzy", "hybrid"]
            for fallback_type in fallback_types:
                if fallback_type != search_type:
                    logger.info(f"Trying fallback search type: {fallback_type}")
                    search_results = self.search(search_query, fallback_type)
                    if search_results:
                        break
        
        return search_results
    
    def _build_enhanced_context(
        self, query: str, search_results: List[SearchResult], 
        context_window_size: int, include_citations: bool
    ) -> str:
        """
        Build enhanced context from search results with better formatting and relevance ranking.
        
        Args:
            query: User query
            search_results: Search results
            context_window_size: Maximum context size in characters
            include_citations: Whether to include citation markers
            
        Returns:
            Enhanced context string
        """
        context_parts = []
        context_parts.append(f"사용자 질문: {query}\n")
        context_parts.append("데이터베이스 스키마에서 관련된 정보:\n")
        
        # Sort results by score (highest first)
        sorted_results = sorted(search_results, key=lambda x: x.score, reverse=True)
        
        current_size = len("".join(context_parts))
        
        for i, result in enumerate(sorted_results):
            doc = result.document
            
            # Create document section
            doc_section = self._format_document_for_context(doc, result.score, i + 1, include_citations)
            
            # Check if adding this document would exceed context window
            if current_size + len(doc_section) > context_window_size:
                logger.info(f"Context window limit reached. Including {i} out of {len(sorted_results)} documents.")
                break
            
            context_parts.append(doc_section)
            current_size += len(doc_section)
        
        return "\n".join(context_parts)
    
    def _format_document_for_context(
        self, doc: Document, score: float, index: int, include_citations: bool
    ) -> str:
        """
        Format a document for inclusion in context.
        
        Args:
            doc: Document to format
            score: Relevance score
            index: Document index
            include_citations: Whether to include citation markers
            
        Returns:
            Formatted document string
        """
        doc_type_names = {
            "schema": "스키마",
            "table": "테이블",
            "column": "컬럼",
            "foreign_key": "외래키",
            "query_history": "쿼리 이력",
            "custom": "사용자 정의"
        }
        
        doc_type_display = doc_type_names.get(doc.doc_type, doc.doc_type)
        citation_marker = f"[{index}]" if include_citations else ""
        
        section = f"\n--- {doc_type_display} 정보 {citation_marker} (관련도: {score:.2f}) ---\n"
        
        # Add metadata if available
        if doc.metadata:
            metadata_info = []
            for key, value in doc.metadata.items():
                if key in ["table_name", "schema_name", "column_name"]:
                    metadata_info.append(f"{key}: {value}")
            
            if metadata_info:
                section += f"메타데이터: {', '.join(metadata_info)}\n"
        
        # Add content with proper formatting
        content = doc.content.strip()
        if len(content) > 500:  # Truncate very long content
            content = content[:500] + "..."
        
        section += f"내용:\n{content}\n"
        
        return section
    
    def _generate_llm_response(self, query: str, context: str, include_citations: bool) -> str:
        """
        Generate LLM response with enhanced prompting.
        
        Args:
            query: User query
            context: Context from search results
            include_citations: Whether to include citations
            
        Returns:
            Generated response
        """
        # Enhanced prompt for better RAG responses
        enhanced_prompt = f"""
다음은 데이터베이스 스키마에 관한 정보입니다. 이 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요.

{context}

### 답변 지침:
1. 제공된 컨텍스트 정보만을 사용하여 답변하세요.
2. 컨텍스트에 없는 정보에 대해서는 "제공된 정보에서는 확인할 수 없습니다"라고 명시하세요.
3. 답변은 명확하고 구체적으로 작성하세요.
4. 테이블명, 컬럼명, 데이터 타입 등 구체적인 정보를 포함하세요.
5. 관련된 테이블 간의 관계가 있다면 설명해주세요.
6. 사용자가 이해하기 쉽도록 한국어로 답변하세요.
{"7. 답변에 사용된 정보의 출처를 [숫자] 형태로 표시하세요." if include_citations else ""}

답변:"""
        
        # Use the LLM service to generate response (sync wrapper for async method)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.llm_service.generate_rag_response(query, enhanced_prompt))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.llm_service.generate_rag_response(query, enhanced_prompt))
    
    def _add_source_citations(self, response: str, search_results: List[SearchResult]) -> str:
        """
        Add source citations to the response.
        
        Args:
            response: Generated response
            search_results: Search results used for context
            
        Returns:
            Response with citations added
        """
        if not search_results:
            return response
        
        # Add citations section
        citations = ["\n\n--- 참고 자료 ---"]
        
        for i, result in enumerate(search_results):
            doc = result.document
            doc_type_names = {
                "schema": "스키마",
                "table": "테이블", 
                "column": "컬럼",
                "foreign_key": "외래키",
                "query_history": "쿼리 이력",
                "custom": "사용자 정의"
            }
            
            doc_type_display = doc_type_names.get(doc.doc_type, doc.doc_type)
            
            citation = f"[{i+1}] {doc_type_display}"
            
            # Add metadata info if available
            if doc.metadata:
                if "table_name" in doc.metadata:
                    citation += f" - {doc.metadata['table_name']}"
                if "schema_name" in doc.metadata:
                    citation += f" ({doc.metadata['schema_name']})"
            
            citation += f" (관련도: {result.score:.2f})"
            citations.append(citation)
        
        return response + "\n".join(citations)
    
    def _build_context(self, query: str, search_results: List[SearchResult]) -> str:
        """
        Build context from search results (legacy method for backward compatibility).
        
        Args:
            query: User query
            search_results: Search results
            
        Returns:
            Context string
        """
        return self._build_enhanced_context(query, search_results, 2000, False)
    
    async def generate_response_async(
        self, db_id: str, query: str, top_k: int = 5, search_type: str = "hybrid",
        include_citations: bool = True, context_window_size: int = 2000
    ) -> RagResponse:
        """
        Async version of generate_response for better performance with LLM calls.
        
        Args:
            db_id: Database ID
            query: User query
            top_k: Number of documents to retrieve
            search_type: Type of search to use
            include_citations: Whether to include source citations in response
            context_window_size: Maximum size of context window in characters
            
        Returns:
            RAG response with enhanced context and citations
        """
        logger.info(f"Generating async RAG response for query: '{query}' in database: {db_id}")
        
        # Create a search query
        search_query = SearchQuery(
            query=query,
            db_id=db_id,
            top_k=top_k
        )
        
        # Search for relevant documents with fallback strategy
        search_results = self._search_with_fallback(search_query, search_type)
        
        if not search_results:
            logger.warning(f"No relevant documents found for query: '{query}'")
            return RagResponse(
                query=query,
                response="죄송합니다. 데이터베이스 스키마에서 관련 정보를 찾을 수 없습니다. "
                         "다른 질문을 시도하거나 더 구체적인 정보를 제공해 주세요.",
                sources=[]
            )
        
        logger.info(f"Found {len(search_results)} relevant documents")
        
        # Build enhanced context from search results
        context = self._build_enhanced_context(
            query, search_results, context_window_size, include_citations
        )
        
        # Generate response using LLM with enhanced prompting (async)
        try:
            response_text = await self._generate_llm_response_async(query, context, include_citations)
        except Exception as e:
            logger.error(f"Failed to generate async LLM response: {e}")
            response_text = "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
        
        # Post-process response to add citations if needed
        if include_citations:
            response_text = self._add_source_citations(response_text, search_results)
        
        # Create enhanced RAG response
        rag_response = RagResponse(
            query=query,
            response=response_text,
            sources=search_results
        )
        
        logger.info("Async RAG response generated successfully")
        return rag_response
    
    async def _generate_llm_response_async(self, query: str, context: str, include_citations: bool) -> str:
        """
        Generate LLM response asynchronously with enhanced prompting.
        
        Args:
            query: User query
            context: Context from search results
            include_citations: Whether to include citations
            
        Returns:
            Generated response
        """
        # Enhanced prompt for better RAG responses
        enhanced_prompt = f"""
다음은 데이터베이스 스키마에 관한 정보입니다. 이 정보를 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공해주세요.

{context}

### 답변 지침:
1. 제공된 컨텍스트 정보만을 사용하여 답변하세요.
2. 컨텍스트에 없는 정보에 대해서는 "제공된 정보에서는 확인할 수 없습니다"라고 명시하세요.
3. 답변은 명확하고 구체적으로 작성하세요.
4. 테이블명, 컬럼명, 데이터 타입 등 구체적인 정보를 포함하세요.
5. 관련된 테이블 간의 관계가 있다면 설명해주세요.
6. 사용자가 이해하기 쉽도록 한국어로 답변하세요.
{"7. 답변에 사용된 정보의 출처를 [숫자] 형태로 표시하세요." if include_citations else ""}

답변:"""
        
        # Use the async LLM service to generate response
        return await self.llm_service.generate_rag_response(query, enhanced_prompt)