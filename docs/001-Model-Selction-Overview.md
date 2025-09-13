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
- **OpenAI GPT-4o / GPT-4-Turbo** – best for structured tutoring and adaptive learning  
- **Gemini 1.5 Pro** – strong at handling long-context and document-based lessons  
- **GPT-4o-mini or Llama 3 70B Instruct** – lower-cost option for flashcards, quick definitions, or lightweight quizzes  

---

## Priority 2: Prompt Engineering Training
**Requirements**
- Consistent responses across a wide range of prompts  
- Demonstrates “good” vs. “bad” prompting  
- Tool-calling support for hands-on experiments

**Recommended Models**
- **OpenAI GPT-4o** – stable for demonstrating prompt effectiveness  
- **Anthropic Claude 3 Sonnet/Opus** – strong at transparent reasoning, useful for training explanations  
- **GPT-4o-mini** – fast, inexpensive option for practice labs  

---

## Priority 3: Daily Productivity Use Cases
**Requirements**
- Cost-efficient and responsive  
- Handles summarization, drafting, and structured responses  
- Strong integration with Microsoft ecosystem (Teams, Outlook, Copilot)

**Recommended Models**
- **GPT-4o-mini** – optimized for speed and cost, ideal for email drafting and summarization  
- **Azure OpenAI GPT-4o** – integrates directly with Microsoft 365 productivity tools  
- **Gemini 1.5 Flash** – fast, low-latency model for repetitive task automation  

---

## Tiered Model Strategy
- **Tutoring & Concept Delivery (Assessment, Planner, Feedback Agents)**  
  → GPT-4o (primary), Gemini Pro (secondary for document-heavy learning)  

- **Prompt Engineering Practice (Experimentation Labs)**  
  → GPT-4o-mini (default), Claude Sonnet/Opus (optional for reasoning transparency)  

- **Daily Productivity (Exercise Generator, Task Assistant)**  
  → GPT-4o-mini and Gemini Flash (for cost-effective, high-frequency tasks)  

