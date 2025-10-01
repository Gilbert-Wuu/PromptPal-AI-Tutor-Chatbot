# Database Setup - AI Learning Platform

Unified database setup for the AI Learning Platform, containing both PostgreSQL (structured data) and Weaviate (vector data) configurations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AI Learning Platform                  │
│            Federated Hermes AI Education Tool            │
└─────────────────────────────────────────────────────────┘
                           │
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐                  ┌─────────▼────────┐
│   PostgreSQL   │                  │     Weaviate     │
│  (Port 5432)   │                  │   (Port 8080)    │
└────────────────┘                  └──────────────────┘
│                                   │
│ • User Profiles                   │ • Educational Content
│ • Learning Progress               │ • Core AI Concepts
│ • Quiz Scores                     │ • Use Case Examples
│ • User Summaries                  │ • Conversation History
│ • Structured Metadata             │ • Vector Embeddings
│                                   │ • Semantic Search
└────────────────┘                  └──────────────────┘
```

## Why Two Databases?

### PostgreSQL - Structured Data Store
Best for data that requires:
- ACID transactions (atomicity, consistency, isolation, durability)
- Complex relationships and joins
- Strong consistency guarantees
- SQL querying capabilities

**Use Cases:**
- User authentication and profiles
- Learning progress tracking
- Quiz scores and module completion
- User summaries (compressed context)

### Weaviate - Vector Database
Best for data that requires:
- Semantic similarity search
- AI-powered content retrieval
- Vector embeddings storage
- Hybrid search (keyword + semantic)

**Use Cases:**
- Educational content with embeddings
- Conversation history with semantic search
- User-specific memory isolation
- Context-aware recommendations

---

## Directory Structure

```
DB_Setup/
├── docker-compose.yml        # Unified container orchestration
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
│
├── PostgreSQL/               # Structured data (user profiles, progress)
│   ├── scripts/
│   │   ├── init_database.sql         # Auto-run on first start
│   │   ├── setup_postgresql.py       # Verification script
│   │   └── add_summary_columns.sql   # Migration for summaries
│   └── README.md             # PostgreSQL-specific documentation
│
└── Vector_DB/                # Vector data (content, conversations)
    ├── data/
    │   ├── ai_concepts.csv           # Core learning concepts
    │   └── use_cases.csv             # Practical exercises
    ├── scripts/
    │   ├── setup_weaviate.py         # Create collections
    │   ├── load_data.py              # Load CSV data
    │   └── config.py                 # Configuration helper
    └── README.md             # Weaviate-specific documentation
```

---

## Quick Start Guide

### Prerequisites

**Required Software:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- Python 3.8+

**Python Dependencies:**
```bash
pip install asyncpg weaviate-client pandas python-dotenv
```

### Step 1: Clone and Configure

```bash
# Navigate to DB_Setup directory
cd DB_Setup

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```bash
OPENAI_API_KEY=sk-your-api-key-here          # Required for embeddings
POSTGRES_PASSWORD=your_secure_password        # Required for PostgreSQL
```

### Step 2: Start Database Services

```bash
# Start both PostgreSQL and Weaviate
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Expected Output:**
```
NAME                  STATUS              PORTS
ai_tutor_postgres     Up (healthy)        0.0.0.0:5432->5432/tcp
ai_tutor_weaviate     Up                  0.0.0.0:8080->8080/tcp, 0.0.0.0:50051->50051/tcp
```

### Step 3: Verify PostgreSQL

```bash
cd PostgreSQL
python scripts/setup_postgresql.py
```

**Expected Output:**
```
✓ Successfully connected to PostgreSQL
✓ Found 2 tables: users, progress
✓ Users table has 11 columns
✓ Found 8 indexes
✓ Found 7 helper functions
✓ Found 3 sample users
```

### Step 4: Setup Weaviate

```bash
cd ../Vector_DB
python scripts/setup_weaviate.py
python scripts/load_data.py
```

**Expected Output:**
```
✓ CoreConcept collection created
✓ UseCase collection created
✓ InteractionLog collection created
✓ Successfully loaded 12 core concepts
✓ Successfully loaded 10 use cases
```

### Step 5: Verify Complete Setup

```bash
# Test PostgreSQL connection
psql -h localhost -U ai_tutor_admin -d ai_tutor_db -c "\dt"

