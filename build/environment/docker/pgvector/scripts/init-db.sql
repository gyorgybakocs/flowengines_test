-- transaction
BEGIN;

-- Enable the 'vector' extension.
\echo '--- Initializing RAG database schema ---'
CREATE EXTENSION IF NOT EXISTS vector;

-- The central table for documents.
\echo '--> Creating central documents table (Single Source of Truth)...'
CREATE TABLE documents (id bigserial PRIMARY KEY, source TEXT NOT NULL, content TEXT NOT NULL, metadata JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
COMMENT ON TABLE documents IS 'Central storage for the knowledge base documents (Single Source of Truth).';

-- Registry for embedding models.
\echo '--> Creating embedding_models registry table...'
CREATE TABLE embedding_models (id serial PRIMARY KEY, name TEXT NOT NULL UNIQUE, dimension INTEGER NOT NULL, notes TEXT);
COMMENT ON TABLE embedding_models IS 'A registry of the embedding models used in the system.';

-- Vector tables, separated by dimension.
-- This way you can use multiple models with different capabilities at the same time.
\echo '--> Creating table for 384-dimension vectors...'
CREATE TABLE embeddings_d384 (id bigserial PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, model_id INTEGER NOT NULL REFERENCES embedding_models(id), embedding VECTOR(384) NOT NULL);
CREATE INDEX ON embeddings_d384 USING HNSW (embedding vector_cosine_ops);
COMMENT ON TABLE embeddings_d384 IS 'Storage for 384-dimension embeddings.';

\echo '--> Creating table for 1536-dimension vectors...'
CREATE TABLE embeddings_d1536 (id bigserial PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, model_id INTEGER NOT NULL REFERENCES embedding_models(id), embedding VECTOR(1536) NOT NULL);
CREATE INDEX ON embeddings_d1536 USING HNSW (embedding vector_cosine_ops);
COMMENT ON TABLE embeddings_d1536 IS 'Storage for 1536-dimension embeddings.';

-- Conversation memory tables (essential for Langflow).
\echo '--> Creating chat_sessions table for conversation memory...'
CREATE TABLE chat_sessions (id bigserial PRIMARY KEY, user_id TEXT, metadata JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
COMMENT ON TABLE chat_sessions IS 'Individual conversation flows (sessions).';

\echo '--> Creating chat_messages table...'
CREATE TABLE chat_messages (id bigserial PRIMARY KEY, session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE, is_from_user BOOLEAN NOT NULL, content TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
COMMENT ON TABLE chat_messages IS 'Messages belonging to a specific session.';

\echo '--- RAG database schema initialization complete. ---'
COMMIT;
