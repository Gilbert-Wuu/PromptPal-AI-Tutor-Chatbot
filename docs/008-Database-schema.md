# AI Tutor Database Schema - Aligned with Requirements

*Database design for Federated Hermes AI Education Platform with user memory isolation*

## Entity Relationship Summary

| Entity | Primary Key | Purpose | Key Relationships |
|--------|-------------|---------|-------------------|
| `users` | user_id | Core user profiles with learning preferences | → progress, conversation_memory |
| `progress` | progress_id | User learning progress and activity tracking | ← users |
| `conversation_memory` | memory_id | User-specific conversation history (isolated) | ← users |
| `knowledge_chunks` | chunk_id | Educational content (shared via Weaviate) | Referenced via vector search |

## Core Database Schema

### 1. Users Table

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) NOT NULL, -- Job function at Federated Hermes
    proficiency VARCHAR(20) CHECK (proficiency IN ('Beginner', 'Intermediate', 'Advanced')) DEFAULT 'Beginner',
    learning_goals JSONB, -- Array of selected goals: ["prompt_engineering", "use_cases", "ethics"]
    learning_style VARCHAR(50), -- "visual", "hands-on", "reading", "interactive"
    time_commitment VARCHAR(20), -- "1-2 hours/week", "3-5 hours/week", "5+ hours/week"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_proficiency ON users(proficiency);
CREATE INDEX idx_users_role ON users(role);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 2. Progress Table

```sql
CREATE TABLE progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    completed_modules JSONB DEFAULT '[]'::jsonb, -- ["module_1", "prompt_basics", "use_case_finance"]
    quiz_scores JSONB DEFAULT '{}'::jsonb, -- {"prompt_basics": 85, "ethics_101": 92}
    interaction_log JSONB DEFAULT '{}'::jsonb, -- {"last_prompts": [], "recent_topics": [], "preferences": {}}
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id) -- One progress record per user
);

CREATE INDEX idx_progress_user_id ON progress(user_id);
CREATE INDEX idx_progress_last_login ON progress(last_login);

-- GIN indexes for JSONB fields to enable efficient querying
CREATE INDEX idx_progress_completed_modules_gin ON progress USING gin(completed_modules);
CREATE INDEX idx_progress_quiz_scores_gin ON progress USING gin(quiz_scores);
```

### 3. Conversation Memory Table (User-Isolated)

```sql
CREATE TABLE conversation_memory (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    memory_content TEXT NOT NULL,
    memory_type ENUM('user_question', 'ai_response', 'learning_insight', 'preference') NOT NULL,
    topic VARCHAR(100), -- "use_cases", "prompt_engineering", "ethics", etc.
    difficulty VARCHAR(20), -- "beginner", "intermediate", "advanced"
    context_metadata JSONB DEFAULT '{}'::jsonb, -- Additional context like session info, tags
    weaviate_id VARCHAR(100), -- Reference to Weaviate UserMemory object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score DECIMAL(3,2) DEFAULT 0.50 CHECK (importance_score >= 0 AND importance_score <= 1)
);

CREATE INDEX idx_conversation_memory_user_id ON conversation_memory(user_id);
CREATE INDEX idx_conversation_memory_topic ON conversation_memory(topic);
CREATE INDEX idx_conversation_memory_type ON conversation_memory(memory_type);
CREATE INDEX idx_conversation_memory_weaviate_id ON conversation_memory(weaviate_id);

-- Row Level Security for strict user isolation
ALTER TABLE conversation_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_memory_isolation ON conversation_memory
    FOR ALL TO application_role
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

## Weaviate Schema Configuration

### 1. Shared Knowledge Collection

```python
# Educational content accessible to all users with filtering
shared_knowledge_schema = {
    "class": "KnowledgeChunk",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-3-small",
            "dimensions": 1536
        }
    },
    "properties": [
        {
            "name": "content_id",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "title",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "content",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "topic",
            "dataType": ["text"],
            "indexInverted": True  # "use_cases", "prompt_engineering", "ethics"
        },
        {
            "name": "difficulty",
            "dataType": ["text"],
            "indexInverted": True  # "beginner", "intermediate", "advanced"
        },
        {
            "name": "role",
            "dataType": ["text"],
            "indexInverted": True  # "finance", "operations", "research", "general"
        },
        {
            "name": "content_type",
            "dataType": ["text"],
            "indexInverted": True  # "concept", "example", "exercise", "case_study"
        },
        {
            "name": "tags",
            "dataType": ["text[]"]
        }
    ]
}
```

### 2. User Memory Collection (Isolated)

```python
# Personal conversation memory with strict user isolation
user_memory_schema = {
    "class": "UserMemory",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-3-small",
            "dimensions": 1536
        }
    },
    "properties": [
        {
            "name": "memory_id",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "user_id",
            "dataType": ["text"],
            "indexInverted": True  # CRITICAL for user isolation
        },
        {
            "name": "memory_content",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "topic",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "difficulty",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "role",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "memory_type",
            "dataType": ["text"],
            "indexInverted": True
        },
        {
            "name": "importance_score",
            "dataType": ["number"]
        },
        {
            "name": "created_at",
            "dataType": ["date"]
        }
    ]
}
```

## Example Weaviate Metadata Structure

### Shared Knowledge Entry
```json
{
    "content_id": "prompt_eng_001",
    "title": "Basic Prompt Structure for Financial Analysis",
    "content": "A good financial analysis prompt has three parts: context about the company, specific analysis request, and desired output format...",
    "topic": "use_cases",
    "difficulty": "beginner",
    "role": "finance",
    "content_type": "example",
    "tags": ["prompt_engineering", "financial_analysis", "structure"]
}
```

### User Memory Entry
```json
{
    "memory_id": "mem_789",
    "user_id": "user_1234",
    "memory_content": "I struggled with creating prompts for ESG analysis. Need more examples of how to structure questions about sustainability metrics.",
    "topic": "use_cases",
    "difficulty": "beginner",
    "role": "finance",
    "memory_type": "learning_insight",
    "importance_score": 0.85,
    "created_at": "2025-09-22T10:30:00Z"
}
```



## Sample Queries

### Get User Profile with Progress
```sql
SELECT 
    u.user_id,
    u.email,
    u.role,
    u.proficiency,
    u.learning_goals,
    u.learning_style,
    u.time_commitment,
    p.completed_modules,
    p.quiz_scores,
    p.last_login
FROM users u
LEFT JOIN progress p ON u.user_id = p.user_id
WHERE u.user_id = $1;
```

### Update Learning Goals
```sql
UPDATE users 
SET learning_goals = $2,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = $1;
```

### Get Quiz Performance Summary
```sql
SELECT 
    user_id,
    jsonb_object_keys(quiz_scores) as module,
    (quiz_scores ->> jsonb_object_keys(quiz_scores))::int as score
FROM progress 
WHERE user_id = $1 
AND quiz_scores IS NOT NULL;
```

This simplified schema aligns with your requirements while maintaining the essential user memory isolation and personalization features needed for the AI education platform.