# Test Weaviate API
curl http://localhost:8080/v1/meta
```

---

## Database Architecture Details

### Data Flow

```
User Query
    │
    ▼
┌─────────────────────────┐
│   Backend Application   │
└─────────────────────────┘
    │                 │
    ▼                 ▼
PostgreSQL        Weaviate
    │                 │
    │                 │
1. Get user        2. Search
   profile            content
   + summaries        + history
    │                 │
    └─────┬───────────┘
          ▼
    Generate AI
     Response
          │
          ▼
3. Update        4. Log full
   progress         interaction
   (PostgreSQL)     (Weaviate)
```

### PostgreSQL Schema

**Tables:**
- `users` - User profiles with short/long-term summaries
- `progress` - Module completion and quiz scores

**Key Features:**
- JSONB columns for flexible data storage
- Full-text search indexes on summaries
- Helper functions for common operations
- Auto-triggers for progress tracking

[See PostgreSQL/README.md for complete schema details]

### Weaviate Collections

**Collections:**
- `CoreConcept` - AI learning concepts with embeddings
- `UseCase` - Practical exercises linked to concepts
- `InteractionLog` - User conversation history (isolated by user_id)

**Key Features:**
- OpenAI text-embedding-3-small (1536 dimensions)
- Hybrid search (semantic + keyword)
- User-specific data isolation
- Related content linking

[See Vector_DB/README.md for complete schema details]

---

## Common Operations

### Starting Services

```bash
# Start both databases
docker-compose up -d

# Start only PostgreSQL
docker-compose up -d postgres

# Start only Weaviate
docker-compose up -d weaviate
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove all data (⚠️ DESTRUCTIVE)
docker-compose down -v
```

### Viewing Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres
docker-compose logs -f weaviate

# View last 100 lines
docker-compose logs --tail=100
```

### Database Backups

**PostgreSQL Backup:**
```bash
# Create backup
docker exec ai_tutor_postgres pg_dump -U ai_tutor_admin ai_tutor_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i ai_tutor_postgres psql -U ai_tutor_admin ai_tutor_db < backup_20250929.sql
```

**Weaviate Backup:**
```bash
# Backup volumes
docker run --rm -v db_setup_weaviate_data:/data -v $(pwd):/backup alpine tar czf /backup/weaviate_backup.tar.gz /data

# Restore volumes
docker run --rm -v db_setup_weaviate_data:/data -v $(pwd):/backup alpine tar xzf /backup/weaviate_backup.tar.gz -C /
```

### Monitoring

```bash
# Check container resource usage
docker stats ai_tutor_postgres ai_tutor_weaviate

# Check database sizes
docker exec ai_tutor_postgres psql -U ai_tutor_admin -d ai_tutor_db \
  -c "SELECT pg_size_pretty(pg_database_size('ai_tutor_db'));"

# Check Weaviate collections
curl http://localhost:8080/v1/schema | jq '.classes[].class'
```

---

## Integration Example

### Full Workflow Implementation

