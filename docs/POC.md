# Proof of Concept (POC) Document  

## 1. Objective of the POC  
The purpose of this Proof of Concept is to validate the feasibility of an **AI-powered tutor chatbot** that can later be integrated into Athena.  

The POC will demonstrate the chatbot’s ability to:  
- Answer both **general AI literacy** questions and **company-specific knowledge** queries  
- Provide one **guided learning module** (e.g., prompt engineering basics)  
- Log user interactions for review and assessment  

This POC will serve as the foundation for the full solution to be presented in midterm and final deliverables.  

## 2. Scope of the POC (First 2 Weeks)  

### Functional Requirements  
- Chatbot embedded in a **demo web UI** (temporary front-end for testing)  
- Supports **freeform Q&A**  
- Connects to a **sample company knowledge base** (e.g., Athena FAQ, Power BI guide)  
- Provides **one structured learning module** (intro to AI / prompt engineering)  
- Basic **user progress logging** (quiz scores, usage history)  

### Non-Functional Requirements  
- **Response time**: ≤ 3 seconds average  
- **Accuracy**: ≥ 70% of answers rated “helpful” in internal testing  
- **Concurrency**: Support ~20 test users  
- **Security**: Contained within demo system, no data leakage  
- **Transparency**: Logs stored for QA and debugging  


## 3. Technical Approach  

**Architecture (POC Version):**  
- **Frontend:** Demo UI (chat window + basic controls)  
- **Conversational Engine:** OpenAI GPT (or alternative LLM)  
- **Knowledge Base:** Limited company docs, indexed in a lightweight vector database  
- **Modules:**  
  - Concept Explainer  
  - Prompt Engineering Exercise  
- **Logging:** Basic event logging (SQLite/Postgres)  


## 4. Timeline & Milestones  

- **Phase 0 (Sept 4 – Sept 16)**  
  - Project setup and repo initialization  
  - Define requirements & success metrics  
  - Create workflow & define technical architecture  
  - **Output:** POC plan + GitHub repo initialized  

- **Phase 1 (Sept 16 – Sept 27)**  
  - Build base demo UI shell (chat window, simple controls)  
  - Connect demo UI to OpenAI API for Q&A  
  - Load sample company document into knowledge base  
  - **Output:** Working chatbot prototype that can answer general + company questions  

- **Phase 2 (Sept 29 – Oct 3)**  
  - Expand demo UI with improvements (e.g., simple menus, formatting)  
  - Implement guided learning module (intro to AI / prompt engineering)  
  - Add basic logging for user progress (SQLite/Postgres)  
  - **Output:** Minimum viable POC ready for testing  

- **Phase 3 (Oct 6 – Oct 10)**  
  - Conduct internal demo with test users (3–5 people)  
  - Collect feedback on usability and accuracy  
  - Refine module & logging based on feedback  
  - **Output:** Polished POC, ready for midterm presentation  


## 5. Success Criteria  
The POC will be considered successful if:  
- The chatbot runs in the **demo UI**  
- It can answer at least one **general AI question** and one **company-specific question**  
- At least 3–5 employees test it and confirm usability  
- Interaction logs and quiz results are recorded successfully  


## 6. Alignment with Capstone Milestones  

- **Sept 29** – POC finalized and documented (this deliverable)  
- **Oct 6–10** – POC demonstrated during the first round of midterm presentations  
- **Oct 20–24** – Enhanced POC with expanded features presented in the second round of midterms  
- **Nov 17** – Creative video due (highlighting POC progress and outcomes)  
- **Dec 1–12** – Final presentations showcasing the refined system  
- **Dec 15** – Final deliverables submitted, including the complete chatbot solution  
  
