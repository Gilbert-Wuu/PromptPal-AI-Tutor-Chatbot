# Proof of Concept (POC) Document  


## 1. Objective of the POC  
The purpose of this Proof of Concept is to validate the feasibility of an **AI-powered tutor chatbot** that can later be integrated into Athena.  

The POC will demonstrate the chatbot’s ability to:  
- Answer both **general AI literacy** questions and **company-specific knowledge** queries  
- Provide one **guided learning module** (e.g., prompt engineering basics)  
- Offer **preliminary prompts** for users to select from, easing onboarding and exploration  
- Log user interactions for review and assessment  

This POC will serve as the foundation for the full solution to be presented in midterm and final deliverables.  


## 2. Scope of the POC (First 2 Weeks)  

### Functional Requirements  
- Chatbot embedded in a **demo web UI** (temporary front-end for testing)  
- Supports **freeform Q&A**  
- Provides **preliminary prompts** for users to select (starter examples / guided entry points)  
- Connects to a **sample company knowledge base** (e.g., Athena FAQ, Power BI guide)  
- Provides **one structured learning module** (intro to AI / prompt engineering)
  - Learning module should include step-by-step lessons (bite-sized AI concepts) and interactive exercises (e.g., multiple choice, prompt writing), with results logged for tracking progress.
- Basic **user progress logging** (quiz scores, usage history)  

### Non-Functional Requirements 
- **Response time**: Should be reasonably fast for demo purposes (target <10 seconds, but not strict)  
- **Accuracy**: ≥ 70% of answers rated “helpful” in internal testing  
- **Deployment/Concurrency**: POC will run in local environments; scalability and concurrency will be considered in later phases  
- **Security**: Contained within demo system, no data leakage  
- **Transparency**: Logs stored for QA and debugging  


## 3. Technical Approach  

**Architecture (POC Version):**  
- **Frontend:** Demo UI (chat window + basic controls + preliminary prompts)  
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
  - Create workflow & draft technical architecture (HLD)  
  - **Output:** POC plan + GitHub repo initialized  

- **Phase 1 (Sept 16 – Sept 27)**  
  - Define AI agent interactions and roles  
  - Design chatbot survey for assessing user AI proficiency and store results in vector DB
  - Define schemas for knowledge base (vector storage, chunking, embeddings, similarity search) and align frontend/backend data structures
  - Build base demo UI shell (chat window, simple controls, preliminary prompts)  
  - Connect demo UI to OpenAI API for Q&A  
  - Load sample company document into knowledge base  
  - **Output:** Working chatbot prototype capable of handling basic interactions  

- **Phase 2 (Sept 29 – Oct 3)**  
  - Expand demo UI with improvements (menus, formatting)  
  - Implement guided learning module, including:  
    - Step-by-step lesson flow (e.g., intro to AI concepts, prompt basics)  
    - At least one interactive exercise (multiple choice or prompt writing)  
  - Add logging for user progress and exercise results (quiz scores, lesson completion)  
  - **Output:** Minimum viable POC with one complete learning + exercise module, ready for initial testing  

- **Phase 3 (Oct 6 – Oct 10)**  
  - Conduct internal demo with test users (3–5 people)  
  - Collect feedback on usability and accuracy  
  - Refine module & logging based on feedback  
  - **Output:** Polished POC, ready for midterm presentation  



## 5. Success Criteria  
The POC will be considered successful if:  
- The chatbot runs in the **demo UI**  
- It can answer at least one **general AI question** and one **company-specific question**  
- Offers **starter prompts** that help guide users into interactions  
- At least 3–5 employees test it and confirm usability  
- Interaction logs and quiz results are recorded successfully  



## 6. Alignment with Capstone Milestones  

- **Sept 29** – POC finalized and documented (this deliverable)  
- **Oct 6–10** – POC demonstrated during the first round of midterm presentations  
- **Oct 20–24** – Enhanced POC with expanded features presented in the second round of midterms  
- **Nov 17** – Creative video due (highlighting POC progress and outcomes)  
- **Dec 1–12** – Final presentations showcasing the refined system  
- **Dec 15** – Final deliverables submitted, including the complete chatbot solution  