```python
import asyncio
import asyncpg
import weaviate
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class AITutorDatabase:
    def __init__(self):
        self.pg_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "database": os.getenv("POSTGRES_DB", "ai_tutor_db"),
            "user": os.getenv("POSTGRES_USER", "ai_tutor_admin"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    async def handle_user_query(self, user_id: str, user_query: str):
        """Complete workflow for handling a user query"""
        
        # 1. Connect to both databases
        pg_conn = await asyncpg.connect(**self.pg_config)
        weaviate_client = weaviate.connect_to_local(host="localhost", port=8080)
        
        try:
            # 2. Get user context from PostgreSQL
            user_context = await pg_conn.fetchrow(
                "SELECT * FROM get_user_context($1)",
                user_id
            )
            
            print(f"User: {user_context['email']}")
            print(f"Proficiency: {user_context['proficiency']}")
            print(f"Short-term context: {user_context['short_term_summary'][:100]}...")
            
            # 3. Search educational content in Weaviate
            concepts = weaviate_client.collections.get("CoreConcept") \
                .query.hybrid(
                    query=user_query,
                    alpha=0.7,  # Favor semantic search
                    limit=3,
                    where={
                        "path": ["role"],
                        "operator": "ContainsAny",
                        "valueTextArray": [user_context['role'].lower(), "general"]
                    }
                ).objects
            
            print(f"\nFound {len(concepts)} relevant concepts")
            
            # 4. Search user's conversation history
            history = weaviate_client.collections.get("InteractionLog") \
                .query.hybrid(
                    query=user_query,
                    alpha=0.8,
                    limit=5,
                    where={
                        "path": ["user_id"],
                        "operator": "Equal",
                        "valueText": user_id
                    }
                ).objects
            
            print(f"Found {len(history)} relevant past interactions")
            
            # 5. Generate AI response (placeholder)
            response = self.generate_response(
                user_query=user_query,
                user_context=user_context,
                concepts=concepts,
                history=history
            )
            
            # 6. Update PostgreSQL progress
            if "completed_module" in response:
                await pg_conn.execute(
                    "SELECT add_completed_module($1, $2)",
                    user_id, response["completed_module"]
                )
                print(f"\n✓ Updated progress: {response['completed_module']}")
            
            # 7. Update short-term summary
            new_summary = await self.generate_short_term_summary(
                user_context, user_query, response
            )
            await pg_conn.execute(
                "SELECT update_short_term_summary($1, $2)",
                user_id, new_summary
            )
            print("✓ Updated short-term summary")
            
            # 8. Log interaction to Weaviate
            weaviate_client.collections.get("InteractionLog").data.insert({
                "user_id": user_id,
                "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "interaction_type": "learn_concept",
                "user_message": user_query,
                "agent_response": response["text"],
                "conversation_text": f"{user_query} {response['text']}",
                "topic": response.get("topic", "general"),
                "timestamp": datetime.now().isoformat(),
                "importance_score": 0.7
            })
            print("✓ Logged interaction to Weaviate")
            
            return response
            
        finally:
            await pg_conn.close()
            weaviate_client.close()
    
    def generate_response(self, user_query, user_context, concepts, history):
        """Generate AI response (placeholder)"""
        return {
            "text": "This is where the AI-generated response would be...",
            "topic": "prompt_engineering",
            "completed_module": None
        }
    
    async def generate_short_term_summary(self, user_context, query, response):
        """Generate updated short-term summary (placeholder)"""
        return f"Recently asked about: {query[:50]}... Learning focus: {response.get('topic', 'general')}"


# Example usage
async def main():
    db = AITutorDatabase()
    
    # Get first user from database
    pg_conn = await asyncpg.connect(**db.pg_config)
    user = await pg_conn.fetchrow("SELECT user_id FROM users LIMIT 1")
    await pg_conn.close()
    
    # Handle query
    await db.handle_user_query(
        user_id=str(user['user_id']),
        user_query="How do I write better prompts for financial analysis?"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### PostgreSQL Issues

**Problem: Connection refused**
```bash
# Check if container is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify port is available
lsof -i :5432
```

**Problem: Init script didn't run**
```bash
# Remove volume and restart
docker-compose down -v
docker-compose up -d postgres
```

**Problem: Can't connect with psql**
```bash
# Wait for health check
docker-compose ps

# Check credentials in .env
cat .env | grep POSTGRES
```

### Weaviate Issues

**Problem: Missing OpenAI API key**
```bash
# Verify .env file
cat .env | grep OPENAI_API_KEY

# Restart container
docker-compose restart weaviate
```

**Problem: Collections not created**
```bash
# Check Weaviate logs
docker-compose logs weaviate

# Manually run setup
cd Vector_DB
python scripts/setup_weaviate.py
```

**Problem: Data not loaded**
```bash
# Verify CSV files exist
ls -la Vector_DB/data/

# Run load script
cd Vector_DB
python scripts/load_data.py
```

### Network Issues

**Problem: Services can't communicate**
```bash
# Check network
docker network inspect db_setup_ai_tutor_network

# Verify both services are on same network
docker inspect ai_tutor_postgres | grep NetworkMode
docker inspect ai_tutor_weaviate | grep NetworkMode
```

### Data Issues

**Problem: Data not persisting**
```bash
# Check volumes exist
docker volume ls | grep db_setup

