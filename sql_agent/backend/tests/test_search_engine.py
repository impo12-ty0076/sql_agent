import unittest
import sys
import os
import numpy as np
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.rag import Document, DocumentType, SearchQuery, SearchResult
from rag.search_engine import SearchEngine

class TestSearchEngine(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.search_engine = SearchEngine()
        self.test_documents = self._create_test_documents()
        
        # Add test documents to the search engine
        self.search_engine.add_documents(self.test_documents)
    
    def _create_test_documents(self):
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
        
        # Foreign key document
        documents.append(Document(
            id="doc_6",
            db_id="test_db",
            doc_type=DocumentType.FOREIGN_KEY,
            title="Orders-Users Relationship",
            content="Foreign key relationship between orders.user_id and users.id. Each order belongs to one user.",
            metadata={
                "source_table": "orders",
                "source_column": "user_id",
                "target_table": "users",
                "target_column": "id",
                "keywords": ["foreign_key", "relationship", "join"]
            },
            embedding=[0.6, 0.7, 0.8, 0.9, 1.0] * 20  # 100-dim vector
        ))
        
        # Document for different database
        documents.append(Document(
            id="doc_7",
            db_id="other_db",
            doc_type=DocumentType.TABLE,
            title="Products Table",
            content="Products table in different database with product information.",
            metadata={
                "table_name": "products",
                "keywords": ["product", "item", "catalog"]
            },
            embedding=[0.7, 0.8, 0.9, 1.0, 0.1] * 20  # 100-dim vector
        ))
        
        return documents
    
    def test_add_document(self):
        """Test adding a single document."""
        new_engine = SearchEngine()
        doc = self.test_documents[0]
        
        new_engine.add_document(doc)
        
        # Check if document was added
        self.assertIn(doc.id, new_engine.documents)
        self.assertEqual(new_engine.documents[doc.id], doc)
        
        # Check if it was added to the database mapping
        self.assertIn(doc.db_id, new_engine.db_documents)
        self.assertIn(doc.id, new_engine.db_documents[doc.db_id])
        
        # Check if keywords were indexed
        self.assertIn(doc.id, new_engine.document_keywords)
    
    def test_add_documents(self):
        """Test adding multiple documents."""
        new_engine = SearchEngine()
        docs = self.test_documents[:3]
        
        new_engine.add_documents(docs)
        
        # Check if all documents were added
        for doc in docs:
            self.assertIn(doc.id, new_engine.documents)
            self.assertEqual(new_engine.documents[doc.id], doc)
    
    def test_keyword_search(self):
        """Test keyword-based search."""
        query = SearchQuery(
            query="user email information",
            db_id="test_db",
            top_k=5
        )
        
        results = self.search_engine.keyword_search(query)
        
        # Should return results
        self.assertGreater(len(results), 0)
        
        # Results should be SearchResult objects
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertIsInstance(result.document, Document)
            self.assertIsInstance(result.score, float)
        
        # Should be sorted by score (descending)
        scores = [result.score for result in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_keyword_search_with_filter(self):
        """Test keyword search with document type filter."""
        query = SearchQuery(
            query="user",
            db_id="test_db",
            top_k=5,
            filter_doc_types=[DocumentType.TABLE]
        )
        
        results = self.search_engine.keyword_search(query)
        
        # All results should be table documents
        for result in results:
            self.assertEqual(result.document.doc_type, DocumentType.TABLE)
    
    def test_embedding_search(self):
        """Test embedding-based search."""
        query = SearchQuery(
            query="user information",
            db_id="test_db",
            top_k=3
        )
        
        # Create a query embedding similar to user-related documents
        query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55] * 20  # 100-dim vector
        
        results = self.search_engine.embedding_search(query, query_embedding)
        
        # Should return results
        self.assertGreater(len(results), 0)
        
        # Results should be SearchResult objects with similarity scores
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertGreaterEqual(result.score, 0.0)
            self.assertLessEqual(result.score, 1.0)
    
    def test_embedding_search_no_embedding(self):
        """Test embedding search without query embedding."""
        query = SearchQuery(
            query="user information",
            db_id="test_db",
            top_k=3
        )
        
        results = self.search_engine.embedding_search(query, None)
        
        # Should return empty results
        self.assertEqual(len(results), 0)
    
    def test_hybrid_search(self):
        """Test hybrid search combining keyword and embedding."""
        query = SearchQuery(
            query="user email",
            db_id="test_db",
            top_k=5
        )
        
        query_embedding = [0.2, 0.3, 0.4, 0.5, 0.6] * 20  # 100-dim vector
        
        results = self.search_engine.hybrid_search(query, query_embedding)
        
        # Should return results
        self.assertGreater(len(results), 0)
        
        # Results should be sorted by combined score
        scores = [result.score for result in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_fuzzy_search(self):
        """Test fuzzy search for handling typos."""
        query = SearchQuery(
            query="usr emial",  # Typos in "user email"
            db_id="test_db",
            top_k=5
        )
        
        results = self.search_engine.fuzzy_search(query)
        
        # Should return results despite typos
        self.assertGreater(len(results), 0)
    
    def test_search_different_types(self):
        """Test the main search method with different search types."""
        query = SearchQuery(
            query="user information",
            db_id="test_db",
            top_k=3
        )
        
        query_embedding = [0.2, 0.3, 0.4, 0.5, 0.6] * 20
        
        # Test different search types
        keyword_results = self.search_engine.search(query, search_type="keyword")
        embedding_results = self.search_engine.search(query, query_embedding, search_type="embedding")
        hybrid_results = self.search_engine.search(query, query_embedding, search_type="hybrid")
        fuzzy_results = self.search_engine.search(query, search_type="fuzzy")
        
        # All should return results
        self.assertGreater(len(keyword_results), 0)
        self.assertGreater(len(embedding_results), 0)
        self.assertGreater(len(hybrid_results), 0)
        self.assertGreater(len(fuzzy_results), 0)
    
    def test_database_filtering(self):
        """Test that search only returns results from the specified database."""
        query = SearchQuery(
            query="table",
            db_id="test_db",
            top_k=10
        )
        
        results = self.search_engine.keyword_search(query)
        
        # All results should be from test_db
        for result in results:
            self.assertEqual(result.document.db_id, "test_db")
    
    def test_get_document(self):
        """Test getting a document by ID."""
        doc_id = self.test_documents[0].id
        retrieved_doc = self.search_engine.get_document(doc_id)
        
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc.id, doc_id)
        
        # Test non-existent document
        non_existent = self.search_engine.get_document("non_existent")
        self.assertIsNone(non_existent)
    
    def test_get_documents_by_db(self):
        """Test getting all documents for a database."""
        docs = self.search_engine.get_documents_by_db("test_db")
        
        # Should return documents from test_db only
        self.assertGreater(len(docs), 0)
        for doc in docs:
            self.assertEqual(doc.db_id, "test_db")
        
        # Test non-existent database
        empty_docs = self.search_engine.get_documents_by_db("non_existent_db")
        self.assertEqual(len(empty_docs), 0)
    
    def test_remove_document(self):
        """Test removing a document."""
        doc_id = self.test_documents[0].id
        
        # Verify document exists
        self.assertIn(doc_id, self.search_engine.documents)
        
        # Remove document
        success = self.search_engine.remove_document(doc_id)
        self.assertTrue(success)
        
        # Verify document was removed
        self.assertNotIn(doc_id, self.search_engine.documents)
        self.assertNotIn(doc_id, self.search_engine.document_keywords)
        
        # Test removing non-existent document
        success = self.search_engine.remove_document("non_existent")
        self.assertFalse(success)
    
    def test_clear_database(self):
        """Test clearing all documents for a database."""
        db_id = "test_db"
        
        # Verify documents exist
        docs_before = self.search_engine.get_documents_by_db(db_id)
        self.assertGreater(len(docs_before), 0)
        
        # Clear database
        success = self.search_engine.clear_database(db_id)
        self.assertTrue(success)
        
        # Verify documents were cleared
        docs_after = self.search_engine.get_documents_by_db(db_id)
        self.assertEqual(len(docs_after), 0)
        
        # Test clearing non-existent database
        success = self.search_engine.clear_database("non_existent_db")
        self.assertFalse(success)
    
    def test_get_stats(self):
        """Test getting search engine statistics."""
        stats = self.search_engine.get_stats()
        
        # Should have expected structure
        self.assertIn("total_documents", stats)
        self.assertIn("databases", stats)
        
        # Should have correct total documents
        self.assertEqual(stats["total_documents"], len(self.test_documents))
        
        # Should have database-specific stats
        self.assertIn("test_db", stats["databases"])
        self.assertIn("other_db", stats["databases"])
        
        # Database stats should have expected fields
        db_stats = stats["databases"]["test_db"]
        self.assertIn("documents", db_stats)
        self.assertIn("document_types", db_stats)
        self.assertIn("keywords", db_stats)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        # Orthogonal vectors should have similarity 0
        sim1 = self.search_engine._calculate_cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim1, 0.0, places=5)
        
        # Identical vectors should have similarity 1
        sim2 = self.search_engine._calculate_cosine_similarity(vec1, vec3)
        self.assertAlmostEqual(sim2, 1.0, places=5)
    
    def test_edit_distance(self):
        """Test edit distance calculation."""
        # Identical strings
        dist1 = self.search_engine._calculate_edit_distance("hello", "hello")
        self.assertEqual(dist1, 0)
        
        # One character difference
        dist2 = self.search_engine._calculate_edit_distance("hello", "hallo")
        self.assertEqual(dist2, 1)
        
        # Completely different strings
        dist3 = self.search_engine._calculate_edit_distance("abc", "xyz")
        self.assertEqual(dist3, 3)
    
    def test_document_type_bonus(self):
        """Test document type bonus calculation."""
        # Test table-related query
        table_tokens = ["table", "entity"]
        table_bonus = self.search_engine._get_document_type_bonus(DocumentType.TABLE, table_tokens)
        self.assertGreater(table_bonus, 0)
        
        # Test column-related query
        column_tokens = ["column", "field"]
        column_bonus = self.search_engine._get_document_type_bonus(DocumentType.COLUMN, column_tokens)
        self.assertGreater(column_bonus, 0)
        
        # Test unrelated query
        unrelated_tokens = ["random", "words"]
        unrelated_bonus = self.search_engine._get_document_type_bonus(DocumentType.TABLE, unrelated_tokens)
        self.assertEqual(unrelated_bonus, 0)

if __name__ == '__main__':
    unittest.main()
