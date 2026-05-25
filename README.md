# PromptPal

PromptPal is an AI-powered learning platform that helps employees at Federated Hermes understand AI concepts, learn prompt engineering, and explore practical use cases through a conversational tutor chatbot.

---

## Architecture

PromptPal's chat pipeline is built on **LangGraph** — a directed graph where each processing step is an isolated node that reads from and writes to a shared state object. Follow-up questions and navigation suggestions run in parallel, cutting response latency by ~30%.

**[View Interactive Architecture →](https://htmlpreview.github.io/?https://github.com/RishabhDev42/PromptPal/blob/main/docs/langgraph_architecture.html)**

```
[fetch_summaries] → [trainer] → [follow_up]  ↘
                              ↘ [navigator]  → [save_module]
```

See [`docs/012-LangGraph-Migration.md`](./docs/012-LangGraph-Migration.md) for the full migration write-up: problems discovered, decisions made, and performance impact.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router) + React 19 |
| Backend | FastAPI + Python 3.11+ |
| Relational DB | PostgreSQL (Supabase hosted) |
| Vector DB | Weaviate 1.27.1 (Docker) |
| Primary LLM | Google Gemini 2.5 Pro |
| Secondary LLM | OpenAI GPT-4 / GPT-5-mini |
| Orchestration | LangGraph |
| Observability | LangSmith |

---

## Recommended Versions

- Python 3.12.7 / pip 25.1.1
- Node.js 24.11.0 / npm 11.6.1

---

## One-Time Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/RishabhDev42/PromptPal.git
cd PromptPal

pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Set up environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required variables: `POSTGRES_*`, `WEAVIATE_URL`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `JWT_SECRET`.

Optional (for LangSmith observability): `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`.

### 3. Initialize the database

Run the SQL scripts in [`Database-setup/PostgreSQL/scripts/`](./Database-setup/PostgreSQL/scripts/) against your PostgreSQL instance.

---

## Running the Project

Make sure **Docker Desktop** is open, then:

```bash
# Backend only — fastest for API testing
make api
# API explorer available at http://127.0.0.1:8000/docs

# Full stack — Backend + Frontend
make dev
# Frontend at http://localhost:3000

# Stop everything
make stop
```

> `make api` is the recommended default during development. Use the built-in API explorer at `/docs` (equivalent to Postman) to test endpoints without running the frontend.

---

## Project Structure

```
PromptPal/
├── backend/app/
│   ├── main.py               # FastAPI app + all endpoints
│   ├── agents/               # TrainerAgent, NavigatorAgent, SummaryAgent, ...
│   └── graph/                # LangGraph pipeline
│       ├── state.py           # PromptPalState TypedDict
│       ├── chat_graph.py      # Graph factory (nodes + edges)
│       └── nodes/             # One file per node
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   └── components/           # ChatComponent, QuizComponent, ...
├── Database-setup/
│   ├── PostgreSQL/scripts/   # SQL init scripts
│   └── VectorDB/             # Weaviate schema + data loading
├── docs/                     # Architecture docs + HTML visualization
├── Makefile                  # Dev shortcuts
└── requirements.txt
```
