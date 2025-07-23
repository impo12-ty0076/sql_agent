#!/usr/bin/env python3
"""
Simple test for search engine functionality with inline imports.
"""

import sys
import os
import numpy as np
import logging
import re
import string
import math
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from collections import Counter
from datetime import datetime

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from models.rag import Document, DocumentType, SearchQuery, SearchResult

logger = logging.getLogger(__name__)

# Simple text processing functions (inline)
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "when", "who", "how", "where", "why", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "would", "should", "could", "ought", "i'm", "you're", "he's",
    "she's", "it's", "we're", "they're", "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll",
    "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't",
    "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't",
    "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't",
    "mustn't", "let's", "that's", "who's", "what's", "here's", "there's",
    "when's", "where's", "why's", "how's", "a", "an", "the", "and", "but",
    "if", "or", "because", "as", "until", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now"
}

SQL_KEYWORDS = {
    "select", "from", "where", "join", "inner", "outer", "left", "right", "full",
    "group", "by", "having", "order", "asc", "desc", "limit", "offset", "union",
    "insert", "update", "delete", "create", "alter", "drop", "table", "view",
    "index", "primary", "key", "foreign", "references", "constraint", "unique",
    "not", "null", "default", "check", "cascade", "restrict", "set", "on", "as",
    "distinct", "count", "sum", "avg", "min", "max", "between", "like", "in",
    "exists", "all", "any", "some", "and", "or", "not", "case", "when", "then",
    "else", "end", "with", "top", "percent", "pivot", "unpivot", "over", "partition"
}

def tokenize(text: str, remove_stopwords: bool = False, keep_sql_keywords: bool = True) -> List[str]:
    """Simple tokenization function."""
    if not text:
        return []
    
    # Convert to lowercase and split
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    words = text.split()
    
    # Remove stopwords if requested
    if remove_stopwords:
        if keep_sql_keywords:
            words = [word for word in words if word not in STOP_WORDS or word in SQL_KEYWORDS]
        else:
            words = [word for word in words if word not in STOP_WORDS]
    
    return words

def extract_keywords(text: str, max_keywords: int = 10, include_sql_keywords: bool = True) -> List[str]:
    """Simple keyword extraction."""
    if not text:
        return []
    
    tokens = tokenize(text, remove_stopwords=True, keep_sql_keywords=include_sql_keywords)
    word_counter = Counter()
    
    for token in tokens:
        if len(token) > 2:
            word_counter[token] += 1
    
    if include_sql_keywords:
        for word in word_counter:
            if word in SQL_KEYWORDS:
                word_counter[word] *= 1.5
    
    sorted_words = word_counter.most_common(max_keywords)
    return [word for word, _ in sorted_words]

# Simplified SearchEngine class
class SimpleSearchEngine:
    """Simplified search engine for testing."""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.db_documents: Dict[str, List[str]] = {}
        self.keyword_index: Dict[str, Dict[str, Set[str]]] = {}
        self.document_keywords: Dict[str, List[str]] = {}
    
    def add_document(self, document: Document) -> None:
        """Add a document to the search engine."""
        self.documents[document.id] = document
        
        if document.db_id not in self.db_documents:
            self.db_documents[document.db_id] = []
        self.db_documents[document.db_id].append(document.id)
        
        self._index_document_keywords(document)
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add multiple documents."""
        for document in documents:
            self.add_document(document)
    
    def _index_document_keywords(self, document: Document) -> None:
        """Index keywords for a document."""
        content_keywords = extract_keywords(document.content, max_keywords=20, include_sql_keywords=True)
        
        metadata_keywords = []
        if document.metadata:
            for key, value in document.metadata.items():
                if isinstance(value, str):
                    metadata_keywords.extend(extract_keywords(value, max_keywords=5))
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    metadata_keywords.extend(value)
        
        all_keywords = list(set(content_keywords + metadata_keywords))
        self.document_keywords[document.id] = all_keywords
        
        if document.db_id not in self.keyword_index:
            self.keyword_index[document.db_id] = {}
        
        for keyword in all_keywords:
            keyword = keyword.lower()
            if keyword not in self.keyword_index[document.db_id]:
                self.keyword_index[document.db_id][keyword] = set()
            self.keyword_index[document.db_id][keyword].add(document.id)
    
    def keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search."""
        db_id = query.db_id
        
        if db_id not in self.db_documents:
            return []
        
        query_keywords = extract_keywords(query.query, max_keywords=10, include_sql_keywords=True)
        query_tokens = tokenize(query.query.lower(), remove_stopwords=True, keep_sql_keywords=True)
        
        if not query_keywords and not query_tokens:
            return []
        
        document_scores: Dict[str, float] = {}
        
        for doc_id in self.db_documents[db_id]:
            document = self.documents.get(doc_id)
            if not document:
                continue
            
            if query.filter_doc_types and document.doc_type not in query.filter_doc_types:
                continue
            
            score = self._calculate_keyword_score(document, query_keywords, query_tokens, db_id)
            
            if score > 0:
                document_scores[doc_id] = score
        
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:query.top_k]
        
        results = []
        for doc_id, score in top_docs:
            document = self.documents[doc_id]
            results.append(SearchResult(document=document, score=score))
        
        return results
    
    def _calculate_keyword_score(self, document: Document, query_keywords: List[str], 
                                query_tokens: List[str], db_id: str) -> float:
        """Calculate keyword-based relevance score."""
        score = 0.0
        
        doc_keywords = self.document_keywords.get(document.id, [])
        doc_content_lower = document.content.lower()
        doc_tokens = tokenize(doc_content_lower, remove_stopwords=True, keep_sql_keywords=True)
        
        # Exact keyword matches
        for keyword in query_keywords:
            if keyword.lower() in [k.lower() for k in doc_keywords]:
                score += 3.0
        
        # Content-based matches
        for token in query_tokens:
            if token.lower() in doc_content_lower:
                score += 1.0
        
        # TF-IDF-like scoring
        total_docs = len(self.db_documents.get(db_id, []))
        if total_docs > 0:
            for token in query_tokens:
                tf = doc_tokens.count(token.lower())
                if tf > 0:
                    df = len(self.keyword_index.get(db_id, {}).get(token.lower(), set()))
                    if df > 0:
                        idf = math.log(total_docs / df)
                        score += tf * idf * 0.5
        
        # Document type bonus
        type_bonus = self._get_document_type_bonus(document.doc_type, query_tokens)
        score += type_bonus
        
        # Normalize by document length
        if len(doc_tokens) > 0:
            score = score / math.log(len(doc_tokens) + 1)
        
        return score
    
    def _get_document_type_bonus(self, doc_type: DocumentType, query_tokens: List[str]) -> float:
        """Get bonus score based on document type."""
        bonus = 0.0
        query_text = ' '.join(query_tokens).lower()
        
        table_keywords = ['table', 'tables', 'entity', 'entities']
        column_keywords = ['column', 'columns', 'field', 'fields', 'attribute', 'attributes']
        schema_keywords = ['schema', 'database', 'structure', 'overview']
        
        if doc_type == DocumentType.TABLE:
            if any(keyword in query_text for keyword in table_keywords):
                bonus += 1.0
        elif doc_type == DocumentType.COLUMN:
            if any(keyword in query_text for keyword in column_keywords):
                bonus += 1.0
        elif doc_type == DocumentType.SCHEMA:
            if any(keyword in query_text for keyword in schema_keywords):
                bonus += 1.0
        
        return bonus
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        stats = {
            "total_documents": len(self.documents),
            "databases": {}
        }
        
        for db_id in self.db_documents:
            doc_ids = self.db_documents[db_id]
            doc_types: Dict[str, int] = {}
            
            for doc_id in doc_ids:
                if doc_id in self.documents:
                    doc_type = self.documents[doc_id].doc_type
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            stats["databases"][db_id] = {
                "documents": len(doc_ids),
                "document_types": doc_types,
                "keywords": len(self.keyword_index.get(db_id, {}))
            }
        
        return stats

