#!/usr/bin/env python3
"""
Manual test runner for the search engine functionality.
"""

import sys
import os
import numpy as np
from datetime import datetime

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the models directly
from models.rag import Document, DocumentType, SearchQuery, SearchResult

# Import search engine with fixed imports
import importlib.util
import types

# Load the search engine module manually to avoid import issues
search_engine_path = os.path.join(current_dir, 'rag', 'search_engine.py')
spec = importlib.util.spec_from_file_location("search_engine", search_engine_path)
search_engine_module = importlib.util.module_from_spec(spec)

# Manually set up the imports for the search engine module
search_engine_module.Document = Document
search_engine_module.DocumentType = DocumentType
search_engine_module.SearchQuery = SearchQuery
search_engine_module.SearchResult = SearchResult

# Import text utils
text_utils_path = os.path.join(current_dir, 'rag', 'text_utils.py')
text_utils_spec = importlib.util.spec_from_file_location("text_utils", text_utils_path)
text_utils_module = importlib.util.module_from_spec(text_utils_spec)
text_utils_spec.loader.exec_module(text_utils_module)

search_engine_module.normalize_text = text_utils_module.normalize_text
search_engine_module.tokenize = text_utils_module.tokenize
search_engine_module.extract_keywords = text_utils_module.extract_keywords
search_engine_module.calculate_text_similarity = text_utils_module.calculate_text_similarity

# Execute the search engine module
spec.loader.exec_module(search_engine_module)

# Get the SearchEngine class
SearchEngine = search_engine_module.SearchEngine

def create_test_documents():
    """Create test documents for testing."""
    documents = []
    
    # Create test documents with different types and content
    
    # Table documents
    documents.append(Document(
        id="doc_1",
        db_id="test_db",
        doc_type=DocumentType.TABLE,
        title="Users Table",
        content="The users table contains user information including id, name, email, and created_at fields. This is the main user entity table.",
        metadata={
            "table_name": "users",
            "schema": "public",
            "keywords": ["user", "account", "profile"]
        },
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100-dim vector
    ))
    
    documents.append(Document(
        id="doc_2",
        db_id="test_db",
        doc_type=DocumentType.TABLE,
        title="Orders Table",
        content="The orders table stores order information with fields like order_id, user_id, product_id, quantity, and order_date. Links to users and products.",
        metadata={
            "table_name": "orders",
            "schema": "public",
            "keywords": ["order", "purchase", "transaction"]
        },
        embedding=[0.2, 0.3, 0.4, 0.5, 0.6] * 20  # 100-dim vector
    ))
    
    # Column documents
    documents.append(Document(
        id="doc_3",
        db_id="test_db",
        doc_type=DocumentType.COLUMN,
        title="User Email Column",
        content="Email field in users table. Stores user email addresses. Must be unique and not null.",
        metadata={
            "table_name": "users",
            "column_name": "email",
            "data_type": "varchar",
            "keywords": ["email", "contact", "unique"]
        },
        embedding=[0.3, 0.4, 0.5, 0.6, 0.7] * 20  # 100-dim vector
    ))
    
    documents.append(Document(
        id="doc_4",
        db_id="test_db",
        doc_type=DocumentType.COLUMN,
        title="Order Quantity Column",
        content="Quantity field in orders table. Stores the number of items ordered. Integer type, must be positive.",
        metadata={
            "table_name": "orders",
            "column_name": "quantity",
            "data_type": "integer",
            "keywords": ["quantity", "amount", "count"]
        },
        embedding=[0.4, 0.5, 0.6, 0.7, 0.8] * 20  # 100-dim vector
    ))
    
    # Schema document
    documents.append(Document(
        id="doc_5",
        db_id="test_db",
        doc_type=DocumentType.SCHEMA,
        title="Public Schema",
        content="Public schema contains all main application tables including users, orders, products, and their relationships.",
        metadata={
            "schema_name": "public",
            "keywords": ["schema", "database", "structure"]
        },
        embedding=[0.5, 0.6, 0.7, 0.8, 0.9] * 20  # 100-dim vector
    ))
    
    return documents

def test_search_engine():
    """Test the search engine functionality."""
    print("=== Testing Search Engine ===")
    
    # Create search engine and add test documents
    search_engine = SearchEngine()
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
        print(f"  {i+1}. {result.document.title} (score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
        print(f"     Content: {result.document.content[:100]}...")
    
    # Test 2: Embedding search
    print("\n--- Test 2: Embedding Search ---")
    query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55] * 20  # 100-dim vector
    
    results = search_engine.embedding_search(query, query_embedding)
    print(f"Query: '{query.query}' (with embedding)")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.document.title} (similarity: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
    
    # Test 3: Hybrid search
    print("\n--- Test 3: Hybrid Search ---")
    results = search_engine.hybrid_search(query, query_embedding)
    print(f"Query: '{query.query}' (hybrid)")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.document.title} (combined score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
    
    # Test 4: Fuzzy search
    print("\n--- Test 4: Fuzzy Search ---")
    fuzzy_query = SearchQuery(
        query="usr emial",  # Typos in "user email"
        db_id="test_db",
        top_k=3
    )
    
    results = search_engine.fuzzy_search(fuzzy_query)
    print(f"Query: '{fuzzy_query.query}' (with typos)")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.document.title} (fuzzy score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
    
    # Test 5: Document type filtering
    print("\n--- Test 5: Document Type Filtering ---")
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
        print(f"  {i+1}. {result.document.title} (score: {result.score:.3f})")
        print(f"     Type: {result.document.doc_type}")
    
    # Test 6: Statistics
    print("\n--- Test 6: Search Engine Statistics ---")
    stats = search_engine.get_stats()
    print(f"Total documents: {stats['total_documents']}")
    for db_id, db_stats in stats['databases'].items():
        print(f"Database '{db_id}':")
        print(f"  Documents: {db_stats['documents']}")
        print(f"  Keywords: {db_stats['keywords']}")
        print(f"  Document types: {db_stats['document_types']}")
    
    print("\n=== All tests completed successfully! ===")

if __name__ == "__main__":
    test_search_engine()