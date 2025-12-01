# Vector DB - AI Learning Platform

This directory contains the vector database setup and data for the AI learning platform. It uses **Weaviate** as the vector database with **OpenAI embeddings** for semantic search capabilities.

## Directory Structure

```
Vector_DB/
├── data/
│   ├── ai_concepts.csv          # Core AI concepts and learning content
│   └── use_case.csv             # Practical use cases and exercises
│
├── scripts/
│   ├── setup_weaviate.py        # Creates Weaviate collections (run once)
│   ├── load_data.py             # Loads CSV data into Weaviate
│   └── config.py                # Configuration file (optional)
│
└── README.md                    # Weaviate-specific documentation
```

---

## Weaviate Collections

### 1. CoreConcept Collection

Stores foundational AI concepts for teaching purposes.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `content_id` | text | Unique identifier (e.g., `concept_001`) |
| `title` | text | Concept title |
| `content` | text | Detailed explanation of the concept |
| `topic` | text | Category (`prompt_engineering`, `foundational`, `ethics`) |
| `role` | text | Target role (`general`, `finance`) |
| `content_type` | text | Type of content (`concept`, `example`) |
| `tags` | text[] | Searchable keywords |

**Example Data:**
```json
{
  "content_id": "concept_003",
  "title": "Prompt Engineering Basics",
  "content": "A good prompt has four parts: Role, Context, Task, and Format...",
  "topic": "prompt_engineering",
  "role": "general",
  "content_type": "concept",
  "tags": ["prompts", "basics", "structure"]
}
```

---

### 2. UseCase Collection

Stores practical use cases that serve as exercises for users to practice learned concepts.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `content_id` | text | Unique identifier (e.g., `uc_001`) |
| `title` | text | Use case title |
| `application` | text | Detailed application scenario |
| `ai_concepts` | text | AI concepts involved |
| `business_value` | text | Business benefits |
| `data_sources` | text | Required data sources |
| `role` | text | Target role (`finance`, `general`) |
| `content_type` | text | Type (`case_study`, `example`) |
| `tags` | text[] | Searchable keywords |
| `related_concepts` | text[] | **Linked CoreConcept IDs** |

**Example Data:**
```json
{
  "content_id": "uc_004",
  "title": "Email Optimization and Response Drafting",
  "application": "Improve email clarity, tone, and effectiveness...",
  "ai_concepts": "Natural language processing, style transfer",
  "business_value": "Increased productivity, improved communication quality",
  "role": "general",
  "tags": ["email", "communication", "productivity"],
  "related_concepts": ["concept_003", "concept_007", "concept_011"]
}
```

**Key Feature:** The `related_concepts` field links use cases to core concepts, enabling:
- Recommending exercises after teaching a concept
- Building learning paths
- Tracking prerequisite knowledge

---

### 3. InteractionLog Collection

Stores user conversation history for personalized learning and context retrieval.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | text | User identifier (for isolation) |
| `session_id` | text | Session identifier |
| `interaction_type` | text | Type (`learn_concept`, `attempt_exercise`, `ask_question`) |
| `action_status` | text | Status (`completed`, `failed`, `skipped`) |
| `content_type` | text | Content type (`core_concept`, `use_case`, `free_form`) |
| `content_id` | text | Related content ID |
| `user_message` | text | User's input |
| `agent_response` | text | Agent's response |
| `conversation_text` | text | Combined text for semantic search |
| `topic` | text | Discussion topic |
| `timestamp` | date | Interaction timestamp |
| `importance_score` | number | Relevance score (0-1) |

**Privacy:** All queries **must** filter by `user_id` to ensure data isolation between users.

---

## Setup Instructions

### Prerequisites

```bash
# Install dependencies
pip install weaviate-client pandas python-dotenv

# Create .env file with:
WEAVIATE_URL=http://localhost:8080
OPENAI_API_KEY=your-openai-api-key
```

### Step 1: Start Weaviate (Local)