def create_test_documents():
    """Create test documents."""
    documents = []
    
    documents.append(Document(
        id="doc_1",
        db_id="test_db",
        doc_type=DocumentType.TABLE,
        content="Users Table: The users table contains user information including id, name, email, and created_at fields. This is the main user entity table.",
        metadata={
            "title": "Users Table",
            "table_name": "users",
            "schema": "public",
            "keywords": ["user", "account", "profile"]
        },
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 20
    ))
    
    documents.append(Document(
        id="doc_2",
        db_id="test_db",
        doc_type=DocumentType.TABLE,
        content="Orders Table: The orders table stores order information with fields like order_id, user_id, product_id, quantity, and order_date. Links to users and products.",
        metadata={
            "title": "Orders Table",
            "table_name": "orders",
            "schema": "public",
            "keywords": ["order", "purchase", "transaction"]
        },
        embedding=[0.2, 0.3, 0.4, 0.5, 0.6] * 20
    ))
    
    documents.append(Document(
        id="doc_3",
        db_id="test_db",
        doc_type=DocumentType.COLUMN,
        content="User Email Column: Email field in users table. Stores user email addresses. Must be unique and not null.",
        metadata={
            "title": "User Email Column",
            "table_name": "users",
            "column_name": "email",
            "data_type": "varchar",
            "keywords": ["email", "contact", "unique"]
        },
        embedding=[0.3, 0.4, 0.5, 0.6, 0.7] * 20
    ))
    
    return documents

def test_search_engine():
    """Test the search engine functionality."""
    print("=== Testing Simple Search Engine ===")
    
    # Create search engine and add test documents
    search_engine = SimpleSearchEngine()
    test_documents = create_test_documents()
    search_engine.add_documents(test_documents)
    
    print(f"Added {len(test_documents)} test documents")
    
    # Test 1: Keyword search
    print("\n--- Test 1: Keyword Search ---")
    query = SearchQuery(
        query="user email information",
        db_id="test_db",
        top_k=3
    )
    
    results = search_engine.keyword_search(query)
    print(f"Query: '{query.query}'")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        title = result.document.metadata.get("title", f"Document {result.document.id}")
        print(f"  {i+1}. {title} (score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
        print(f"     Content: {result.document.content[:100]}...")
    
    # Test 2: Document type filtering
    print("\n--- Test 2: Document Type Filtering ---")
    filtered_query = SearchQuery(
        query="table",
        db_id="test_db",
        top_k=5,
        filter_doc_types=[DocumentType.TABLE]
    )
    
    results = search_engine.keyword_search(filtered_query)
    print(f"Query: '{filtered_query.query}' (tables only)")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        title = result.document.metadata.get("title", f"Document {result.document.id}")
        print(f"  {i+1}. {title} (score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
    
    # Test 3: Statistics
    print("\n--- Test 3: Search Engine Statistics ---")
    stats = search_engine.get_stats()
    print(f"Total documents: {stats['total_documents']}")
    for db_id, db_stats in stats['databases'].items():
        print(f"Database '{db_id}':")
        print(f"  Documents: {db_stats['documents']}")
        print(f"  Keywords: {db_stats['keywords']}")
        print(f"  Document types: {db_stats['document_types']}")
    
    print("\n=== Search engine test completed successfully! ===")

if __name__ == "__main__":
    test_search_engine()