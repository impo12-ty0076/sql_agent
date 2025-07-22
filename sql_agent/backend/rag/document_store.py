import logging
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime
import pickle

from ..models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult

logger = logging.getLogger(__name__)

class DocumentStore:
    """
    Store for RAG documents and their embeddings.
    Uses FAISS for efficient similarity search.
    """
    
    def __init__(self, index_dir: str = "indexes"):
        """
        Initialize the document store.
        
        Args:
            index_dir: Directory to store indexes
        """
        self.index_dir = index_dir
        self.documents: Dict[str, Document] = {}  # id -> Document
        self.chunks: Dict[str, List[DocumentChunk]] = {}  # document_id -> List[DocumentChunk]
        self.db_indexes: Dict[str, faiss.Index] = {}  # db_id -> FAISS index
        self.db_doc_ids: Dict[str, List[str]] = {}  # db_id -> List[document_id]
        
        # Create index directory if it doesn't exist
        os.makedirs(index_dir, exist_ok=True)
    
    def add_document(self, document: Document, chunks: List[DocumentChunk] = None) -> str:
        """
        Add a document to the store.
        
        Args:
            document: Document to add
            chunks: Optional document chunks
            
        Returns:
            Document ID
        """
        # Store the document
        self.documents[document.id] = document
        
        # Store chunks if provided
        if chunks:
            self.chunks[document.id] = chunks
        
        # Add to db_doc_ids mapping
        if document.db_id not in self.db_doc_ids:
            self.db_doc_ids[document.db_id] = []
        self.db_doc_ids[document.db_id].append(document.id)
        
        # Update the index for this database
        self._update_index(document.db_id)
        
        return document.id
    
    def add_documents(self, documents: List[Document], chunks_map: Dict[str, List[DocumentChunk]] = None) -> List[str]:
        """
        Add multiple documents to the store.
        
        Args:
            documents: Documents to add
            chunks_map: Optional mapping of document ID to chunks
            
        Returns:
            List of document IDs
        """
        # Group documents by database ID
        db_docs: Dict[str, List[Document]] = {}
        for doc in documents:
            if doc.db_id not in db_docs:
                db_docs[doc.db_id] = []
            db_docs[doc.db_id].append(doc)
            
            # Store the document
            self.documents[doc.id] = doc
            
            # Store chunks if provided
            if chunks_map and doc.id in chunks_map:
                self.chunks[doc.id] = chunks_map[doc.id]
            
            # Add to db_doc_ids mapping
            if doc.db_id not in self.db_doc_ids:
                self.db_doc_ids[doc.db_id] = []
            self.db_doc_ids[doc.db_id].append(doc.id)
        
        # Update indexes for each database
        for db_id in db_docs:
            self._update_index(db_id)
        
        return [doc.id for doc in documents]
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(doc_id)
    
    def get_documents_by_db(self, db_id: str) -> List[Document]:
        """
        Get all documents for a database.
        
        Args:
            db_id: Database ID
            
        Returns:
            List of documents
        """
        doc_ids = self.db_doc_ids.get(db_id, [])
        return [self.documents[doc_id] for doc_id in doc_ids if doc_id in self.documents]
    
    def get_chunks(self, doc_id: str) -> List[DocumentChunk]:
        """
        Get chunks for a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of document chunks
        """
        return self.chunks.get(doc_id, [])
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        db_id = query.db_id
        
        # Check if we have an index for this database
        if db_id not in self.db_indexes:
            logger.warning(f"No index found for database {db_id}")
            return []
        
        # Get the index and document IDs for this database
        index = self.db_indexes[db_id]
        doc_ids = self.db_doc_ids.get(db_id, [])
        
        if not doc_ids:
            logger.warning(f"No documents found for database {db_id}")
            return []
        
        # Get embedding for the query
        # This would normally come from the LLM service, but for testing we'll use a dummy
        # In a real implementation, you would use:
        # query_embedding = llm_service.get_embeddings([query.query])[0]
        # For now, we'll use a dummy embedding of the right dimension
        dimension = index.d
        query_embedding = np.random.rand(dimension).astype(np.float32)
        
        # Search the index
        top_k = min(query.top_k, len(doc_ids))
        distances, indices = index.search(np.array([query_embedding]), top_k)
        
        # Convert to search results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(doc_ids):
                continue
                
            doc_id = doc_ids[idx]
            document = self.documents.get(doc_id)
            
            if not document:
                continue
                
            # Filter by document type if specified
            if query.filter_doc_types and document.doc_type not in query.filter_doc_types:
                continue
                
            # Convert distance to similarity score (1 - normalized distance)
            # FAISS returns squared L2 distance, so we need to normalize it
            distance = distances[0][i]
            max_distance = 2.0  # Maximum possible squared L2 distance for normalized vectors
            similarity = 1.0 - (distance / max_distance)
            
            results.append(SearchResult(document=document, score=similarity))
        
        # Sort by score in descending order
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _update_index(self, db_id: str) -> None:
        """
        Update the FAISS index for a database.
        
        Args:
            db_id: Database ID
        """
        # Get all documents for this database
        doc_ids = self.db_doc_ids.get(db_id, [])
        documents = [self.documents[doc_id] for doc_id in doc_ids if doc_id in self.documents]
        
        # Filter documents with embeddings
        docs_with_embeddings = [doc for doc in documents if doc.embedding is not None]
        
        if not docs_with_embeddings:
            logger.warning(f"No documents with embeddings found for database {db_id}")
            return
        
        # Get embeddings
        embeddings = [np.array(doc.embedding, dtype=np.float32) for doc in docs_with_embeddings]
        
        # Create or update the index
        dimension = len(embeddings[0])
        if db_id in self.db_indexes:
            # Reset the index
            self.db_indexes[db_id] = faiss.IndexFlatL2(dimension)
        else:
            # Create a new index
            self.db_indexes[db_id] = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to the index
        embeddings_array = np.array(embeddings)
        self.db_indexes[db_id].add(embeddings_array)
        
        # Update the document IDs for this database
        self.db_doc_ids[db_id] = [doc.id for doc in docs_with_embeddings]
        
        # Save the index to disk
        self._save_index(db_id)
    
    def _save_index(self, db_id: str) -> None:
        """
        Save the FAISS index for a database to disk.
        
        Args:
            db_id: Database ID
        """
        try:
            # Create a safe filename from the database ID
            safe_db_id = db_id.replace("/", "_").replace("\\", "_")
            index_path = os.path.join(self.index_dir, f"{safe_db_id}.index")
            
            # Save the FAISS index
            faiss.write_index(self.db_indexes[db_id], index_path)
            
            # Save the document IDs
            doc_ids_path = os.path.join(self.index_dir, f"{safe_db_id}.docids")
            with open(doc_ids_path, "wb") as f:
                pickle.dump(self.db_doc_ids[db_id], f)
            
            # Save the documents
            docs_path = os.path.join(self.index_dir, f"{safe_db_id}.docs")
            docs = {doc_id: self.documents[doc_id] for doc_id in self.db_doc_ids[db_id] if doc_id in self.documents}
            with open(docs_path, "wb") as f:
                pickle.dump(docs, f)
            
            # Save the chunks
            chunks_path = os.path.join(self.index_dir, f"{safe_db_id}.chunks")
            chunks = {doc_id: self.chunks.get(doc_id, []) for doc_id in self.db_doc_ids[db_id]}
            with open(chunks_path, "wb") as f:
                pickle.dump(chunks, f)
                
            logger.info(f"Saved index for database {db_id}")
        except Exception as e:
            logger.error(f"Error saving index for database {db_id}: {e}")
    
    def load_index(self, db_id: str) -> bool:
        """
        Load the FAISS index for a database from disk.
        
        Args:
            db_id: Database ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a safe filename from the database ID
            safe_db_id = db_id.replace("/", "_").replace("\\", "_")
            index_path = os.path.join(self.index_dir, f"{safe_db_id}.index")
            
            # Check if the index exists
            if not os.path.exists(index_path):
                logger.warning(f"Index file not found for database {db_id}")
                return False
            
            # Load the FAISS index
            self.db_indexes[db_id] = faiss.read_index(index_path)
            
            # Load the document IDs
            doc_ids_path = os.path.join(self.index_dir, f"{safe_db_id}.docids")
            if os.path.exists(doc_ids_path):
                with open(doc_ids_path, "rb") as f:
                    self.db_doc_ids[db_id] = pickle.load(f)
            
            # Load the documents
            docs_path = os.path.join(self.index_dir, f"{safe_db_id}.docs")
            if os.path.exists(docs_path):
                with open(docs_path, "rb") as f:
                    docs = pickle.load(f)
                    for doc_id, doc in docs.items():
                        self.documents[doc_id] = doc
            
            # Load the chunks
            chunks_path = os.path.join(self.index_dir, f"{safe_db_id}.chunks")
            if os.path.exists(chunks_path):
                with open(chunks_path, "rb") as f:
                    chunks = pickle.load(f)
                    for doc_id, doc_chunks in chunks.items():
                        self.chunks[doc_id] = doc_chunks
            
            logger.info(f"Loaded index for database {db_id}")
            return True
        except Exception as e:
            logger.error(f"Error loading index for database {db_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the store.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        if doc_id not in self.documents:
            return False
        
        # Get the database ID
        db_id = self.documents[doc_id].db_id
        
        # Remove from documents
        del self.documents[doc_id]
        
        # Remove from chunks
        if doc_id in self.chunks:
            del self.chunks[doc_id]
        
        # Remove from db_doc_ids
        if db_id in self.db_doc_ids:
            self.db_doc_ids[db_id] = [d_id for d_id in self.db_doc_ids[db_id] if d_id != doc_id]
        
        # Update the index
        self._update_index(db_id)
        
        return True
    
    def clear_db(self, db_id: str) -> bool:
        """
        Clear all documents for a database.
        
        Args:
            db_id: Database ID
            
        Returns:
            True if successful, False otherwise
        """
        if db_id not in self.db_doc_ids:
            return False
        
        # Get document IDs for this database
        doc_ids = self.db_doc_ids[db_id]
        
        # Remove from documents and chunks
        for doc_id in doc_ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
            if doc_id in self.chunks:
                del self.chunks[doc_id]
        
        # Clear db_doc_ids
        self.db_doc_ids[db_id] = []
        
        # Remove the index
        if db_id in self.db_indexes:
            del self.db_indexes[db_id]
        
        # Remove index files
        self._delete_index_files(db_id)
        
        return True
    
    def _delete_index_files(self, db_id: str) -> None:
        """
        Delete index files for a database.
        
        Args:
            db_id: Database ID
        """
        try:
            # Create a safe filename from the database ID
            safe_db_id = db_id.replace("/", "_").replace("\\", "_")
            
            # Delete the index files
            for ext in [".index", ".docids", ".docs", ".chunks"]:
                path = os.path.join(self.index_dir, f"{safe_db_id}{ext}")
                if os.path.exists(path):
                    os.remove(path)
            
            logger.info(f"Deleted index files for database {db_id}")
        except Exception as e:
            logger.error(f"Error deleting index files for database {db_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document store.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_documents": len(self.documents),
            "total_chunks": sum(len(chunks) for chunks in self.chunks.values()),
            "databases": {}
        }
        
        for db_id in self.db_doc_ids:
            doc_ids = self.db_doc_ids[db_id]
            doc_types: Dict[str, int] = {}
            
            for doc_id in doc_ids:
                if doc_id in self.documents:
                    doc_type = self.documents[doc_id].doc_type
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            stats["databases"][db_id] = {
                "documents": len(doc_ids),
                "document_types": doc_types,
                "chunks": sum(len(self.chunks.get(doc_id, [])) for doc_id in doc_ids)
            }
        
        return stats