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

## How Agents Communicate

- Each agent is implemented as a **LangGraph node**.  
- Data flows through a **state object** (like a dictionary), which carries the user’s profile, current question, retrieved content, and assessment results.  
- Agents read from this state, process their part, and then **update the state** before handing it to the next agent.  

### Example Flow

1. **Navigator Agent**  
   - Writes to state:  
     ```json
     { "selected_prompt": "Explain supervised learning for finance" }
     ```

2. **Trainer Agent**  
   - Reads `selected_prompt` from state.  
   - Queries Weaviate DB.  
   - **If DB has content** → updates state:  
     ```json
     { "lesson": "...content from DB..." }
     ```  
   - **If DB has no content** → routes to **Curation Agent**.  

3. **Curation Agent**  
   - Fetches external references.  
   - Updates state with curated content:  
     ```json
     { "lesson": "...fetched from Perplexity..." }
     ```  
   - Returns control to **Trainer Agent** for synthesis.  

4. **Trainer Agent (Synthesis)**  
   - Synthesizes final lesson content from DB and/or curated references.  
   - Updates state:  
     ```json
     { "lesson": "...final explanation..." }
     ```  

5. **Assessment Agent**  
   - Reads `lesson` from state.  
   - Generates quiz.  
   - Updates state:  
     ```json
     { "quiz": "...questions..." }
     ```  

6. **Profile Updater**  
   - Reads quiz results from state.  
   - Updates PostgreSQL with:  
     ```json
     { "results": "...user performance..." }
     ```
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
