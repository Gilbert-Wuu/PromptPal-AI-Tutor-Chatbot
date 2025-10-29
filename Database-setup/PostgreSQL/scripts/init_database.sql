-- ============================================
-- AI Tutor Database Initialization Script
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE (SIMPLIFIED)
-- ============================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL,
    long_term_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_long_term_summary_fts ON users USING gin(to_tsvector('english', COALESCE(long_term_summary, '')));

-- Comments
COMMENT ON COLUMN users.long_term_summary IS 'Persistent learning patterns, strengths, weaknesses, and key milestones';

-- ============================================
-- PROGRESS TABLE
-- ============================================
CREATE TABLE progress (
    progress_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    completed_modules JSONB DEFAULT '[]'::jsonb,
    quiz_scores JSONB DEFAULT '{}'::jsonb,
    interaction_log JSONB DEFAULT '{}'::jsonb,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_progress_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_progress_user_id ON progress(user_id);
CREATE INDEX idx_progress_last_login ON progress(last_login);
CREATE INDEX idx_progress_completed_modules_gin ON progress USING gin(completed_modules);
CREATE INDEX idx_progress_quiz_scores_gin ON progress USING gin(quiz_scores);
CREATE INDEX idx_progress_interaction_log_gin ON progress USING gin(interaction_log);

-- ============================================
-- INTERACTIONS TABLE
-- ============================================
CREATE TABLE interactions (
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    log TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for interactions
CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
CREATE INDEX idx_interactions_log_fts ON interactions USING gin(to_tsvector('english', log));

-- Comment
COMMENT ON TABLE interactions IS 'Stores complete conversation logs between user and AI tutor';
COMMENT ON COLUMN interactions.log IS 'Full conversation text including both user messages and agent responses';

-- ============================================
-- TRIGGERS
-- ============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-create progress record for new users
CREATE OR REPLACE FUNCTION create_initial_progress()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO progress (user_id, completed_modules, quiz_scores, interaction_log)
    VALUES (
        NEW.user_id,
        '[]'::jsonb,
        '{}'::jsonb,
        '{
            "last_prompts": [],
            "recent_topics": [],
            "preferences": {}
        }'::jsonb
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_user_progress
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_initial_progress();

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Add completed module
CREATE OR REPLACE FUNCTION add_completed_module(
    p_user_id UUID,
    p_module_id TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE progress
    SET completed_modules = 
        CASE 
            WHEN completed_modules @> to_jsonb(p_module_id)
            THEN completed_modules
            ELSE completed_modules || to_jsonb(p_module_id)
        END,
        last_login = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Update quiz score
CREATE OR REPLACE FUNCTION update_quiz_score(
    p_user_id UUID,
    p_module_id TEXT,
    p_score INTEGER
)
RETURNS VOID AS $$
BEGIN
    UPDATE progress
    SET quiz_scores = jsonb_set(
            quiz_scores,
            ARRAY[p_module_id],
            to_jsonb(p_score),
            true
        ),
        last_login = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Log interaction metadata
CREATE OR REPLACE FUNCTION log_user_interaction(
    p_user_id UUID,
    p_interaction_data JSONB
)
RETURNS VOID AS $$
BEGIN
    UPDATE progress
    SET interaction_log = interaction_log || p_interaction_data,
        last_login = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;


-- Update long-term summary
CREATE OR REPLACE FUNCTION update_long_term_summary(
    p_user_id UUID,
    p_summary TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET long_term_summary = p_summary,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Log conversation interaction
CREATE OR REPLACE FUNCTION log_conversation(
    p_user_id UUID,
    p_log TEXT
)
RETURNS UUID AS $$
DECLARE
    v_interaction_id UUID;
BEGIN
    INSERT INTO interactions (user_id, log)
    VALUES (p_user_id, p_log)
    RETURNING interaction_id INTO v_interaction_id;  -- Fixed: correct column name and INTO clause

    RETURN v_interaction_id;
END;
$$ LANGUAGE plpgsql;
