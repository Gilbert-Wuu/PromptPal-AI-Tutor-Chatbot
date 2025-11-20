-- Drop and recreate (only if you don't have important data)
DROP TABLE IF EXISTS sessions CASCADE;

-- Recreate with the correct schema
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
