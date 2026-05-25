# 012 — Migrating to LangGraph: Why We Did It and What Changed

*May 2026 — PromptPal Backend Architecture*

---

## How We Got Here

PromptPal started with a straightforward architecture: five Python classes (`TrainerAgent`, `NavigatorAgent`, `SummaryAgent`, `AssessmentAgent`, `DocumentAgent`) that each handled their own slice of functionality. The `/chat/` endpoint in `main.py` called them in sequence:

```
trainer.generate_learning_content() 
→ trainer.generate_follow_up_questions()
→ navigator.get_next_learning_options()
→ summary.save_completed_module()
```

This worked. But as the system became more complex, some cracks started showing — and a closer look at the logs revealed they were bigger than they first appeared.

---

## Problem 1: We Were Querying the Same Data Six Times Per Request

The first red flag appeared when profiling request latency. A single `/chat/` call was hitting PostgreSQL way more often than it should.

The root cause: both `TrainerAgent` and `NavigatorAgent` had been given a reference to `SummaryAgent` in their constructors (dependency injection), and both called it internally to fetch the user's memory context before doing their work.

```python
# Inside TrainerAgent.generate_learning_content():
long_term  = self.summary_agent.get_long_term_summary(user_id)   # DB call
short_term = self.summary_agent.get_short_term_summary(user_id)  # DB call + GPT-5-mini

# Inside TrainerAgent.generate_follow_up_questions():
long_term  = self.summary_agent.get_long_term_summary(user_id)   # SAME DB CALL AGAIN
short_term = self.summary_agent.get_short_term_summary(user_id)  # SAME AGAIN

# Inside NavigatorAgent.get_next_learning_options():
long_term_summary  = self.summary_agent.get_long_term_summary(user_id)  # THIRD TIME
short_term_summary = self.summary_agent.get_short_term_summary(user_id) # THIRD TIME
```

That's **6 database queries** and **3 GPT-5-mini API calls** per `/chat/` request, all fetching the exact same data. Every agent fetched its own copy because there was no shared runtime state — the only way to share data between agents was through the database, which meant writing it first and reading it fresh every time.

**Impact estimate**: `get_short_term_summary()` queries the last 5 interactions and then summarizes them with GPT-5-mini. That's roughly 200–400ms of DB + LLM time, times 3 = 600–1200ms wasted per request.

---

## Problem 2: Sequential Execution Where Parallel Was Possible

Looking at the call chain more carefully:

```
trainer.generate_learning_content()          # takes ~3–4s (Gemini call)
trainer.generate_follow_up_questions()       # takes ~1–2s (GPT-4 call)
navigator.get_next_learning_options()        # takes ~3–5s (embed + Weaviate + GPT-4)
summary.save_completed_module()              # takes ~500ms (embed + cosine check + DB write)
```

`generate_follow_up_questions()` and `get_next_learning_options()` are completely independent of each other — neither uses the other's output. But they ran sequentially, meaning we were waiting the full duration of both when we could wait the duration of just the longer one.

With a sequential wall-clock time of ~8–11s per request, this was a real UX problem.

---

## Problem 3: 200 Lines of Orchestration in One Endpoint

The `/chat/` endpoint in `main.py` had grown to around 200 lines. It mixed:
- Routing logic (`if is_initial: ...`)
- Agent calls
- DB writes (interactions table)
- Error handling for each step
- Response formatting

This made it impossible to test individual steps in isolation. To unit-test the follow-up question generation, you had to set up the entire endpoint context. To add a new processing step (e.g., a translation node or a safety check), you had to modify this 200-line function and figure out where to fit it.

---

## What We Decided to Do

The core insight is that what we called "agents" were actually stateless processing steps. The state lived in the database, and each step read it fresh because there was no in-memory shared context.

**LangGraph** models this exact pattern: a `TypedDict` state object that flows through a directed graph of nodes. Each node reads from state and writes back to it. The graph is compiled once and invoked per request.

This gives us:
1. **Fetch once, share everywhere** — a `fetch_summaries_node` runs first and puts memory context into state; all downstream nodes read from state instead of querying the DB
2. **Parallel execution** — follow-up questions and navigator suggestions are independent, so we wire them as parallel branches
3. **Clean separation** — each node is a pure function `PromptPalState → dict` that can be tested without touching main.py

---

## The New Graph Structure

