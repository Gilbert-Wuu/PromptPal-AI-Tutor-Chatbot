# PostgreSQL - AI Learning Platform

This directory contains the PostgreSQL database setup for the AI learning platform. It stores **structured data** for user profiles, learning progress, and quiz scores.

## Directory Structure

```
PostgreSQL/
├── scripts/
│   ├── init_database.sql        # Database initialization script
│   └── setup_postgresql.py      # Verifies schema and loads sample data
│
└── README.md
```

---

## Database Schema

### 1. Users Table

Stores user profiles and learning preferences with conversation summaries.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | UUID | Primary key (auto-generated) |
| `email` | VARCHAR(255) | Unique email address |
| `role` | VARCHAR(100) | Job function (`Finance`, `Marketing`, `Product`, `Data Science`, `Engineering`, `Operations`, `Other`) |
| `proficiency` | VARCHAR(20) | AI skill level (`Beginner`, `Intermediate`, `Advanced`) |
| `learning_goals` | JSONB | Array of learning objectives |
| `learning_style` | VARCHAR(50) | Preferred learning method (`visual`, `hands-on`, `reading`, `interactive`, `mixed`) |
| `time_commitment` | VARCHAR(20) | Weekly study time (`1-2 hours/week`, `3-5 hours/week`, `5+ hours/week`) |
| `short_term_summary` | TEXT | Recent conversation context (last 3-5 sessions) |
| `long_term_summary` | TEXT | Persistent learning patterns and key milestones |
| `created_at` | TIMESTAMP | Account creation timestamp |
| `updated_at` | TIMESTAMP | Last profile update |

**Example Data:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "frank.amato@federatedhermes.com",
  "role": "Data Science",
  "proficiency": "Advanced",
  "learning_goals": ["prompt_engineering", "use_cases", "ai_strategy"],
  "learning_style": "hands-on",
  "time_commitment": "3-5 hours/week",
  "short_term_summary": "Recently focused on ESG analysis prompts. Prefers financial use case examples.",
  "long_term_summary": "Advanced learner with strong analytical skills. Excels at applying AI to investment research."
}
```

**Constraints:**
- Email format validation via regex
- Role must be one of predefined values
- Proficiency must be Beginner/Intermediate/Advanced

---

### 2. Progress Table

Tracks user learning progress, completed modules, and quiz performance.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `progress_id` | UUID | Primary key (auto-generated) |
| `user_id` | UUID | Foreign key to users (unique, one-to-one) |
| `completed_modules` | JSONB | Array of completed module IDs |
| `quiz_scores` | JSONB | Object mapping module IDs to scores |
| `last_login` | TIMESTAMP | Most recent activity |

**Example Data:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "completed_modules": ["ai_basics_101", "prompt_fundamentals", "advanced_prompting"],
  "quiz_scores": {
    "ai_basics_101": 88,
    "prompt_fundamentals": 92,
    "advanced_prompting": 85
  }
}
```

**Auto-created:** A progress record is automatically created via trigger when a new user is inserted.

---

## User Summary Columns

### short_term_summary
Recent conversation context (rolling window of last 3-5 sessions).

**Contains:**
- Current learning focus areas
- Recent struggles or confusion points
- Immediate preferences or patterns
- Temporary learning state

**Update frequency:** After each session

**Example:**
```
"Recently focused on prompt engineering for ESG analysis. Struggled with 
structuring complex multi-step prompts. Prefers seeing financial industry 
examples. Last 3 sessions covered advanced prompting techniques."
```

### long_term_summary
Persistent learning profile and patterns over time.

**Contains:**
- Overall strengths and weaknesses
- Consistent learning patterns
- Key milestones achieved
- Learning style observations

**Update frequency:** Weekly or after significant milestones

**Example:**
```
"Advanced learner with strong technical background in data science. 
Excels at understanding complex AI concepts quickly. Consistently 
achieves high quiz scores (avg 90+). Primary interest: applying AI 
to investment research and risk analysis. Learning style: hands-on 
with real-world examples."
```

**Purpose:**
These summaries enable the AI tutor to maintain conversation context and provide personalized responses without storing full conversation history in PostgreSQL. Full conversation logs are stored in Weaviate's `InteractionLog` collection.

---

## Setup Instructions

### Prerequisites

```bash
# Install dependencies
pip install asyncpg python-dotenv

# Create .env file in root DB_Setup directory with:
POSTGRES_USER=ai_tutor_admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=ai_tutor_db
```

### Step 1: Start PostgreSQL

```bash
# From DB_Setup directory
docker-compose up -d postgres
```

**Verify running:**
```bash
docker ps | grep postgres
```

### Step 2: Initialize Database

The `init_database.sql` script runs automatically on first container start. It creates:
- Tables with constraints
- Indexes for performance (including full-text search on summaries)
- Helper functions
- Triggers for auto-updates
- Summary views
- Sample data

### Step 3: Verify Setup

```bash
cd PostgreSQL
python scripts/setup_postgresql.py
```

