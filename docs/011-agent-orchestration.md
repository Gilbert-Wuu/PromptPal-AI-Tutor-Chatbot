# Agent Orchestration Architecture

## Overview
Our learning platform uses an **agent-based architecture** to deliver adaptive, personalized AI training.  
- **LangGraph** is the orchestration backbone.  
- It manages how agents pass information between each other, keeps a shared state, and supports branching workflows (e.g., fallback to external search if internal DB has no results).  

This design keeps all orchestration in one framework, with no reliance on external workflow tools.

---

## Why LangGraph Instead of LangChain Alone?
- **Stateful orchestration:** Agents share a central state object instead of passing raw outputs.  
- **Branching and looping:** Easier to implement “if/else” flows (e.g., search DB → if empty → call Curation Agent).  
- **Multi-agent focus:** Purpose-built for agent graphs, unlike classic LangChain chains.  
- **Scalability:** Adding or removing agents is easier as the graph grows.  

---

## Key Agents
1. **Learning Navigator Agent**  
   - Generates relevant prompts based on user profile, role, and past learning history.  
   - Hands prompts to the **Trainer Agent**.  

2. **Trainer Agent**  
   - Retrieves content from the Curriculum Vector DB (Weaviate).  
   - Synthesizes explanations with GPT-5.  
   - If content is missing, routes to the **Curation Agent**.  

3. **Curation Agent**  
   - Performs web search (Perplexity API) to supplement missing materials.  
   - Updates the state with new references for the Trainer Agent.  

4. **Assessment Agent**  
   - Generates quizzes to evaluate user understanding.  
   - Updates the user profile in Postgres with results.  

---

## Orchestration Flow

```mermaid
flowchart TD
    A[User Profile Creation] --> B[Learning Navigator Agent]
    B --> C[Trainer Agent]

    C -->|Vector Search| D[Weaviate DB]
    C -->|If no results| E[Curation Agent - Perplexity]
    E --> C

    C --> F[Synthesize & <br/>Deliver Response]
    F --> G[Assessment Agent]
    G --> H[Update Profile <br/>in PostgreSQL]
    H --> I[Log Results to Dashboard]

    %% Optional step styling
    style I stroke-dasharray: 5 5
