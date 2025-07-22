import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio
import re
import uuid

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..models.database import DatabaseSchema, Schema, Table, Column, ForeignKey
from ..models.rag import Document, DocumentType, DocumentChunk
from ..llm.base import LLMService
from .text_utils import normalize_text, extract_keywords

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """
    Class responsible for indexing database schema and metadata into documents
    that can be used by the RAG system.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the document indexer.
        
        Args:
            llm_service: LLM service for generating embeddings
        """
        self.llm_service = llm_service
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=self._get_token_length,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _get_token_length(self, text: str) -> int:
        """
        Get the number of tokens in a text using tiktoken.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback to approximate token count (1 token ≈ 4 chars)
            return len(text) // 4
            
    def _preprocess_text_for_embedding(self, text: str) -> str:
        """
        텍스트를 임베딩 생성을 위해 전처리
        
        Args:
            text (str): 전처리할 텍스트
            
        Returns:
            str: 전처리된 텍스트
        """
        # 줄바꿈 정규화
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 연속된 공백 제거
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def index_database_schema(self, db_schema: DatabaseSchema) -> List[Document]:
        """
        Index a database schema into documents.
        
        Args:
            db_schema: Database schema to index
            
        Returns:
            List of created documents
        """
        documents = []
        
        # Create a document for the entire database schema
        db_doc = self._create_database_document(db_schema)
        documents.append(db_doc)
        
        # Create documents for each schema
        for schema in db_schema.schemas:
            schema_doc = self._create_schema_document(db_schema.db_id, schema)
            documents.append(schema_doc)
            
            # Create documents for each table
            for table in schema.tables:
                table_doc = self._create_table_document(db_schema.db_id, schema.name, table)
                documents.append(table_doc)
                
                # Create documents for each column
                for column in table.columns:
                    column_doc = self._create_column_document(
                        db_schema.db_id, schema.name, table.name, column
                    )
                    documents.append(column_doc)
                
                # Create documents for each foreign key
                for fk in table.foreign_keys:
                    fk_doc = self._create_foreign_key_document(
                        db_schema.db_id, schema.name, table.name, fk
                    )
                    documents.append(fk_doc)
        
        # Generate embeddings for all documents
        return self._generate_embeddings(documents)
    
    def _create_database_document(self, db_schema: DatabaseSchema) -> Document:
        """
        Create a document for the entire database schema.
        
        Args:
            db_schema: Database schema
            
        Returns:
            Document for the database schema
        """
        # Create a summary of the database schema
        schema_names = [schema.name for schema in db_schema.schemas]
        table_count = sum(len(schema.tables) for schema in db_schema.schemas)
        column_count = sum(len(table.columns) for schema in db_schema.schemas for table in schema.tables)
        
        content = f"Database ID: {db_schema.db_id}\n"
        content += f"Schemas: {', '.join(schema_names)}\n"
        content += f"Total tables: {table_count}\n"
        content += f"Total columns: {column_count}\n\n"
        
        # Add a list of all tables with column counts
        content += "Database Structure Overview:\n"
        for schema in db_schema.schemas:
            content += f"- Schema '{schema.name}':\n"
            for table in schema.tables:
                pk_info = f" (PK: {', '.join(table.primary_key)})" if table.primary_key else ""
                content += f"  - Table '{table.name}'{pk_info}: {len(table.columns)} columns\n"
                if table.description:
                    content += f"    Description: {table.description}\n"
        
        # Add relationships overview
        content += "\nRelationships Overview:\n"
        for schema in db_schema.schemas:
            for table in schema.tables:
                if table.foreign_keys:
                    content += f"- Table '{schema.name}.{table.name}' has relationships with:\n"
                    for fk in table.foreign_keys:
                        content += f"  - {fk.reference_table} (via columns: {', '.join(fk.columns)} -> {', '.join(fk.reference_columns)})\n"
        
        # Extract keywords for better search
        keywords = extract_keywords(content, max_keywords=20, include_sql_keywords=True)
        
        return Document(
            id=f"db_{db_schema.db_id}_overview",
            db_id=db_schema.db_id,
            doc_type=DocumentType.SCHEMA,
            content=content,
            metadata={
                "schema_count": len(db_schema.schemas),
                "table_count": table_count,
                "column_count": column_count,
                "keywords": keywords,
                "last_updated": db_schema.last_updated.isoformat()
            }
        )
    
    def _create_schema_document(self, db_id: str, schema: Schema) -> Document:
        """
        Create a document for a database schema.
        
        Args:
            db_id: Database ID
            schema: Schema to create document for
            
        Returns:
            Document for the schema
        """
        content = f"Schema: {schema.name}\n"
        content += f"Tables: {len(schema.tables)}\n"
        
        # Calculate total columns
        total_columns = sum(len(table.columns) for table in schema.tables)
        content += f"Total columns: {total_columns}\n\n"
        
        # Add a list of tables in this schema with column counts
        content += "Tables in this schema:\n"
        for table in schema.tables:
            pk_info = f" (PK: {', '.join(table.primary_key)})" if table.primary_key else ""
            content += f"- {table.name}{pk_info}: {len(table.columns)} columns\n"
            if table.description:
                content += f"  Description: {table.description}\n"
        
        # Add relationship information
        tables_with_fks = [table for table in schema.tables if table.foreign_keys]
        if tables_with_fks:
            content += "\nRelationships in this schema:\n"
            for table in tables_with_fks:
                content += f"- Table '{table.name}' has relationships with:\n"
                for fk in table.foreign_keys:
                    content += f"  - {fk.reference_table} (via columns: {', '.join(fk.columns)} -> {', '.join(fk.reference_columns)})\n"
        
        # Extract keywords for better search
        keywords = extract_keywords(content, max_keywords=15, include_sql_keywords=True)
        
        return Document(
            id=f"schema_{db_id}_{schema.name}",
            db_id=db_id,
            doc_type=DocumentType.SCHEMA,
            content=content,
            metadata={
                "schema_name": schema.name,
                "table_count": len(schema.tables),
                "column_count": total_columns,
                "keywords": keywords
            }
        )
    
    def _create_table_document(self, db_id: str, schema_name: str, table: Table) -> Document:
        """
        Create a document for a database table.
        
        Args:
            db_id: Database ID
            schema_name: Schema name
            table: Table to create document for
            
        Returns:
            Document for the table
        """
        content = f"Table: {schema_name}.{table.name}\n"
        if table.description:
            content += f"Description: {table.description}\n"
        content += f"Columns: {len(table.columns)}\n"
        
        # Add primary key information
        if table.primary_key:
            content += f"Primary Key: {', '.join(table.primary_key)}\n"
        
        # Add foreign key count
        if table.foreign_keys:
            content += f"Foreign Keys: {len(table.foreign_keys)}\n"
        
        # Add detailed column information
        content += "\nColumns:\n"
        for column in table.columns:
            # Mark primary key columns
            pk_marker = " (PK)" if column.name in table.primary_key else ""
            # Mark foreign key columns
            fk_marker = ""
            for fk in table.foreign_keys:
                if column.name in fk.columns:
                    fk_marker = f" (FK -> {fk.reference_table})"
                    break
            
            content += f"- {column.name}{pk_marker}{fk_marker} ({column.type})"
            if column.description:
                content += f": {column.description}"
            if not column.nullable:
                content += " (NOT NULL)"
            if column.default_value is not None:
                content += f" (DEFAULT: {column.default_value})"
            content += "\n"
        
        # Add detailed foreign key information
        if table.foreign_keys:
            content += "\nForeign Keys (Relationships):\n"
            for i, fk in enumerate(table.foreign_keys):
                content += f"- Relationship {i+1}: This table's {', '.join(fk.columns)} references {fk.reference_table}'s {', '.join(fk.reference_columns)}\n"
                content += f"  This means each record in {table.name} is related to a record in {fk.reference_table}\n"
        
        # Add sample queries section to help with natural language to SQL conversion
        content += "\nSample Queries:\n"
        content += f"- SELECT * FROM {schema_name}.{table.name} LIMIT 10;\n"
        if table.primary_key:
            pk_col = table.primary_key[0]
            content += f"- SELECT * FROM {schema_name}.{table.name} WHERE {pk_col} = [value];\n"
        
        # If there are foreign keys, add a sample join query
        if table.foreign_keys:
            fk = table.foreign_keys[0]
            content += f"- SELECT t1.*, t2.* FROM {schema_name}.{table.name} t1 JOIN {fk.reference_table} t2 ON t1.{fk.columns[0]} = t2.{fk.reference_columns[0]};\n"
        
        # Extract keywords for better search
        column_names = [col.name for col in table.columns]
        combined_text = f"{table.name} {' '.join(column_names)} {table.description or ''}"
        keywords = extract_keywords(combined_text, max_keywords=15, include_sql_keywords=True)
        
        return Document(
            id=f"table_{db_id}_{schema_name}_{table.name}",
            db_id=db_id,
            doc_type=DocumentType.TABLE,
            content=content,
            metadata={
                "schema_name": schema_name,
                "table_name": table.name,
                "column_count": len(table.columns),
                "has_primary_key": bool(table.primary_key),
                "has_foreign_keys": bool(table.foreign_keys),
                "has_description": bool(table.description),
                "column_names": column_names,
                "keywords": keywords
            }
        )
    
    def _create_column_document(
        self, db_id: str, schema_name: str, table_name: str, column: Column
    ) -> Document:
        """
        Create a document for a database column.
        
        Args:
            db_id: Database ID
            schema_name: Schema name
            table_name: Table name
            column: Column to create document for
            
        Returns:
            Document for the column
        """
        content = f"Column: {schema_name}.{table_name}.{column.name}\n"
        content += f"Type: {column.type}\n"
        content += f"Nullable: {column.nullable}\n"
        
        if column.default_value is not None:
            content += f"Default Value: {column.default_value}\n"
        
        if column.description:
            content += f"Description: {column.description}\n"
        
        # Add information about common SQL operations with this column
        content += "\nCommon SQL operations with this column:\n"
        
        # Select operation
        content += f"- SELECT {column.name} FROM {schema_name}.{table_name};\n"
        
        # Filter operation
        if column.type.lower() in ['varchar', 'nvarchar', 'char', 'nchar', 'text', 'string']:
            content += f"- SELECT * FROM {schema_name}.{table_name} WHERE {column.name} LIKE '%value%';\n"
        elif column.type.lower() in ['int', 'integer', 'bigint', 'smallint', 'tinyint', 'decimal', 'numeric', 'float', 'real']:
            content += f"- SELECT * FROM {schema_name}.{table_name} WHERE {column.name} > [number_value];\n"
        elif column.type.lower() in ['date', 'datetime', 'timestamp']:
            content += f"- SELECT * FROM {schema_name}.{table_name} WHERE {column.name} BETWEEN '[start_date]' AND '[end_date]';\n"
        else:
            content += f"- SELECT * FROM {schema_name}.{table_name} WHERE {column.name} = [value];\n"
        
        # Aggregation operation
        if column.type.lower() in ['int', 'integer', 'bigint', 'smallint', 'tinyint', 'decimal', 'numeric', 'float', 'real']:
            content += f"- SELECT AVG({column.name}), SUM({column.name}), MIN({column.name}), MAX({column.name}) FROM {schema_name}.{table_name};\n"
        
        # Group by operation
        content += f"- SELECT {column.name}, COUNT(*) FROM {schema_name}.{table_name} GROUP BY {column.name};\n"
        
        # Order by operation
        content += f"- SELECT * FROM {schema_name}.{table_name} ORDER BY {column.name} DESC;\n"
        
        # Extract keywords for better search
        combined_text = f"{column.name} {column.type} {column.description or ''} {table_name}"
        keywords = extract_keywords(combined_text, max_keywords=10, include_sql_keywords=True)
        
        # Determine if this column might be a primary or foreign key based on name patterns
        is_potential_pk = column.name.lower() in ['id', 'key', f'{table_name.lower()}_id', f'{table_name.lower()}_key']
        is_potential_fk = '_id' in column.name.lower() or '_key' in column.name.lower()
        
        return Document(
            id=f"column_{db_id}_{schema_name}_{table_name}_{column.name}",
            db_id=db_id,
            doc_type=DocumentType.COLUMN,
            content=content,
            metadata={
                "schema_name": schema_name,
                "table_name": table_name,
                "column_name": column.name,
                "column_type": column.type,
                "nullable": column.nullable,
                "has_default": column.default_value is not None,
                "has_description": bool(column.description),
                "potential_primary_key": is_potential_pk,
                "potential_foreign_key": is_potential_fk,
                "keywords": keywords
            }
        )
    
    def _create_foreign_key_document(
        self, db_id: str, schema_name: str, table_name: str, fk: ForeignKey
    ) -> Document:
        """
        Create a document for a foreign key relationship.
        
        Args:
            db_id: Database ID
            schema_name: Schema name
            table_name: Table name
            fk: Foreign key to create document for
            
        Returns:
            Document for the foreign key
        """
        # Create a unique identifier for this foreign key
        fk_id = f"{table_name}_{'-'.join(fk.columns)}_to_{fk.reference_table}_{'-'.join(fk.reference_columns)}"
        
        content = f"Foreign Key Relationship: {schema_name}.{table_name}.{', '.join(fk.columns)} -> {fk.reference_table}.{', '.join(fk.reference_columns)}\n\n"
        
        # Detailed explanation of the relationship
        content += f"This foreign key defines a relationship between the table '{table_name}' "
        content += f"and the table '{fk.reference_table}'. "
        content += f"The columns {', '.join(fk.columns)} in '{table_name}' reference "
        content += f"the columns {', '.join(fk.reference_columns)} in '{fk.reference_table}'.\n\n"
        
        # Business meaning explanation
        content += "Business Meaning:\n"
        content += f"Each record in the '{table_name}' table is related to a record in the '{fk.reference_table}' table. "
        content += f"This typically represents a '{table_name}' belongs to a '{fk.reference_table}' relationship "
        content += f"or a '{fk.reference_table}' has many '{table_name}' relationship.\n\n"
        
        # Sample join queries
        content += "Sample Join Queries:\n"
        
        # Inner join
        content += f"-- Inner join (only matching records)\n"
        content += f"SELECT t1.*, t2.*\n"
        content += f"FROM {schema_name}.{table_name} t1\n"
        content += f"INNER JOIN {schema_name}.{fk.reference_table} t2\n"
        content += f"ON t1.{fk.columns[0]} = t2.{fk.reference_columns[0]};\n\n"
        
        # Left join
        content += f"-- Left join (all records from {table_name}, even without matches)\n"
        content += f"SELECT t1.*, t2.*\n"
        content += f"FROM {schema_name}.{table_name} t1\n"
        content += f"LEFT JOIN {schema_name}.{fk.reference_table} t2\n"
        content += f"ON t1.{fk.columns[0]} = t2.{fk.reference_columns[0]};\n\n"
        
        # Right join
        content += f"-- Right join (all records from {fk.reference_table}, even without matches)\n"
        content += f"SELECT t1.*, t2.*\n"
        content += f"FROM {schema_name}.{table_name} t1\n"
        content += f"RIGHT JOIN {schema_name}.{fk.reference_table} t2\n"
        content += f"ON t1.{fk.columns[0]} = t2.{fk.reference_columns[0]};\n"
        
        # Extract keywords for better search
        combined_text = f"{table_name} {' '.join(fk.columns)} {fk.reference_table} {' '.join(fk.reference_columns)} relationship join foreign key"
        keywords = extract_keywords(combined_text, max_keywords=15, include_sql_keywords=True)
        
        return Document(
            id=f"fk_{db_id}_{schema_name}_{fk_id}",
            db_id=db_id,
            doc_type=DocumentType.FOREIGN_KEY,
            content=content,
            metadata={
                "schema_name": schema_name,
                "table_name": table_name,
                "columns": fk.columns,
                "reference_table": fk.reference_table,
                "reference_columns": fk.reference_columns,
                "relationship_type": "many_to_one",  # Assuming most FKs represent many-to-one relationships
                "keywords": keywords
            }
        )
    
    def index_query_history(
        self, db_id: str, query_text: str, sql: str, result_summary: Optional[str] = None
    ) -> Document:
        """
        Index a query history entry.
        
        Args:
            db_id: Database ID
            query_text: Natural language query
            sql: Generated SQL
            result_summary: Optional summary of the query results
            
        Returns:
            Created document with embedding
        """
        # Create a unique ID for this query history entry
        query_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        content = f"Natural Language Query: {query_text}\n\n"
        content += f"Generated SQL Query:\n```sql\n{sql}\n```\n\n"
        
        if result_summary:
            content += f"Result Summary: {result_summary}\n\n"
        
        # Extract SQL components for better understanding
        sql_components = self._extract_sql_components(sql)
        
        # Add explanation of the SQL query
        content += "SQL Query Explanation:\n"
        if "select" in sql_components:
            content += f"- Selecting: {sql_components['select']}\n"
        if "from" in sql_components:
            content += f"- From tables: {sql_components['from']}\n"
        if "join" in sql_components:
            content += f"- Joining with: {sql_components['join']}\n"
        if "where" in sql_components:
            content += f"- Where conditions: {sql_components['where']}\n"
        if "group_by" in sql_components:
            content += f"- Grouping by: {sql_components['group_by']}\n"
        if "order_by" in sql_components:
            content += f"- Ordering by: {sql_components['order_by']}\n"
        
        # Extract keywords for better search
        keywords = extract_keywords(query_text + " " + sql, max_keywords=15, include_sql_keywords=True)
        
        doc = Document(
            id=f"query_history_{db_id}_{query_id}",
            db_id=db_id,
            doc_type=DocumentType.QUERY_HISTORY,
            content=content,
            metadata={
                "query_text": query_text,
                "sql": sql,
                "has_summary": bool(result_summary),
                "timestamp": timestamp,
                "sql_components": sql_components,
                "keywords": keywords
            }
        )
        
        # Generate embedding for the document
        docs_with_embeddings = self._generate_embeddings([doc])
        return docs_with_embeddings[0]
        
    def _extract_sql_components(self, sql: str) -> Dict[str, str]:
        """
        Extract components from an SQL query for better indexing and searching.
        
        Args:
            sql: SQL query string
            
        Returns:
            Dictionary of SQL components
        """
        components = {}
        
        # Normalize SQL for easier parsing
        normalized_sql = sql.lower().replace("\n", " ").strip()
        
        # Extract SELECT clause
        select_match = re.search(r'select\s+(.*?)\s+from', normalized_sql)
        if select_match:
            components["select"] = select_match.group(1).strip()
        
        # Extract FROM clause
        from_match = re.search(r'from\s+(.*?)(?:\s+where|\s+group\s+by|\s+order\s+by|\s+limit|\s*$)', normalized_sql)
        if from_match:
            components["from"] = from_match.group(1).strip()
        
        # Extract JOIN clauses
        join_pattern = r'(inner\s+join|left\s+join|right\s+join|full\s+join|join)\s+(.*?)(?:\s+on\s+(.*?))?(?:\s+where|\s+group\s+by|\s+order\s+by|\s+limit|\s+inner\s+join|\s+left\s+join|\s+right\s+join|\s+full\s+join|\s+join|\s*$)'
        join_matches = re.findall(join_pattern, normalized_sql)
        if join_matches:
            join_clauses = []
            for join_type, table, on_clause in join_matches:
                join_info = f"{join_type} {table}"
                if on_clause:
                    join_info += f" ON {on_clause}"
                join_clauses.append(join_info)
            components["join"] = "; ".join(join_clauses)
        
        # Extract WHERE clause
        where_match = re.search(r'where\s+(.*?)(?:\s+group\s+by|\s+order\s+by|\s+limit|\s*$)', normalized_sql)
        if where_match:
            components["where"] = where_match.group(1).strip()
        
        # Extract GROUP BY clause
        group_by_match = re.search(r'group\s+by\s+(.*?)(?:\s+having|\s+order\s+by|\s+limit|\s*$)', normalized_sql)
        if group_by_match:
            components["group_by"] = group_by_match.group(1).strip()
        
        # Extract HAVING clause
        having_match = re.search(r'having\s+(.*?)(?:\s+order\s+by|\s+limit|\s*$)', normalized_sql)
        if having_match:
            components["having"] = having_match.group(1).strip()
        
        # Extract ORDER BY clause
        order_by_match = re.search(r'order\s+by\s+(.*?)(?:\s+limit|\s*$)', normalized_sql)
        if order_by_match:
            components["order_by"] = order_by_match.group(1).strip()
        
        # Extract LIMIT clause
        limit_match = re.search(r'limit\s+(.*?)$', normalized_sql)
        if limit_match:
            components["limit"] = limit_match.group(1).strip()
        
        return components
    
    def index_custom_document(
        self, db_id: str, content: str, title: str = "", doc_type: DocumentType = DocumentType.CUSTOM, 
        metadata: Dict[str, Any] = None
    ) -> Document:
        """
        Index a custom document.
        
        Args:
            db_id: Database ID
            content: Document content
            title: Optional document title
            doc_type: Document type (default: CUSTOM)
            metadata: Additional metadata
            
        Returns:
            Created document with embedding
        """
        if metadata is None:
            metadata = {}
            
        # Create a unique ID for this custom document
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Add title to content if provided
        formatted_content = content
        if title:
            formatted_content = f"{title}\n\n{content}"
            metadata["title"] = title
            
        # Extract keywords for better search
        keywords = extract_keywords(formatted_content, max_keywords=15, include_sql_keywords=True)
        
        # Add timestamp to metadata
        metadata["timestamp"] = timestamp
        metadata["keywords"] = keywords
        
        doc = Document(
            id=f"custom_{db_id}_{doc_id}",
            db_id=db_id,
            doc_type=doc_type,
            content=formatted_content,
            metadata=metadata
        )
        
        # Generate embedding for the document
        docs_with_embeddings = self._generate_embeddings([doc])
        return docs_with_embeddings[0]
    
    def _generate_embeddings(self, documents: List[Document]) -> List[Document]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents: List of documents to generate embeddings for
            
        Returns:
            List of documents with embeddings
        """
        # Process documents in batches to avoid overwhelming the LLM service
        batch_size = 10
        processed_docs = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            texts = [self._preprocess_text_for_embedding(doc.content) for doc in batch]
            
            try:
                # 비동기 함수를 동기적으로 호출
                embeddings = self.llm_service.get_embeddings_sync(texts)
                
                for j, doc in enumerate(batch):
                    doc.embedding = embeddings[j]
                    processed_docs.append(doc)
                    
                logger.info(f"Generated embeddings for {len(batch)} documents")
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                # Add documents without embeddings
                processed_docs.extend(batch)
                logger.warning(f"Added {len(batch)} documents without embeddings")
        
        return processed_docs
    
    def chunk_document(self, document: Document) -> Tuple[Document, List[DocumentChunk]]:
        """
        Split a document into chunks if it's too large.
        
        Args:
            document: Document to split
            
        Returns:
            Tuple of (original document, list of document chunks)
        """
        # Check if document needs chunking (based on token count)
        token_count = self._get_token_length(document.content)
        if token_count <= 1000:  # If under 1000 tokens, no need to chunk
            return document, []
        
        # Split the document content into chunks
        chunks = self.text_splitter.split_text(document.content)
        logger.info(f"Split document {document.id} into {len(chunks)} chunks")
        
        # Create DocumentChunk objects
        doc_chunks = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document.id,
                content=chunk_content,
                chunk_index=i
            )
            doc_chunks.append(chunk)
        
        # Generate embeddings for chunks
        try:
            chunk_texts = [self._preprocess_text_for_embedding(chunk.content) for chunk in doc_chunks]
            embeddings = self.llm_service.get_embeddings_sync(chunk_texts)
            
            for i, chunk in enumerate(doc_chunks):
                chunk.embedding = embeddings[i]
                
            logger.info(f"Generated embeddings for {len(doc_chunks)} chunks")
        except Exception as e:
            logger.error(f"Error generating embeddings for chunks: {e}")
        
        return document, doc_chunks
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better indexing and searching.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple whitespace with a single space
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that aren't useful for searching
        text = re.sub(r'[^\w\s\.\,\-]', '', text)
        
        return text.strip()