**Output:**
```
✓ Successfully connected to PostgreSQL
✓ Found 2 tables: users, progress
✓ Users table has 11 columns
✓ Found 8 indexes
✓ Found 7 helper functions
✓ Found 3 sample users
```

---

## Helper Functions

### add_completed_module(user_id, module_id)
Safely adds a module to completed list (prevents duplicates).

```sql
SELECT add_completed_module(
    '550e8400-e29b-41d4-a716-446655440000',
    'prompt_fundamentals'
);
```

### update_quiz_score(user_id, module_id, score)
Updates or inserts quiz score for a module.

```sql
SELECT update_quiz_score(
    '550e8400-e29b-41d4-a716-446655440000',
    'ai_basics_101',
    88
);
```

### log_user_interaction(user_id, interaction_data)
Appends interaction metadata to progress log.

```sql
SELECT log_user_interaction(
    '550e8400-e29b-41d4-a716-446655440000',
    '{"action": "completed_exercise", "timestamp": "2025-09-29T10:30:00Z"}'::jsonb
);
```

### update_short_term_summary(user_id, summary)
Updates the user's short-term memory summary.

```sql
SELECT update_short_term_summary(
    '550e8400-e29b-41d4-a716-446655440000',
    'User recently struggled with prompt structure. Prefers financial examples.'
);
```

### update_long_term_summary(user_id, summary)
Updates the user's long-term learning profile.

```sql
SELECT update_long_term_summary(
    '550e8400-e29b-41d4-a716-446655440000',
    'Advanced learner. Excels at technical concepts. Primary focus: investment AI.'
);
```

### get_user_context(user_id)
Retrieves comprehensive user context including summaries and progress.

```sql
SELECT * FROM get_user_context('550e8400-e29b-41d4-a716-446655440000');
```

**Returns:**
- user_id, email, role, proficiency
- short_term_summary, long_term_summary
- learning_goals, learning_style
- completed_modules, avg_quiz_score

---

## Query Examples

### Get User Profile with Progress

```sql
SELECT * FROM user_profile_summary 
WHERE email = 'frank.amato@federatedhermes.com';
```

### Find Users by Learning Goal

```sql
SELECT email, role, proficiency, short_term_summary
FROM users
WHERE learning_goals @> '["prompt_engineering"]'::jsonb;
```

### Search Users by Summary Content

```sql
-- Find users struggling with specific topics
SELECT email, role, short_term_summary
FROM users
WHERE to_tsvector('english', short_term_summary) @@ plainto_tsquery('english', 'prompt structure');
```

### Get Average Quiz Performance by Role

```sql
SELECT 
    u.role,
    AVG((SELECT AVG((value::text)::int) FROM jsonb_each(p.quiz_scores))) as avg_score,
    COUNT(*) as user_count
FROM users u
JOIN progress p ON u.user_id = p.user_id
WHERE jsonb_typeof(p.quiz_scores) = 'object'
GROUP BY u.role
ORDER BY avg_score DESC;
```

### Check Module Completion Rate

```sql
SELECT 
    jsonb_array_elements_text(completed_modules) as module,
    COUNT(*) as users_completed
FROM progress
GROUP BY module
ORDER BY users_completed DESC;
```

### Find High Performers

```sql
SELECT 
    u.email,
    u.role,
    u.proficiency,
    ROUND((SELECT AVG((value::text)::numeric) FROM jsonb_each(p.quiz_scores)), 2) as avg_score,
    u.long_term_summary
FROM users u
JOIN progress p ON u.user_id = p.user_id
WHERE (SELECT AVG((value::text)::numeric) FROM jsonb_each(p.quiz_scores)) > 85
ORDER BY avg_score DESC;
```

---

## Triggers

### Auto-Update Timestamp
When a user record is updated, `updated_at` automatically refreshes to `CURRENT_TIMESTAMP`.

### Auto-Create Progress
When a new user is inserted, a corresponding progress record is automatically created with default empty values.

---

## Indexes

**Standard B-tree indexes:**
- `idx_users_email` - Fast email lookups for authentication
- `idx_users_proficiency` - Filter by skill level
- `idx_users_role` - Filter by job function
- `idx_progress_last_login` - Track user activity

**GIN indexes (JSONB):**
- `idx_users_learning_goals_gin` - Query learning goals arrays
- `idx_progress_completed_modules_gin` - Search completed modules
- `idx_progress_quiz_scores_gin` - Query quiz scores

**Full-text search indexes:**
- `idx_users_short_term_summary_fts` - Search short-term summaries
- `idx_users_long_term_summary_fts` - Search long-term summaries

**Performance:** GIN indexes enable efficient `@>` (contains) and `?` (exists) operators on JSONB fields. Full-text search indexes enable semantic search within user summaries.

---

## Integration with Vector DB

### Data Separation

**PostgreSQL (Structured Data):**
- User profiles and authentication
- Learning progress and quiz scores
- Module completion tracking
- Short-term and long-term summaries (compressed context)
- Lightweight interaction metadata

