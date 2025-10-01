-- ============================================
-- AI Tutor Database Initialization Script
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL,
    proficiency VARCHAR(20) NOT NULL DEFAULT 'Beginner',
    learning_goals JSONB DEFAULT '[]'::jsonb,
    learning_style VARCHAR(50),
    time_commitment VARCHAR(20),
    short_term_summary TEXT,
    long_term_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_proficiency CHECK (proficiency IN ('Beginner', 'Intermediate', 'Advanced')),
    CONSTRAINT chk_role CHECK (role IN ('Finance', 'Marketing', 'Product', 'Data Science', 'Engineering', 'Operations', 'Other')),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_learning_style CHECK (learning_style IS NULL OR learning_style IN ('visual', 'hands-on', 'reading', 'interactive', 'mixed')),
    CONSTRAINT chk_time_commitment CHECK (time_commitment IS NULL OR time_commitment IN ('1-2 hours/week', '3-5 hours/week', '5+ hours/week'))
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_proficiency ON users(proficiency);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_learning_goals_gin ON users USING gin(learning_goals);
CREATE INDEX idx_users_short_term_summary_fts ON users USING gin(to_tsvector('english', COALESCE(short_term_summary, '')));
CREATE INDEX idx_users_long_term_summary_fts ON users USING gin(to_tsvector('english', COALESCE(long_term_summary, '')));

-- Comments
COMMENT ON COLUMN users.short_term_summary IS 'Recent conversation context and immediate learning state (rolling window of last few sessions)';
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

-- Log interaction
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

-- Update short-term summary
CREATE OR REPLACE FUNCTION update_short_term_summary(
    p_user_id UUID,
    p_summary TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET short_term_summary = p_summary,
        updated_at = CURRENT_TIMESTAMP
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

-- Get combined user context
CREATE OR REPLACE FUNCTION get_user_context(p_user_id UUID)
RETURNS TABLE (
    user_id UUID,
    email VARCHAR,
    role VARCHAR,
    proficiency VARCHAR,
    short_term_summary TEXT,
    long_term_summary TEXT,
    learning_goals JSONB,
    learning_style VARCHAR,
    completed_modules JSONB,
    avg_quiz_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.user_id,
        u.email,
        u.role,
        u.proficiency,
        u.short_term_summary,
        u.long_term_summary,
        u.learning_goals,
        u.learning_style,
        p.completed_modules,
        (SELECT AVG((value::text)::int) FROM jsonb_each(p.quiz_scores)) as avg_quiz_score
    FROM users u
    LEFT JOIN progress p ON u.user_id = p.user_id
    WHERE u.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS
-- ============================================

CREATE OR REPLACE VIEW user_profile_summary AS
SELECT 
    u.user_id,
    u.email,
    u.role,
    u.proficiency,
    u.learning_goals,
    u.learning_style,
    u.time_commitment,
    u.short_term_summary,
    u.long_term_summary,
    jsonb_array_length(p.completed_modules) as modules_completed,
    (SELECT COUNT(*) FROM jsonb_object_keys(p.quiz_scores)) as quizzes_taken,
    (SELECT AVG((value::text)::int) FROM jsonb_each(p.quiz_scores)) as avg_quiz_score,
    p.last_login,
    u.created_at
FROM users u
LEFT JOIN progress p ON u.user_id = p.user_id;

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Insert sample users
INSERT INTO users (email, role, proficiency, learning_goals, learning_style, time_commitment, short_term_summary, long_term_summary)
VALUES 
    (
        'frank.amato@federatedhermes.com', 
        'Data Science', 
        'Advanced', 
        '["prompt_engineering", "use_cases", "ai_strategy"]'::jsonb, 
        'hands-on', 
        '3-5 hours/week',
        'Recently focused on ESG analysis prompts. Prefers financial use case examples. Last 3 sessions covered advanced prompting techniques.',
        'Advanced learner with strong analytical skills. Excels at applying AI to investment research. Consistently achieves high quiz scores (avg 90+). Primary focus: integrating AI into financial analysis workflows.'
    ),
    (
        'jonah.woods@federatedhermes.com', 
        'Data Science', 
        'Advanced',
        '["advanced_prompting", "model_evaluation", "ethics"]'::jsonb, 
        'interactive', 
        '5+ hours/week',
        'Currently exploring model evaluation techniques. Shows strong interest in AI ethics and responsible use. Active learner with frequent questions.',
        'Highly technical learner with deep understanding of AI concepts. Background in data science enables quick grasp of complex topics. Interested in both technical implementation and ethical implications.'
    ),
    (
        'analyst1@federatedhermes.com', 
        'Finance', 
        'Beginner',
        '["ai_basics", "prompt_engineering", "investment_use_cases"]'::jsonb, 
        'visual', 
        '1-2 hours/week',
        'New to AI concepts. Struggles with technical terminology but motivated to learn. Prefers step-by-step examples with visual aids.',
        'Beginner learner building foundational knowledge. Financial analyst background helps with business context but needs support on technical concepts. Learning style: visual and example-driven.'
    );

-- Update progress for sample users
DO $$
DECLARE
    v_user_id UUID;
BEGIN
    -- Frank Amato progress
    SELECT user_id INTO v_user_id FROM users WHERE email = 'frank.amato@federatedhermes.com';
    PERFORM add_completed_module(v_user_id, 'ai_basics_101');
    PERFORM add_completed_module(v_user_id, 'prompt_fundamentals');
    PERFORM add_completed_module(v_user_id, 'advanced_prompting');
    PERFORM add_completed_module(v_user_id, 'use_case_finance');
    PERFORM update_quiz_score(v_user_id, 'ai_basics_101', 88);
    PERFORM update_quiz_score(v_user_id, 'prompt_fundamentals', 92);
    PERFORM update_quiz_score(v_user_id, 'advanced_prompting', 85);
    PERFORM update_quiz_score(v_user_id, 'use_case_finance', 90);
    
    -- Jonah Woods progress
    SELECT user_id INTO v_user_id FROM users WHERE email = 'jonah.woods@federatedhermes.com';
    PERFORM add_completed_module(v_user_id, 'ai_basics_101');
    PERFORM add_completed_module(v_user_id, 'prompt_fundamentals');
    PERFORM add_completed_module(v_user_id, 'advanced_prompting');
    PERFORM add_completed_module(v_user_id, 'model_evaluation');
    PERFORM add_completed_module(v_user_id, 'ethics_ai');
    PERFORM update_quiz_score(v_user_id, 'ai_basics_101', 95);
    PERFORM update_quiz_score(v_user_id, 'prompt_fundamentals', 98);
    PERFORM update_quiz_score(v_user_id, 'advanced_prompting', 94);
    PERFORM update_quiz_score(v_user_id, 'model_evaluation', 91);
    PERFORM update_quiz_score(v_user_id, 'ethics_ai', 89);
    
    -- Finance Analyst progress
    SELECT user_id INTO v_user_id FROM users WHERE email = 'analyst1@federatedhermes.com';
    PERFORM add_completed_module(v_user_id, 'ai_basics_101');
    PERFORM add_completed_module(v_user_id, 'prompt_fundamentals');
    PERFORM update_quiz_score(v_user_id, 'ai_basics_101', 78);
    PERFORM update_quiz_score(v_user_id, 'prompt_fundamentals', 72);
END $$;