# Inspect volumes
docker volume inspect db_setup_postgres_data
docker volume inspect db_setup_weaviate_data
```

---

## Security Considerations

### Development Setup (Current)

The current configuration is suitable for local development:
- Anonymous Weaviate access enabled
- Default PostgreSQL credentials
- No SSL/TLS encryption
- Services exposed on localhost only

### Production Recommendations

**1. Enable Authentication**
```yaml
# docker-compose.yml
weaviate:
  environment:
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
    AUTHENTICATION_APIKEY_ENABLED: 'true'
    AUTHENTICATION_APIKEY_ALLOWED_KEYS: '${WEAVIATE_API_KEY}'
```

**2. Use Docker Secrets**
```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  openai_api_key:
    file: ./secrets/openai_api_key.txt

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

**3. Enable SSL/TLS**
```yaml
postgres:
  volumes:
    - ./certs:/etc/ssl/certs
  environment:
    POSTGRES_SSL: 'on'
```

**4. Network Isolation**
```yaml
# Don't expose ports publicly in production
# Use reverse proxy (nginx, traefik) instead
services:
  postgres:
    expose:
      - "5432"
    # Remove 'ports' section
```

**5. Row-Level Security**
```sql
-- Enable RLS in PostgreSQL
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress ENABLE ROW LEVEL SECURITY;
```

**6. Regular Backups**
```bash
# Setup automated backups
0 2 * * * /path/to/backup_script.sh
```

---

## Performance Optimization

### PostgreSQL Tuning

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM user_profile_summary WHERE email = 'test@example.com';

-- Update statistics
ANALYZE users;
ANALYZE progress;

-- Vacuum regularly
VACUUM ANALYZE;
```

### Weaviate Tuning

```python
# Adjust alpha parameter for optimal results
# alpha = 0.0: Pure keyword search
# alpha = 0.5: Balanced hybrid
# alpha = 1.0: Pure vector search

response = collection.query.hybrid(
    query="prompt engineering",
    alpha=0.7,  # Tune based on your use case
    limit=5
)
```

### Connection Pooling

```python
# Use connection pooling for PostgreSQL
import asyncpg

pool = await asyncpg.create_pool(
    **DATABASE_CONFIG,
    min_size=5,
    max_size=20
)
```

---

## Maintenance Tasks

### Daily
- Monitor container resource usage
- Check error logs
- Verify service health

### Weekly
- Review database sizes
- Update PostgreSQL statistics
- Check backup integrity

### Monthly
- Update Docker images
- Review and optimize queries
- Clean up old data
- Update user summaries (long-term)

---

## Cost Estimation

### OpenAI Embeddings
- Model: text-embedding-3-small
- Cost: $0.00002 per 1K tokens
- Estimated monthly cost for 100 active users: ~$5-10

### Infrastructure
- PostgreSQL: Minimal (Docker local)
- Weaviate: Minimal (Docker local)
- Production deployment: Varies by provider

---

## Next Steps

1. **Review Component Documentation**
   - Read [PostgreSQL/README.md](./PostgreSQL/README.md)
   - Read [Vector_DB/README.md](./Vector_DB/README.md)

2. **Customize for Your Needs**
   - Add your educational content to Vector_DB/data/
   - Modify user roles in PostgreSQL constraints
   - Adjust learning modules and goals

3. **Integrate with Backend**
   - Implement the workflow example above
   - Add authentication layer
   - Create API endpoints

4. **Deploy to Production**
   - Enable authentication
   - Setup SSL/TLS
   - Configure backups
   - Implement monitoring

---

## Support and Resources

### Documentation
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

### Troubleshooting
- Check logs: `docker-compose logs -f`
- Verify network: `docker network inspect db_setup_ai_tutor_network`
- Test connections: Use provided verification scripts

### Project Structure
- Database schemas: `/PostgreSQL/README.md` and `/Vector_DB/README.md`
- Sample data: `/Vector_DB/data/`
- Setup scripts: `scripts/` folders in each directory

---

## License and Credits

This database setup is designed for the Federated Hermes AI Learning Platform capstone project at CMU Heinz College.

**Technologies Used:**
- PostgreSQL 15
- Weaviate 1.26.1
- OpenAI Embeddings
- Docker & Docker Compose