**Weaviate (Vector Data):**
- Educational content (concepts, use cases)
- Full conversation history (semantic search)
- User-specific memory with isolation
- Context retrieval for personalization
- Vector embeddings for similarity search

### Backend Integration Pattern

```python
import asyncpg
import weaviate

# 1. Get user profile with summaries from PostgreSQL
user_context = await pg_conn.fetchrow(
    "SELECT * FROM get_user_context($1)",
    user_id
)

# 2. Use summaries for quick context
short_term = user_context['short_term_summary']
long_term = user_context['long_term_summary']

# 3. Retrieve relevant content from Weaviate
content = weaviate_client.query.get("CoreConcept") \
    .with_near_text({"concepts": [user_query]}) \
    .with_where({
        "path": ["role"], 
        "operator": "Equal", 
        "valueText": user_context["role"]
    }) \
    .do()

# 4. Generate personalized response using both sources
response = generate_response(
    user_query=user_query,
    content=content,
    short_term_context=short_term,
    long_term_context=long_term
)

# 5. Update PostgreSQL progress
await pg_conn.execute(
    "SELECT add_completed_module($1, $2)",
    user_id, module_id
)

# 6. Update short-term summary (after each session)
new_summary = await generate_short_term_summary(recent_interactions)
await pg_conn.execute(
    "SELECT update_short_term_summary($1, $2)",
    user_id, new_summary
)

# 7. Log full interaction to Weaviate
weaviate_client.data_object.create({
    "user_id": user_id,
    "conversation_text": user_query + response,
    "timestamp": datetime.now()
}, "InteractionLog")
```

### Summary Update Strategy

**Short-term summary (Rolling Window):**
- Update: After each learning session
- Method: Summarize last 3-5 interactions using LLM
- Keep: Recent struggles, preferences, immediate context
- Discard: Old information as it's moved to long-term

**Long-term summary (Persistent Profile):**
- Update: Weekly or after major milestones
- Method: Analyze all historical data periodically
- Keep: Consistent patterns, key achievements, learning style
- Accumulate: Build comprehensive learning profile over time

---

## Security Notes

**Row Level Security (RLS):**
Not currently enabled. For production deployment:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_data_isolation ON users
    FOR ALL TO application_role
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY progress_data_isolation ON progress
    FOR ALL TO application_role
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

**Connection Security:**
- Use SSL/TLS for production connections
- Restrict database access to application servers only
- Rotate passwords regularly
- Never commit credentials to version control
- Use connection pooling for better performance

---

## Maintenance

### Backup Database

```bash
docker exec ai_tutor_postgres pg_dump -U ai_tutor_admin ai_tutor_db > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
docker exec -i ai_tutor_postgres psql -U ai_tutor_admin ai_tutor_db < backup_20250929.sql
```

### Monitor Database Size

```sql
SELECT 
    pg_size_pretty(pg_database_size('ai_tutor_db')) as database_size,
    pg_size_pretty(pg_total_relation_size('users')) as users_table_size,
    pg_size_pretty(pg_total_relation_size('progress')) as progress_table_size;
```

### Clean Old Data

```sql
-- Archive inactive users (optional)
DELETE FROM users 
WHERE user_id IN (
    SELECT user_id FROM progress 
    WHERE last_login < NOW() - INTERVAL '1 year'
);

-- Vacuum and analyze
VACUUM ANALYZE users;
VACUUM ANALYZE progress;
```

### Update Summary Columns for Existing Users

If you're migrating from an older schema without summary columns:

```bash
psql -h localhost -U ai_tutor_admin -d ai_tutor_db -f scripts/add_summary_columns.sql
```

---

## Future Enhancements

- [ ] Add session tracking table for detailed activity logs
- [ ] Implement learning path recommendations table
- [ ] Create analytics views for admin dashboard
- [ ] Add module catalog table with prerequisites
- [ ] Implement badge/achievement system
- [ ] Add audit logging for compliance
- [ ] Implement multi-tenancy for different organizations

---

## Connection Examples

### Python (asyncpg)

```python
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def connect_db():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "ai_tutor_db"),
        user=os.getenv("POSTGRES_USER", "ai_tutor_admin"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    # Get user with summaries
    user = await conn.fetchrow(
        "SELECT * FROM get_user_context($1)",
        user_id
    )
    
    await conn.close()
    return user
```

### Python (psycopg2)

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    database=os.getenv("POSTGRES_DB", "ai_tutor_db"),
    user=os.getenv("POSTGRES_USER", "ai_tutor_admin"),
    password=os.getenv("POSTGRES_PASSWORD")
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM user_profile_summary WHERE email = %s", 
               ("frank.amato@federatedhermes.com",))
user = cursor.fetchone()
```

---

## Support

For issues:
1. Check PostgreSQL logs: `docker-compose logs -f postgres`
2. Verify connection: `psql -h localhost -U ai_tutor_admin -d ai_tutor_db`
3. Check table structure: `\dt` and `\d users`
4. View function definitions: `\df`

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [JSONB Performance Tips](https://www.postgresql.org/docs/current/datatype-json.html)
- [Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- Project Documentation: `/docs/database-schema.md`
