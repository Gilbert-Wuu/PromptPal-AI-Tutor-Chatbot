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
│ • User Summaries                  │ • Vector Embeddings
│ • Interaction Log                 │ • Semantic Search
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
│   │   └── setup_postgresql.py       # Verification script
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
   + summaries 
    │                 │
    └─────┬───────────┘
          ▼
    Generate AI
     Response
          │
          ▼
3. Update        4. Keep static
   progress
   with ST/LT
   summary
   & interaction
   (PostgreSQL)     (Weaviate)
```

### PostgreSQL Schema

**Tables:**
- `users` - User profiles with short/long-term summaries
- `progress` - Module completion and quiz scores
- `interactions` - Interaction Log

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
