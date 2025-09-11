# PromptPal

PromptPal is an AI-powered chatbot that helps employees at Federated Hermes understand AI concepts, learn prompt engineering, and explore practical use cases. It is designed as a modular, agent-based system with a central conversational engine that integrates with the firm’s internal Athena platform.

---

## Features

* Conversational engine supporting multi-turn, context-aware dialogue.
* Modular agent design for tasks such as:

  * AI fundamentals tutoring
  * Prompt editing and refinement
  * Use case discovery
* Adaptive learning approach based on user proficiency.
* Transparent logging for debugging and accountability.

---

## Technical Architecture

* **Core**: Central conversational engine (generative AI backbone).
* **Agents**: Specialized modules for different pedagogical tasks.
* **Integration**: Scalable deployment into Athena (Federated Hermes’ in-house AI portal).
* **Reasoning**: Chain-of-thought style internal evaluation before generating responses.

---

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/RishabhDev42/PromptPal.git
   cd promptpal
   ```
2. Install dependencies (Python + JS/TS stack):

   ```bash
   pip install -r requirements.txt
   npm install
   ```
3. Run the development server:

   ```bash
   npm run dev
   ```

---

## Roadmap

* [ ] Build central conversational engine
* [ ] Implement AI fundamentals agent
* [ ] Add prompt engineering/refinement agent
* [ ] Introduce adaptive learning module
* [ ] Integrate into Athena platform
