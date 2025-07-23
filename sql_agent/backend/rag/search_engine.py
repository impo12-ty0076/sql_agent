import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from collections import Counter
import re
import math

try:
    from ..models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult
    from .text_utils import normalize_text, tokenize, extract_keywords, calculate_text_similarity
except ImportError:
    # Try absolute imports
    from sql_agent.backend.models.rag import Document, DocumentChunk, DocumentType, SearchQuery, SearchResult
    from sql_agent.backend.rag.text_utils import normalize_text, tokenize, extract_keywords, calculate_text_similarity

logger = logging.getLogger(__name__)

class SearchEngine:
    """
    Advanced search engine for RAG documents supporting keyword-based search,
    embedding similarity search, and hybrid search algorithms.
    """
    
    def __init__(self):
        """
        Initialize the search engine.
        """
        self.documents: Dict[str, Document] = {}  # id -> Document
        self.db_documents: Dict[str, List[str]] = {}  # db_id -> List[document_id]
        self.keyword_index: Dict[str, Dict[str, Set[str]]] = {}  # db_id -> keyword -> Set[document_id]
        self.document_keywords: Dict[str, List[str]] = {}  # document_id -> List[keywords]
        
    def add_document(self, document: Document) -> None:
        """
        Add a document to the search engine.
        
        Args:
            document: Document to add
        """
        # Store the document
        self.documents[document.id] = document
        
        # Add to database document mapping
        if document.db_id not in self.db_documents:
            self.db_documents[document.db_id] = []
        self.db_documents[document.db_id].append(document.id)
        
        # Build keyword index for this document
        self._index_document_keywords(document)
        
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add multiple documents to the search engine.
        
        Args:
            documents: List of documents to add
        """
        for document in documents:
            self.add_document(document)
    
    def _index_document_keywords(self, document: Document) -> None:
        """
        Index keywords for a document.
        
        Args:
            document: Document to index
        """
        # Extract keywords from document content
        content_keywords = extract_keywords(document.content, max_keywords=20, include_sql_keywords=True)
        
        # Extract keywords from metadata if available
        metadata_keywords = []
        if document.metadata:
            # Extract keywords from metadata values
            for key, value in document.metadata.items():
                if isinstance(value, str):
                    metadata_keywords.extend(extract_keywords(value, max_keywords=5))
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    # Handle list of strings (like keywords field)
                    metadata_keywords.extend(value)
        
        # Combine all keywords
        all_keywords = list(set(content_keywords + metadata_keywords))
        
        # Store document keywords
        self.document_keywords[document.id] = all_keywords
        
        # Update keyword index
        if document.db_id not in self.keyword_index:
            self.keyword_index[document.db_id] = {}
        
        for keyword in all_keywords:
            keyword = keyword.lower()
            if keyword not in self.keyword_index[document.db_id]:
                self.keyword_index[document.db_id][keyword] = set()
            self.keyword_index[document.db_id][keyword].add(document.id)
    
    def keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform keyword-based search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results sorted by relevance
        """
        db_id = query.db_id
        
        # Check if we have documents for this database
        if db_id not in self.db_documents:
            logger.warning(f"No documents found for database {db_id}")
            return []
        
        # Extract keywords from the query
        query_keywords = extract_keywords(query.query, max_keywords=10, include_sql_keywords=True)
        query_tokens = tokenize(query.query.lower(), remove_stopwords=True, keep_sql_keywords=True)
        
        if not query_keywords and not query_tokens:
            logger.warning("No keywords extracted from query")
            return []
        
        # Calculate scores for each document
        document_scores: Dict[str, float] = {}
        
        for doc_id in self.db_documents[db_id]:
            document = self.documents.get(doc_id)
            if not document:
                continue
            
            # Filter by document type if specified
            if query.filter_doc_types and document.doc_type not in query.filter_doc_types:
                continue
            
            # Calculate keyword-based score
            score = self._calculate_keyword_score(
                document, query_keywords, query_tokens, db_id
            )
            
            if score > 0:
                document_scores[doc_id] = score
        
        # Sort by score and return top results
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:query.top_k]
        
        # Create search results
        results = []
        for doc_id, score in top_docs:
            document = self.documents[doc_id]
            results.append(SearchResult(document=document, score=score))
        
        return results
    
    def _calculate_keyword_score(
        self, document: Document, query_keywords: List[str], 
        query_tokens: List[str], db_id: str
    ) -> float:
        """
        Calculate keyword-based relevance score for a document.
        
        Args:
            document: Document to score
            query_keywords: Extracted keywords from query
            query_tokens: All tokens from query
            db_id: Database ID
            
        Returns:
            Relevance score
        """
        score = 0.0
        
        # Get document keywords
        doc_keywords = self.document_keywords.get(document.id, [])
        doc_content_lower = document.content.lower()
        doc_tokens = tokenize(doc_content_lower, remove_stopwords=True, keep_sql_keywords=True)
        
        # 1. Exact keyword matches (highest weight)
        keyword_matches = 0
        for keyword in query_keywords:
            if keyword.lower() in [k.lower() for k in doc_keywords]:
                keyword_matches += 1
                score += 3.0  # High weight for exact keyword matches
        
        # 2. Content-based matches
        content_matches = 0
        for token in query_tokens:
            if token.lower() in doc_content_lower:
                content_matches += 1
                score += 1.0  # Medium weight for content matches
        
        # 3. TF-IDF-like scoring for query tokens
        total_docs = len(self.db_documents.get(db_id, []))
        if total_docs > 0:
            for token in query_tokens:
                # Term frequency in document
                tf = doc_tokens.count(token.lower())
                if tf > 0:
                    # Document frequency (how many documents contain this term)
                    df = len(self.keyword_index.get(db_id, {}).get(token.lower(), set()))
                    if df > 0:
                        # TF-IDF score
                        idf = math.log(total_docs / df)
                        score += tf * idf * 0.5  # Lower weight for TF-IDF
        
        # 4. Document type bonus
        type_bonus = self._get_document_type_bonus(document.doc_type, query_tokens)
        score += type_bonus
        
        # 5. Metadata matches
        if document.metadata:
            for key, value in document.metadata.items():
                if isinstance(value, str):
                    for token in query_tokens:
                        if token.lower() in value.lower():
                            score += 0.5  # Lower weight for metadata matches
        
        # Normalize score by document length to avoid bias towards longer documents
        if len(doc_tokens) > 0:
            score = score / math.log(len(doc_tokens) + 1)
        
        return score
    
    def _get_document_type_bonus(self, doc_type: DocumentType, query_tokens: List[str]) -> float:
        """
        Get bonus score based on document type and query content.
        
        Args:
            doc_type: Document type
            query_tokens: Query tokens
            
        Returns:
            Bonus score
        """
        bonus = 0.0
        
        # Check for type-specific keywords in query
        table_keywords = ['table', 'tables', 'entity', 'entities']
        column_keywords = ['column', 'columns', 'field', 'fields', 'attribute', 'attributes']
        schema_keywords = ['schema', 'database', 'structure', 'overview']
        relationship_keywords = ['relationship', 'join', 'foreign', 'key', 'reference']
        
        query_text = ' '.join(query_tokens).lower()
        
        if doc_type == DocumentType.TABLE:
            if any(keyword in query_text for keyword in table_keywords):
                bonus += 1.0
        elif doc_type == DocumentType.COLUMN:
            if any(keyword in query_text for keyword in column_keywords):
                bonus += 1.0
        elif doc_type == DocumentType.SCHEMA:
            if any(keyword in query_text for keyword in schema_keywords):
                bonus += 1.0
        elif doc_type == DocumentType.FOREIGN_KEY:
            if any(keyword in query_text for keyword in relationship_keywords):
                bonus += 1.0
        
        return bonus
    
    def embedding_search(
        self, query: SearchQuery, query_embedding: Optional[List[float]] = None
    ) -> List[SearchResult]:
        """
        Perform embedding-based similarity search.
        
        Args:
            query: Search query
            query_embedding: Pre-computed query embedding (optional)
            
        Returns:
            List of search results sorted by similarity
        """
        db_id = query.db_id
        
        # Check if we have documents for this database
        if db_id not in self.db_documents:
            logger.warning(f"No documents found for database {db_id}")
            return []
        
        # If no query embedding provided, we can't perform embedding search
        if query_embedding is None:
            logger.warning("No query embedding provided for embedding search")
            return []
        
        # Calculate similarity scores for each document
        document_scores: Dict[str, float] = {}
        
        for doc_id in self.db_documents[db_id]:
            document = self.documents.get(doc_id)
            if not document or document.embedding is None:
                continue
            
            # Filter by document type if specified
            if query.filter_doc_types and document.doc_type not in query.filter_doc_types:
                continue
            
            # Calculate cosine similarity
            similarity = self._calculate_cosine_similarity(query_embedding, document.embedding)
            
            if similarity > 0:
                document_scores[doc_id] = similarity
        
        # Sort by similarity and return top results
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:query.top_k]
        
        # Create search results
        results = []
        for doc_id, score in top_docs:
            document = self.documents[doc_id]
            results.append(SearchResult(document=document, score=score))
        
        return results
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # Ensure the result is between 0 and 1
            return max(0.0, min(1.0, similarity))
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def hybrid_search(
        self, query: SearchQuery, query_embedding: Optional[List[float]] = None,
        keyword_weight: float = 0.6, embedding_weight: float = 0.4
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining keyword and embedding-based search.
        
        Args:
            query: Search query
            query_embedding: Pre-computed query embedding (optional)
            keyword_weight: Weight for keyword search results (0-1)
            embedding_weight: Weight for embedding search results (0-1)
            
        Returns:
            List of search results sorted by combined relevance
        """
        # Normalize weights
        total_weight = keyword_weight + embedding_weight
        if total_weight > 0:
            keyword_weight = keyword_weight / total_weight
            embedding_weight = embedding_weight / total_weight
        else:
            keyword_weight = 0.6
            embedding_weight = 0.4
        
        # Perform keyword search
        keyword_results = self.keyword_search(query)
        keyword_scores = {result.document.id: result.score for result in keyword_results}
        
        # Perform embedding search if embedding is available
        embedding_scores = {}
        if query_embedding is not None:
            embedding_results = self.embedding_search(query, query_embedding)
            embedding_scores = {result.document.id: result.score for result in embedding_results}
        
        # Combine scores
        combined_scores: Dict[str, float] = {}
        all_doc_ids = set(keyword_scores.keys()) | set(embedding_scores.keys())
        
        for doc_id in all_doc_ids:
            # Normalize scores to 0-1 range
            keyword_score = keyword_scores.get(doc_id, 0.0)
            embedding_score = embedding_scores.get(doc_id, 0.0)
            
            # Normalize keyword scores
            if keyword_results:
                max_keyword_score = max(result.score for result in keyword_results)
                if max_keyword_score > 0:
                    keyword_score = keyword_score / max_keyword_score
            
            # Embedding scores are already normalized (cosine similarity)
            
            # Calculate combined score
            combined_score = (keyword_weight * keyword_score + 
                            embedding_weight * embedding_score)
            
            combined_scores[doc_id] = combined_score
        
        # Sort by combined score and return top results
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:query.top_k]
        
        # Create search results
        results = []
        for doc_id, score in top_docs:
            document = self.documents[doc_id]
            results.append(SearchResult(document=document, score=score))
        
        return results
    
    def fuzzy_search(self, query: SearchQuery, max_distance: int = 2) -> List[SearchResult]:
        """
        Perform fuzzy search to handle typos and variations in keywords.
        
        Args:
            query: Search query
            max_distance: Maximum edit distance for fuzzy matching
            
        Returns:
            List of search results
        """
        db_id = query.db_id
        
        # Check if we have documents for this database
        if db_id not in self.db_documents:
            logger.warning(f"No documents found for database {db_id}")
            return []
        
        # Extract query tokens
        query_tokens = tokenize(query.query.lower(), remove_stopwords=True, keep_sql_keywords=True)
        
        if not query_tokens:
            return []
        
        # Find fuzzy matches for each query token
        fuzzy_matches: Dict[str, List[str]] = {}
        
        if db_id in self.keyword_index:
            for query_token in query_tokens:
                matches = []
                for keyword in self.keyword_index[db_id].keys():
                    distance = self._calculate_edit_distance(query_token, keyword)
                    if distance <= max_distance:
                        matches.append(keyword)
                fuzzy_matches[query_token] = matches
        
        # Score documents based on fuzzy matches
        document_scores: Dict[str, float] = {}
        
        for doc_id in self.db_documents[db_id]:
            document = self.documents.get(doc_id)
            if not document:
                continue
            
            # Filter by document type if specified
            if query.filter_doc_types and document.doc_type not in query.filter_doc_types:
                continue
            
            score = 0.0
            
            # Calculate score based on fuzzy matches
            for query_token, matched_keywords in fuzzy_matches.items():
                for keyword in matched_keywords:
                    if doc_id in self.keyword_index[db_id].get(keyword, set()):
                        # Score decreases with edit distance
                        distance = self._calculate_edit_distance(query_token, keyword)
                        fuzzy_score = 1.0 / (1.0 + distance)
                        score += fuzzy_score
            
            if score > 0:
                document_scores[doc_id] = score
        
        # Sort by score and return top results
        sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:query.top_k]
        
        # Create search results
        results = []
        for doc_id, score in top_docs:
            document = self.documents[doc_id]
            results.append(SearchResult(document=document, score=score))
        
        return results
    
    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """
        Calculate edit distance (Levenshtein distance) between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def search(
        self, query: SearchQuery, query_embedding: Optional[List[float]] = None,
        search_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        Main search method that delegates to specific search algorithms.
        
        Args:
            query: Search query
            query_embedding: Pre-computed query embedding (optional)
            search_type: Type of search ("keyword", "embedding", "hybrid", "fuzzy")
            
        Returns:
            List of search results
        """
        if search_type == "keyword":
            return self.keyword_search(query)
        elif search_type == "embedding":
            return self.embedding_search(query, query_embedding)
        elif search_type == "fuzzy":
            return self.fuzzy_search(query)
        elif search_type == "hybrid":
            return self.hybrid_search(query, query_embedding)
        else:
            logger.warning(f"Unknown search type: {search_type}. Using hybrid search.")
            return self.hybrid_search(query, query_embedding)
    
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
        doc_ids = self.db_documents.get(db_id, [])
        return [self.documents[doc_id] for doc_id in doc_ids if doc_id in self.documents]
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the search engine.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        if doc_id not in self.documents:
            return False
        
        document = self.documents[doc_id]
        db_id = document.db_id
        
        # Remove from documents
        del self.documents[doc_id]
        
        # Remove from database document mapping
        if db_id in self.db_documents:
            self.db_documents[db_id] = [d_id for d_id in self.db_documents[db_id] if d_id != doc_id]
        
        # Remove from keyword index
        if doc_id in self.document_keywords:
            keywords = self.document_keywords[doc_id]
            for keyword in keywords:
                if db_id in self.keyword_index and keyword in self.keyword_index[db_id]:
                    self.keyword_index[db_id][keyword].discard(doc_id)
                    # Remove empty keyword entries
                    if not self.keyword_index[db_id][keyword]:
                        del self.keyword_index[db_id][keyword]
            del self.document_keywords[doc_id]
        
        return True
    
    def clear_database(self, db_id: str) -> bool:
        """
        Clear all documents for a database.
        
        Args:
            db_id: Database ID
            
        Returns:
            True if successful, False otherwise
        """
        if db_id not in self.db_documents:
            return False
        
        # Get document IDs for this database
        doc_ids = self.db_documents[db_id].copy()
        
        # Remove each document
        for doc_id in doc_ids:
            self.remove_document(doc_id)
        
        # Clear database mappings
        if db_id in self.db_documents:
            del self.db_documents[db_id]
        if db_id in self.keyword_index:
            del self.keyword_index[db_id]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search engine.
        
        Returns:
            Dictionary of statistics
        """
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