```
[fetch_summaries_node]   ← fetches short_term, long_term, completed_modules ONCE
         │
    [trainer_node]       ← RAG + Gemini, reads summaries from state
       /         \
[follow_up_node]  [navigator_node]   ← PARALLEL: independent GPT-4 calls
       \         /
   [save_module_node]    ← join point: saves completed topic to DB
```

The key change in `fetch_summaries_node` is that it fetches **everything** up front:

```python
def fetch_summaries_node(state):
    short_term = summary_agent.get_short_term_summary(state["user_id"])   # once
    long_term  = summary_agent.get_long_term_summary(state["user_id"])    # once
    completed_modules = cursor.execute("SELECT ...")                        # once
    return {
        "short_term_summary": short_term,
        "long_term_summary":  long_term,
        "completed_modules":  completed_modules,
    }
```

All downstream nodes read `state["short_term_summary"]` and `state["long_term_summary"]` directly — no more redundant fetches.

---

## What Changed in the Codebase

**New files** in `backend/app/graph/`:

```
graph/
├── state.py              — PromptPalState TypedDict definition
├── chat_graph.py         — graph factory: instantiates agents, wires nodes + edges
└── nodes/
    ├── summary_node.py   — make_fetch_summaries_node()
    ├── trainer_node.py   — make_trainer_node()
    ├── followup_node.py  — make_follow_up_node()
    ├── navigator_node.py — make_navigator_node()
    └── save_module_node.py — make_save_module_node()
```

**Why factory functions instead of plain functions?**  
Each node needs access to its agent (TrainerAgent, SummaryAgent, etc.) and those agents need DB connections and LLM clients. Rather than passing these as global variables or using a class, each node file exposes a `make_*_node()` factory that captures the dependencies in a closure and returns a plain callable. This keeps nodes testable — you can inject mocks without patching globals.

**The existing agent classes stay unchanged.** The nodes call internal methods (`_search_knowledge_base`, `_build_clear_prompt`, `_store_conversation`, etc.) directly where needed, bypassing the summary-fetching logic that's now handled by `fetch_summaries_node`.

**`main.py`'s `/chat/` endpoint** becomes:
```python
result = chat_graph.invoke({
    "user_id":   req.user_id,
    "user_role": req.user_role,
    "query":     req.content,
    "selected_document_ids": req.selected_documents or [],
    # remaining fields initialized empty
    ...
})
return {
    "answer":             result["conversational_response"],
    "follow_up_questions": result["follow_up_questions"],
    "suggestions":        result["next_topic_suggestions"],
    "learning_options":   [],
}
```

The 200-line orchestration is replaced by a single `graph.invoke()` call.

**`assessment_agent.py` and `document_agent.py` were not changed.** They are independent CRUD/quiz flows with no inter-agent dependencies, so they don't benefit from a graph pattern.

---

## Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| DB queries per `/chat/` | 7 (4 redundant) | 3 (all unique) |
| GPT-5-mini calls for summarization | 3× | 1× |
| Follow-up + Navigator | Sequential | Parallel |
| Estimated request latency | ~8–12s | ~5–7s |
| Lines in `/chat/` endpoint | ~200 | ~15 |

---

## What We Didn't Change (Yet)

**Connection pooling**: The current code uses a single global `psycopg2.connect()`. Parallel branches sharing one connection is safe as long as LangGraph runs them in separate threads (which it does via `concurrent.futures`), but for higher concurrency we should migrate to `psycopg2.pool.ThreadedConnectionPool`. This is noted as a follow-up task.

**`cache_prompts_task` background task**: This still runs as a FastAPI `BackgroundTasks` after the graph returns. It could be modeled as a post-graph side effect node, but since it's already non-blocking and uses the same `NavigatorAgent` logic, leaving it as-is is fine for now.

**`AssessmentAgent`**: Independent flow, no state sharing needed, no change.

---

## Lessons

The most important lesson from this migration: **the "agent" pattern only helps if agents actually communicate through state, not by re-querying a shared database.** Our original design was shaped like agent-based code but behaved like a sequential script — each class fetched its own copy of the world before doing its job.

LangGraph made the state-passing explicit. Once we defined `PromptPalState`, it became obvious which fields were being redundantly computed and which steps could legitimately run in parallel. The graph structure *forced* clarity about data flow that the original class-based design had been hiding.
