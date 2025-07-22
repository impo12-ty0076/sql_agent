from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

class DocumentType(str, Enum):
    """
    Types of documents that can be indexed in the RAG system.
    """
    SCHEMA = "schema"
    TABLE = "table"
    COLUMN = "column"
    FOREIGN_KEY = "foreign_key"
    QUERY_HISTORY = "query_history"
    CUSTOM = "custom"

class Document(BaseModel):
    """
    A document that can be indexed in the RAG system.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    db_id: str
    doc_type: DocumentType
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Document content cannot be empty")
        return v
    
    @validator('db_id')
    def validate_db_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Database ID cannot be empty")
        return v

class DocumentChunk(BaseModel):
    """
    A chunk of a document that can be indexed in the RAG system.
    Used for large documents that need to be split into smaller pieces.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Document chunk content cannot be empty")
        return v
    
    @validator('document_id')
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Document ID cannot be empty")
        return v

class SearchQuery(BaseModel):
    """
    A search query for the RAG system.
    """
    query: str
    db_id: str
    top_k: int = 5
    filter_doc_types: Optional[List[DocumentType]] = None
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v
    
    @validator('db_id')
    def validate_db_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Database ID cannot be empty")
        return v
    
    @validator('top_k')
    def validate_top_k(cls, v):
        if v <= 0:
            raise ValueError("top_k must be a positive integer")
        return v

class SearchResult(BaseModel):
    """
    A search result from the RAG system.
    """
    document: Document
    score: float
    
    class Config:
        arbitrary_types_allowed = True

class RagResponse(BaseModel):
    """
    A response from the RAG system.
    """
    query: str
    response: str
    sources: List[SearchResult]
    
    @validator('query', 'response')
    def validate_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if not v:
            raise ValueError("Sources cannot be empty")
        return v