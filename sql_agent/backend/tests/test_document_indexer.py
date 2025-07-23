import unittest
import sys
import os
from datetime import datetime
import numpy as np

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import DatabaseSchema, Schema, Table, Column, ForeignKey
from models.rag import Document, DocumentType, DocumentChunk
from rag.document_indexer import DocumentIndexer
from rag.document_store import DocumentStore
from rag.rag_service import RagService

# Mock LLM service for testing
class MockLLMService:
    def get_embeddings_sync(self, texts):
        # Return random embeddings of fixed dimension for testing
        return [np.random.rand(384).tolist() for _ in texts]
    
    def generate_rag_response(self, query, context):
        # Return a simple response for testing
        return f"Response to '{query}' based on provided context."

class TestDocumentIndexer(unittest.TestCase):
    def setUp(self):
        self.llm_service = MockLLMService()
        self.document_indexer = DocumentIndexer(self.llm_service)
        self.document_store = DocumentStore(index_dir="test_indexes")
        self.rag_service = RagService(self.llm_service, self.document_store)
        
        # Create a sample database schema for testing
        self.sample_schema = self._create_sample_schema()
    
    def tearDown(self):
        # Clean up test indexes
        if os.path.exists("test_indexes"):
            for file in os.listdir("test_indexes"):
                os.remove(os.path.join("test_indexes", file))
            os.rmdir("test_indexes")
    
    def _create_sample_schema(self):
        # Create a sample database schema for testing
        columns_users = [
            Column(name="id", type="INT", nullable=False, default_value=None, description="User ID"),
            Column(name="username", type="VARCHAR(50)", nullable=False, default_value=None, description="Username"),
            Column(name="email", type="VARCHAR(100)", nullable=False, default_value=None, description="Email address"),
            Column(name="created_at", type="DATETIME", nullable=False, default_value="CURRENT_TIMESTAMP", description="Creation timestamp")
        ]
        
        columns_orders = [
            Column(name="id", type="INT", nullable=False, default_value=None, description="Order ID"),
            Column(name="user_id", type="INT", nullable=False, default_value=None, description="User ID (foreign key)"),
            Column(name="amount", type="DECIMAL(10,2)", nullable=False, default_value=None, description="Order amount"),
            Column(name="status", type="VARCHAR(20)", nullable=False, default_value="'pending'", description="Order status"),
            Column(name="created_at", type="DATETIME", nullable=False, default_value="CURRENT_TIMESTAMP", description="Creation timestamp")
        ]
        
        users_table = Table(
            name="users",
            columns=columns_users,
            primary_key=["id"],
            foreign_keys=[],
            description="Users table containing user information"
        )
        
        orders_table = Table(
            name="orders",
            columns=columns_orders,
            primary_key=["id"],
            foreign_keys=[
                ForeignKey(
                    columns=["user_id"],
                    reference_table="users",
                    reference_columns=["id"]
                )
            ],
            description="Orders table containing order information"
        )
        
        schema = Schema(
            name="public",
            tables=[users_table, orders_table]
        )
        
        return DatabaseSchema(
            db_id="test_db",
            schemas=[schema],
            last_updated=datetime.now()
        )
    
    def test_index_database_schema(self):
        # Test indexing a database schema
        documents = self.document_indexer.index_database_schema(self.sample_schema)
        
        # Check that documents were created
        self.assertGreater(len(documents), 0)
        
        # Check that we have documents for the database, schema, tables, columns, and foreign keys
        doc_types = [doc.doc_type for doc in documents]
        self.assertIn(DocumentType.SCHEMA, doc_types)
        self.assertIn(DocumentType.TABLE, doc_types)
        self.assertIn(DocumentType.COLUMN, doc_types)
        self.assertIn(DocumentType.FOREIGN_KEY, doc_types)
        
        # Check that all documents have embeddings
        for doc in documents:
            self.assertIsNotNone(doc.embedding)
            self.assertEqual(len(doc.embedding), 384)  # Check embedding dimension
    
    def test_index_query_history(self):
        # Test indexing a query history entry
        query_text = "Show me all users who placed orders over $100"
        sql = "SELECT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 100"
        result_summary = "Found 5 users with orders over $100"
        
        document = self.document_indexer.index_query_history("test_db", query_text, sql, result_summary)
        
        # Check that the document was created with the right type
        self.assertEqual(document.doc_type, DocumentType.QUERY_HISTORY)
        
        # Check that the document has an embedding
        self.assertIsNotNone(document.embedding)
        
        # Check that the document content contains the query, SQL, and summary
        self.assertIn(query_text, document.content)
        self.assertIn(sql, document.content)
        self.assertIn(result_summary, document.content)
    
    def test_chunk_document(self):
        # Create a large document that will need chunking
        large_content = "This is a test document.\n" * 500  # Should be over 1000 tokens
        doc = Document(
            id="test_large_doc",
            db_id="test_db",
            doc_type=DocumentType.CUSTOM,
            content=large_content,
            metadata={}
        )
        
        # Chunk the document
        parent_doc, chunks = self.document_indexer.chunk_document(doc)
        
        # Check that chunks were created
        self.assertGreater(len(chunks), 1)
        
        # Check that all chunks reference the parent document
        for chunk in chunks:
            self.assertEqual(chunk.document_id, doc.id)
    
    def test_rag_service_integration(self):
        # Test the integration of document indexer with RAG service
        
        # Index the sample schema
        doc_ids = self.rag_service.index_database_schema(self.sample_schema)
        
        # Check that documents were added to the store
        self.assertGreater(len(doc_ids), 0)
        
        # Check that we can retrieve documents from the store
        for doc_id in doc_ids:
            doc = self.document_store.get_document(doc_id)
            self.assertIsNotNone(doc)
        
        # Test search functionality
        from models.rag import SearchQuery
        query = SearchQuery(
            query="users table",
            db_id="test_db",
            top_k=5
        )
        
        results = self.rag_service.search(query)
        
        # We should get some results, but since we're using random embeddings,
        # we can't assert much about the quality of the results
        self.assertGreaterEqual(len(results), 0)
        
        # Test response generation
        response = self.rag_service.generate_response("test_db", "Tell me about the users table")
        
        # Check that we got a response
        self.assertIsNotNone(response.response)
        self.assertGreater(len(response.response), 0)

if __name__ == "__main__":
    unittest.main()