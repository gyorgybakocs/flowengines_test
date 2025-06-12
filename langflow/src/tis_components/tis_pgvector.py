"""
Tis PGVector Component - Custom PostgreSQL Vector Store for Langflow

A flexible PostgreSQL vector store that works with user-defined database schemas,
giving you full control over table names and structure.

Author: BGDS
Version: 1.0.0
"""

import psycopg2
import psycopg2.extras
from typing import List, Any
from langflow.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from langflow.io import HandleInput, IntInput, SecretStrInput, StrInput, DropdownInput
from langflow.schema import Data
from langflow.utils.connection_string_parser import transform_connection_string


class TisVectorStore:
    """Custom VectorStore implementation for PostgreSQL with flexible schema support"""

    def __init__(self, connection_string: str, documents_table: str, embeddings_table: str,
                 models_table: str, source_name: str, embedding_dimension: int, embedding_model):
        self.connection_string = connection_string
        self.documents_table = documents_table
        self.embeddings_table = embeddings_table
        self.models_table = models_table
        self.source_name = source_name
        self.embedding_dimension = embedding_dimension
        self.embedding_model = embedding_model
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Validate that all required tables exist and are accessible"""
        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()
        try:
            # Test table accessibility
            cursor.execute(f"SELECT 1 FROM {self.documents_table} LIMIT 1")
            cursor.execute(f"SELECT 1 FROM {self.embeddings_table} LIMIT 1")
            cursor.execute(f"SELECT 1 FROM {self.models_table} LIMIT 1")
        except psycopg2.Error as e:
            raise Exception(f"Schema validation failed. Tables not found: {self.documents_table}, "
                            f"{self.embeddings_table}, {self.models_table}. Error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def _ensure_model_exists(self, cursor) -> int:
        """Ensure embedding model exists and return its ID"""
        model_name = f"langflow-{self.embedding_dimension}d"

        # Try to find existing model
        cursor.execute(f"SELECT id FROM {self.models_table} WHERE name = %s", (model_name,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Create new model - try different schema variations
        try:
            # Full schema: name, dimension, notes
            cursor.execute(f"""
                INSERT INTO {self.models_table} (name, dimension, notes) 
                VALUES (%s, %s, %s) RETURNING id
            """, (model_name, self.embedding_dimension, f"Langflow {self.embedding_dimension}D embeddings"))
            return cursor.fetchone()[0]
        except psycopg2.Error:
            # Fallback: just name
            cursor.execute(f"""
                INSERT INTO {self.models_table} (name) VALUES (%s) RETURNING id
            """, (model_name,))
            return cursor.fetchone()[0]

    def _insert_document(self, cursor, document: Any) -> int:
        """Insert document with flexible schema support"""
        metadata = getattr(document, 'metadata', {}) or {}
        content = document.page_content

        # Try different schema variations
        try:
            # Full schema: source, content, metadata
            cursor.execute(f"""
                INSERT INTO {self.documents_table} (source, content, metadata) 
                VALUES (%s, %s, %s) RETURNING id
            """, (self.source_name, content, psycopg2.extras.Json(metadata)))
            return cursor.fetchone()[0]
        except psycopg2.Error:
            try:
                # Minimal schema: source, content
                cursor.execute(f"""
                    INSERT INTO {self.documents_table} (source, content) 
                    VALUES (%s, %s) RETURNING id
                """, (self.source_name, content))
                return cursor.fetchone()[0]
            except psycopg2.Error:
                # Most minimal: just content
                cursor.execute(f"""
                    INSERT INTO {self.documents_table} (content) VALUES (%s) RETURNING id
                """, (content,))
                return cursor.fetchone()[0]

    def _insert_embedding(self, cursor, document_id: int, model_id: int, embedding_vector: List[float]) -> None:
        """Insert embedding with flexible schema support"""
        try:
            # Full schema: document_id, model_id, embedding
            cursor.execute(f"""
                INSERT INTO {self.embeddings_table} (document_id, model_id, embedding) 
                VALUES (%s, %s, %s)
            """, (document_id, model_id, embedding_vector))
        except psycopg2.Error:
            # Fallback: document_id, embedding (no model_id)
            cursor.execute(f"""
                INSERT INTO {self.embeddings_table} (document_id, embedding) 
                VALUES (%s, %s)
            """, (document_id, embedding_vector))

    def add_documents(self, documents: List[Any]) -> List[str]:
        """Add documents to the vector store"""
        if not documents:
            return []

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()

        try:
            # Ensure model exists (within same transaction)
            model_id = self._ensure_model_exists(cursor)

            # Generate embeddings for all documents
            texts = [doc.page_content for doc in documents]
            embeddings_list = self.embedding_model.embed_documents(texts)

            document_ids = []

            # Process each document and embedding
            for doc, embedding_vector in zip(documents, embeddings_list):
                # Insert document
                document_id = self._insert_document(cursor, doc)
                document_ids.append(str(document_id))

                # Insert embedding
                self._insert_embedding(cursor, document_id, model_id, embedding_vector)

            conn.commit()
            return document_ids

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to add documents: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        if hasattr(self.embedding_model, 'embed_query'):
            return self.embedding_model.embed_query(query)
        else:
            return self.embedding_model.embed_documents([query])[0]

    def similarity_search(self, query: str, k: int = 4) -> List[Any]:
        """Search for similar documents using vector similarity"""
        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()

        try:
            # Check if we have any embeddings
            cursor.execute(f"SELECT COUNT(*) FROM {self.embeddings_table}")
            embedding_count = cursor.fetchone()[0]

            if embedding_count == 0:
                raise Exception(f"No embeddings found in {self.embeddings_table}")

            # Generate query embedding
            query_embedding = self._get_query_embedding(query)

            # Simple test: get ANY results regardless of distance
            cursor.execute(f"""
                SELECT d.content, d.metadata, e.embedding <=> %s as distance
                FROM {self.embeddings_table} e
                JOIN {self.documents_table} d ON e.document_id = d.id
                ORDER BY distance 
                LIMIT %s
            """, (query_embedding, k))

            rows = cursor.fetchall()

            if not rows:
                raise Exception(f"Query executed but returned 0 rows. Embeddings: {embedding_count}, Query dim: {len(query_embedding)}")

            results = []
            for row in rows:
                # Create LangChain-compatible document object
                class MockDocument:
                    def __init__(self, content: str, metadata: dict):
                        self.page_content = content
                        self.metadata = metadata or {}

                doc = MockDocument(row[0], row[1])
                results.append(doc)

            # Return results with debug info in first result
            if results:
                results[0].metadata['debug_info'] = f"Found {len(results)} results, distances: {[row[2] for row in rows]}"

            return results

        except Exception as e:
            # Re-raise to show in status
            raise Exception(f"Search debug: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def search(self, query: str, search_type: str = "similarity", k: int = 4, **kwargs) -> List[Any]:
        """LangChain-compatible search interface"""
        return self.similarity_search(query, k)


class TisPGVectorComponent(LCVectorStoreComponent):
    """
    Tis PGVector - Custom PostgreSQL Vector Store

    A flexible PostgreSQL vector store that respects your custom database schema.
    You control the table names and structure - no hardcoded assumptions.

    Features:
    • Custom table names (documents, embeddings, models)
    • Flexible schema detection and adaptation
    • Proper foreign key relationships
    • Vector similarity search with pgvector
    • LangChain compatible interface
    """

    display_name = "Tis PGVector"
    description = "Custom PostgreSQL Vector Store with flexible schema support"
    name = "tis_pgvector"
    icon = "database"

    inputs = [
        SecretStrInput(
            name="pg_server_url",
            display_name="PostgreSQL Connection String",
            required=True,
            info="Format: postgresql://user:password@host:port/database"
        ),
        StrInput(
            name="documents_table",
            display_name="Documents Table",
            value="documents",
            required=True,
            info="Table name for storing document content"
        ),
        StrInput(
            name="embeddings_table",
            display_name="Embeddings Table",
            value="embeddings_d384",
            required=True,
            info="Table name for storing vector embeddings"
        ),
        StrInput(
            name="models_table",
            display_name="Models Table",
            value="embedding_models",
            required=True,
            info="Table name for embedding model metadata"
        ),
        StrInput(
            name="source_name",
            display_name="Source Name",
            value="langflow",
            info="Identifier for this data source"
        ),
        IntInput(
            name="embedding_dimension",
            display_name="Embedding Dimension",
            value=384,
            info="Vector dimension (must match your embedding model)"
        ),
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            options=["similarity", "mmr"],
            value="similarity",
            advanced=True,
            info="Type of search to perform"
        ),
        *LCVectorStoreComponent.inputs,
        HandleInput(
            name="embedding",
            display_name="Embedding Model",
            input_types=["Embeddings"],
            required=True,
            info="Embedding model for generating vectors"
        ),
        IntInput(
            name="number_of_results",
            display_name="Search Results Count",
            value=4,
            advanced=True,
            info="Number of similar documents to return"
        ),
    ]

    def search_documents(self) -> List[Data]:
        """Override base class to provide better debugging and handle empty queries"""
        try:
            # Get vector store
            if self._cached_vector_store is not None:
                vector_store = self._cached_vector_store
            else:
                vector_store = self.build_vector_store()
                self._cached_vector_store = vector_store

            search_query: str = self.search_query or ""

            # If no search query, return all documents from database
            if not search_query.strip():
                return self._get_all_documents()

            # Perform similarity search
            docs = vector_store.similarity_search(search_query, k=self.number_of_results)

            # Convert to Data objects
            from langflow.helpers.data import docs_to_data
            data = docs_to_data(docs)
            self.status = f"Found {len(data)} results for query: '{search_query}'"
            return data

        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.status = error_msg
            return []

    def _get_all_documents(self) -> List[Data]:
        """Get all documents from database when no search query provided"""
        try:
            conn = psycopg2.connect(transform_connection_string(self.pg_server_url))
            cursor = conn.cursor()

            # Get all documents
            cursor.execute(f"SELECT content, metadata FROM {self.documents_table} LIMIT {self.number_of_results}")
            rows = cursor.fetchall()

            # Convert to Data objects
            data_objects = []
            for row in rows:
                content = row[0]
                metadata = row[1] if len(row) > 1 and row[1] else {}

                # Create Data object
                from langflow.schema import Data
                data_obj = Data(text=content, data={"content": content, "metadata": metadata})
                data_objects.append(data_obj)

            cursor.close()
            conn.close()

            self.status = f"Retrieved {len(data_objects)} documents (no search query provided)"
            return data_objects

        except Exception as e:
            error_msg = f"Failed to get all documents: {str(e)}"
            self.status = error_msg
            return []

    @check_cached_vector_store
    def build_vector_store(self) -> TisVectorStore:
        """Build the custom vector store"""
        try:
            # Prepare input data
            self.ingest_data = self._prepare_ingest_data()

            # Convert to LangChain documents
            documents = []
            for _input in self.ingest_data or []:
                if isinstance(_input, Data):
                    documents.append(_input.to_lc_document())
                else:
                    documents.append(_input)

            # Parse connection string
            connection_string = transform_connection_string(self.pg_server_url)

            # Create vector store with custom configuration
            vector_store = TisVectorStore(
                connection_string=connection_string,
                documents_table=self.documents_table,
                embeddings_table=self.embeddings_table,
                models_table=self.models_table,
                source_name=self.source_name,
                embedding_dimension=self.embedding_dimension,
                embedding_model=self.embedding
            )

            # Add documents if provided
            if documents:
                document_ids = vector_store.add_documents(documents)
                self.status = f"✅ Stored {len(document_ids)} documents in {self.documents_table}/{self.embeddings_table}"
            else:
                self.status = f"✅ Vector store ready: {self.documents_table}/{self.embeddings_table}"

            return vector_store

        except Exception as e:
            error_msg = f"❌ Vector store build failed: {str(e)}"
            self.status = error_msg
            raise Exception(error_msg)
