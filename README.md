# PromptPal

PromptPal is an AI-powered chatbot that helps employees at Federated Hermes understand AI concepts, learn prompt engineering, and explore practical use cases. It is designed as a modular, agent-based system with a central conversational engine that integrates with the firm’s internal Athena platform.

---

## Recommended Setup

Python version: 3.12.7
pip version: 25.1.1
Node.js version: 24.11.0
npm version: 11.6.1

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/RishabhDev42/PromptPal.git
   cd promptpal
   ```
2. Install dependencies (Python + JS/TS stack):

   ```bash
   pip install -r requirements.txt
   cd frontend
   npm install
   ```
   
3. Set up environment variables:

   Create a `.env` file in the root directory and add necessary configurations, [an example env file](./.env.example) is present in the root directory.

4. Set up the database:

   Add the database configuration in the `.env` file and run the SQL scripts located in the [`Database-setup` folder](./Database-setup/PostgreSQL/scripts) to create necessary tables.

5. Set up the Vector database:

   Start your docker engine, navigate to the [`VectorDB` folder](./Database-setup/VectorDB) and run:

   ```bash
    docker-compose up -d
    ```
   
6. Start the backend server:

   Navigate to the [`app` directory](./backend/app) and run:

   ```bash
    uvicorn main:app --reload
    ```
   
7. Run the development server:
    Navigate to the [`frontend` directory](./frontend) and run:
   ```bash
   npm run dev
   ```