```bash
# Using Docker Compose
docker-compose up -d
```

### Step 2: Create Collections

```bash
# Run once to create schema
python scripts/setup_weaviate.py
```

**Output:**
```
✓ CoreConcept collection created
✓ UseCase collection created
✓ InteractionLog collection created
```

### Step 3: Load Data

```bash
# Load CSV data into Weaviate
python scripts/load_data.py
```

**Output:**
```
✓ Successfully loaded 12 core concepts
✓ Successfully loaded 10 use cases
```

---

## Query Examples

### Search for Concepts

```python
from weaviate import Client

client = Client("http://localhost:8080")

# Semantic search
results = client.query.get(
    "CoreConcept",
    ["content_id", "title", "content"]
).with_near_text({
    "concepts": ["how to write better prompts"]
}).with_limit(3).do()
```

### Find Related Exercises

```python
# Get exercises for a learned concept
results = client.query.get(
    "UseCase",
    ["content_id", "title", "application"]
).with_where({
    "path": ["related_concepts"],
    "operator": "ContainsAny",
    "valueTextArray": ["concept_003"]
}).do()
```

### Search User History

```python
# Semantic search in user's past conversations
results = client.query.get(
    "InteractionLog",
    ["conversation_text", "timestamp"]
).with_near_text({
    "concepts": ["email writing tips"]
}).with_where({
    "path": ["user_id"],
    "operator": "Equal",
    "valueText": "user_123"
}).do()
```

---

## Data Relationships

```
CoreConcept (Teaching)
    ↓
    | related_concepts
    ↓
UseCase (Practice)
    ↓
    | logs user attempts
    ↓
InteractionLog (History)
```

**Learning Flow:**
1. User learns a `CoreConcept`
2. System recommends `UseCase` exercises via `related_concepts`
3. User interaction logged in `InteractionLog`
4. System uses history for personalized recommendations

---

## Embeddings

All text fields are automatically converted to **1536-dimensional vectors** using OpenAI's `text-embedding-3-small` model. This enables:

- Semantic search (find similar concepts)
- Context retrieval (relevant conversation history)
- Intelligent recommendations (related content)

**Cost:** Approximately $0.02 per 1M tokens (~$0.0001 for this dataset)

---

## Integration with Backend

### PostgreSQL (Structured Data)
- User profiles
- Learning progress
- Quiz scores
- Login timestamps

### Weaviate (Vector Data)
- Learning content (CoreConcept, UseCase)
- Conversation history (InteractionLog)
- Semantic search capabilities

**Backend should:**
1. Query Weaviate for content retrieval
2. Log interactions to Weaviate's InteractionLog
3. Update user progress in PostgreSQL
4. Combine both sources for comprehensive user profiles

---

## Security Notes

**User Isolation:**
- Always filter by `user_id` when querying `InteractionLog`
- Never expose other users' conversation data
- Implement proper authentication before database access

**API Keys:**
- Keep `OPENAI_API_KEY` secure (never commit to git)
- Use environment variables for all credentials
- Rotate keys regularly

---

## Maintenance

### Update Data
```bash
# Reload CSV data
python scripts/load_data.py
```

### Rebuild Schema
```bash
# Delete and recreate collections
python scripts/setup_weaviate.py
python scripts/load_data.py
```

### Monitor Usage
```bash
# Check collection sizes
curl http://localhost:8080/v1/schema
```

---

## Future Enhancements

- [ ] Add more core concepts (ML, Deep Learning, etc.)
- [ ] Expand use cases for different roles
- [ ] Implement automatic content curation
- [ ] Add multilingual support
- [ ] Create data retention policies for GDPR compliance

---

## Support

For questions or issues:
1. Check Weaviate logs: `docker-compose logs -f`
2. Verify collections: `http://localhost:8080/v1/schema`
3. Test queries using the Weaviate Console

---

## References

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- Project Documentation: `/docs/008-Database-schema.md`
