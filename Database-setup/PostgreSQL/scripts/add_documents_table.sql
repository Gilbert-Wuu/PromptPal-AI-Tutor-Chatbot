-- ============================================
-- User Documents Table
-- Stores metadata for uploaded documents
-- ============================================

CREATE TABLE IF NOT EXISTS user_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    weaviate_doc_id VARCHAR(255),
    chunk_count INTEGER DEFAULT 0,
    
    CONSTRAINT chk_status CHECK (status IN ('active', 'processing', 'deleted', 'error'))
);

-- Indexes for efficient queries
CREATE INDEX idx_user_documents_user_id ON user_documents(user_id);
CREATE INDEX idx_user_documents_status ON user_documents(status);
CREATE INDEX idx_user_documents_upload_date ON user_documents(upload_date DESC);

-- Comments
COMMENT ON TABLE user_documents IS 'Stores metadata for user-uploaded documents';
COMMENT ON COLUMN user_documents.weaviate_doc_id IS 'Reference to document chunks in Weaviate';
COMMENT ON COLUMN user_documents.chunk_count IS 'Number of chunks this document was split into';

