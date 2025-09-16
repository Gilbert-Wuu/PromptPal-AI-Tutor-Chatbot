# Technology Discovery: Model Selection for AI Tutoring

## Project Learning Priorities
Based on client objectives, model selection will focus on three key priorities:

1. **Deliver general AI concepts to employees**  
2. **Teach prompt engineering skills**  
3. **Support common daily use cases (emails, document summaries, forms, etc.)**

---

## Priority 1: Deliver General AI Concepts
**Requirements**
- Accurate, reliable explanations of concepts  
- Multi-turn conversational ability  
- Adaptive teaching (adjust difficulty based on user proficiency)

**Recommended Models**
- **GPT-5 (Input: $1.25, Output: $10.00 / 1M tokens)**  
  Best choice for structured tutoring and adaptive learning  
- **Gemini 2.5 Pro (Input: $1.25, Output: $10.00 / 1M tokens)**  
  Strong for long-context and document-based lessons.  
- **GPT-5-mini (Input: $0.25, Output: $2.00 / 1M tokens)**  
  Lower-cost option for flashcards, quick definitions, or lightweight quizzes.

---

## Priority 2: Prompt Engineering Training
**Requirements**
- Consistent responses across a wide range of prompts  
- Demonstrates “good” vs. “bad” prompting  
- Tool-calling support for hands-on experiments

**Recommended Models**
- **GPT-5** – stable reasoning, cost-efficient for interactive training.  
- **GPT-5-mini ($0.25 in / $2.00 out)** – affordable practice sessions.  
- **Claude 4 Sonnet ($3.00 in / $15.00 out)** – transparent reasoning, helpful for teaching.

---

## Priority 3: Daily Productivity Use Cases
**Requirements**
- Cost-efficient and responsive  
- Handles summarization, drafting, and structured responses  
- Strong integration with Microsoft ecosystem (Teams, Outlook, Copilot)

**Recommended Models**
- **GPT-5-nano ($0.05 in / $0.40 out per 1M tokens)** – ultra-low cost for repetitive tasks 
- **GPT-5-mini** – balance of quality and price  
- **Gemini 2.5 Flash (Input: $0.30, Output: $2.50 / 1M tokens)** – very low latency, affordable, scalable   

---

## API Pricing Comparisons (as of 2025)

### OpenAI (GPT Family)
| Model            | Input / 1M | Cached Input / 1M | Output / 1M |
|------------------|------------|-------------------|-------------|
| **GPT-5**        | $1.25      | $0.125            | $10.00      |
| **GPT-5-mini**   | $0.25      | $0.025            | $2.00       |
| **GPT-5-nano**   | $0.05      | $0.005            | $0.40       |
| GPT-5-chat-latest| $1.25      | $0.125            | $10.00      |
| GPT-4.1          | $2.00      | $0.50             | $8.00       |
| GPT-4.1-mini     | $0.40      | $0.10             | $1.60       |
| GPT-4.1-nano     | $0.10      | $0.025            | $0.40       |
| GPT-4o           | $2.50      | $1.25             | $10.00      |

---

### Google Gemini 2.5
| Model                  | Input / 1M | Output / 1M |
|-------------------------|------------|-------------|
| Gemini 2.5 Flash-Lite   | $0.10      | $0.40       |
| Gemini 2.5 Flash        | $0.30      | $2.50       |
| Gemini 2.5 Pro (≤200k)  | $1.25      | $10.00      |
| Gemini 2.5 Pro (>200k)  | $2.50      | $15.00      |

---

### Anthropic Claude 4
| Model              | Input / 1M | Output / 1M |
|--------------------|------------|-------------|
| Claude 4 Sonnet    | $3.00      | $15.00      |
| (>200k token prompts) | $6.00   | $22.50      |

---

## Hybrid Tutor with Retrieval Mode
While most teaching modules can rely on static model knowledge, some scenarios require **fresh references** (e.g., the latest AI use cases, new regulations, current industry examples).

**Approach**
- **Closed-book default:**  
  Use GPT-5 / Gemini Pro for stable, consistent tutoring.  
- **Research mode (open-book):**  
  Triggered when a user explicitly asks for “latest” or “real-world examples.”  
  - Calls a retriever (Google Search API or Perplexity API).  
  - Retrieves top results and grounds them in model responses.  
  - Displays **sources alongside explanations** for transparency.  

**Benefits**
- Keeps baseline training stable and predictable.  
- Allows selective internet access only where valuable.  
- Provides employees with **current, cited references** without over-reliance on web search for every query.

---

## One Agent, Two Modes of Operation

The Tutor Agent will appear to employees as **one unified system**, but under the hood it runs in two distinct modes:

### 1. Closed-Book Mode (Default)
- **Powered by:** GPT-5 (primary) or Gemini Pro (secondary).  
- **Use cases:**  
  - Delivering AI concepts and explanations  
  - Running assessments and quizzes  
  - Prompt engineering practice  
  - Daily productivity exercises (summarizing documents, drafting emails)  
- **Why:** Stable, consistent, predictable cost and quality.

### 2. Research Mode (Triggered on Demand)
- **Trigger:** When an employee explicitly asks for “latest” or “real-world examples,” or when a learning module requires external references.  
- **Workflow:**  
  1. Tutor Agent sends the query to a **Search API** (Google Search, Bing, or Perplexity API).  
  2. Top results are retrieved.  
  3. GPT-5 or Gemini Pro summarizes and grounds the response with **citations**.  
- **Why:** Provides fresh, trustworthy, real-world examples without making every interaction dependent on the internet.

---

## Cost-Performance Strategy
- **High-value reasoning tasks (AI concepts, adaptive tutoring):** GPT-5 or Gemini 2.5 Pro  
- **Prompt engineering labs:** GPT-5-mini (low cost), optional Claude Sonnet for deeper reasoning demos  
- **Daily productivity tasks:** GPT-5-nano, Gemini 2.5 Flash/Flash-Lite  
- **Fresh external references:** Hybrid approach via Gemini + Search or Perplexity API

