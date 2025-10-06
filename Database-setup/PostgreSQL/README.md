# PostgreSQL - AI Learning Platform

This directory contains the PostgreSQL database setup for the AI learning platform. It stores **structured data** for user profiles, learning progress, quiz scores, and conversation logs.

## Directory Structure

```
PostgreSQL/
├── scripts/
│   ├── init_database.sql        # Database initialization script
│   └── setup_postgresql.py      # Verification script
│
└── README.md
```

---

## Database Schema

### 1. Users Table (Simplified)

Stores essential user information with conversation summaries.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | UUID | Primary key (auto-generated) |
| `email` | VARCHAR(255) | Unique email address |
| `role` | VARCHAR(100) | Job function (`Finance`, `Marketing`, `Product`, `Data Science`, `Engineering`, `Operations`, `Other`) |
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
  "short_term_summary": "Recently focused on ESG analysis prompts. Prefers financial use case examples.",
  "long_term_summary": "Advanced learner with strong analytical skills. Excels at applying AI to investment research."
}
```

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
| `interaction_log` | JSONB | Lightweight metadata (last prompts, preferences) |
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
  },
  "interaction_log": {
    "last_prompts": ["How do I create ESG analysis prompts?"],
    "recent_topics": ["use_cases", "finance"],
    "preferences": {"prefers_examples": true}
  }
}
```

**Auto-created:** A progress record is automatically created via trigger when a new user is inserted.

---

### 3. Interactions Table (Simplified)

Stores complete conversation logs between users and the AI tutor.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `interaction_id` | UUID | Primary key (auto-generated) |
| `user_id` | UUID | Foreign key to users |
| `log` | TEXT | Complete conversation text (both user and agent messages) |
| `timestamp` | TIMESTAMP | When the interaction occurred |

**Example Data:**
```sql
INSERT INTO interactions (user_id, log) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    E'User: How do I write better prompts for financial analysis?\n\nAssistant: For financial analysis prompts, follow these key principles:\n1. Provide company context\n2. Specify the type of analysis\n3. Define the output format\n\nFor example: "Analyze Tesla\'s Q3 2024 earnings report. Focus on revenue growth and profit margins. Provide a summary with bullet points."'
);
```

**Log Format:**
The `log` field contains the complete conversation in a simple text format:
```
User: [user's message]
