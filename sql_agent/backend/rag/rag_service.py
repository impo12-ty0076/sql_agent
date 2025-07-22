import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from ..models.database import DatabaseSchema
from ..models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult, RagResponse
from ..llm.base import LLMService
from .document_indexer import DocumentIndexer
from .document_store import DocumentStore
from .text_utils import extract_keywords, normalize_text

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
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Extract keywords from the query
        keywords = extract_keywords(query.query)
        
        # Log the keywords for debugging
        logger.debug(f"Extracted keywords: {keywords}")
        
        # Perform the search
        results = self.document_store.search(query)
        
        return results
    
    def generate_response(
        self, db_id: str, query: str, top_k: int = 5
    ) -> RagResponse:
        """
        Generate a response to a query using RAG.
        
        Args:
            db_id: Database ID
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            RAG response
        """
        # Create a search query
        search_query = SearchQuery(
            query=query,
            db_id=db_id,
            top_k=top_k
        )
        
        # Search for relevant documents
        search_results = self.search(search_query)
        
        if not search_results:
            # No relevant documents found
            return RagResponse(
                query=query,
                response="I couldn't find any relevant information in the database schema. "
                         "Please try a different query or provide more details.",
                sources=[]
            )
        
        # Build context from search results
        context = self._build_context(query, search_results)
        
        # Generate response using LLM
        response = self.llm_service.generate_rag_response(query, context)
        
        # Create RAG response
        rag_response = RagResponse(
            query=query,
            response=response,
            sources=search_results
        )
        
        return rag_response
    
    def _build_context(self, query: str, search_results: List[SearchResult]) -> str:
        """
        Build context from search results.
        
        Args:
            query: User query
            search_results: Search results
            
        Returns:
            Context string
        """
        context = f"Query: {query}\n\n"
        context += "Relevant information from the database schema:\n\n"
        
        for i, result in enumerate(search_results):
            doc = result.document
            context += f"--- Document {i+1} (Score: {result.score:.2f}) ---\n"
            context += f"Type: {doc.doc_type}\n"
            context += f"Content:\n{doc.content}\n\n"
        
        return context