import logging
import dotenv
from openai import OpenAI
import weaviate
import os
import psycopg2
from .summary_agent import SummaryAgent

class NavigatorAgent:
    def __init__(self, llm, summary_agent, weaviate_client=None, model="gpt-4"):
        self.llm = llm
        self.model = model
        self.summary_agent = summary_agent
        self.weaviate_client = weaviate_client

    # -------------------------------------------------------------------------
    # Helper: build user context from profile memory
    # -------------------------------------------------------------------------
    def _build_user_context(self, user_role, long_term, short_term):
        return f"""
        Role: {user_role}
        Long-term memory: {long_term}
        Short-term memory: {short_term}
        """
    
    # -------------------------------------------------------------------------
    # Helper: embed text using OpenAI embedding model
    # -------------------------------------------------------------------------
    def _embed_text(self, text):
        try:
            response = self.llm.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Failed to embed text: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helper: retrieve relevant AI Concepts + Use Cases from Weaviate
    # -------------------------------------------------------------------------
    def _retrieve_related_items(self, user_vector, top_k=5):
        try:
            if not user_vector:
                return {"use_cases": [], "concepts": []}

            if not self.weaviate_client:
                logging.warning("Weaviate client not available")
                return {"use_cases": [], "concepts": []}

            usecase_collection = self.weaviate_client.collections.get("UseCase")
            usecase_query = usecase_collection.query.near_vector(
                near_vector=user_vector,
                limit=top_k
            )

            concept_collection = self.weaviate_client.collections.get("CoreConcept")
            concept_query = concept_collection.query.near_vector(
                near_vector=user_vector,
                limit=top_k
            )

            use_cases = []
            for obj in usecase_query.objects:
                use_cases.append({
                    'title': obj.properties.get('title', ''),
                    'application': obj.properties.get('application', ''),
                    'ai_concepts': obj.properties.get('ai_concepts', ''),
                    'role': obj.properties.get('role', '')
                })

            concepts = []
            for obj in concept_query.objects:
                concepts.append({
                    'title': obj.properties.get('title', ''),
                    'concept': obj.properties.get('content', ''),
                    'role': obj.properties.get('role', '')
                })

            # 🔥 Debug print
            print("\n===== WEAVIATE USE CASES =====")
            print(use_cases)
            print("\n===== WEAVIATE CONCEPTS =====")
            print(concepts)

            return {"use_cases": use_cases, "concepts": concepts}
        except Exception as e:
            logging.error(f"Failed to retrieve related items from Weaviate: {e}")
            return {"use_cases": [], "concepts": []}

    def _query_llm(self, prompt):
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"LLM query failed: {e}")
            return "Failed to generate navigation options due to an internal error."

    def _parse_response(self, response):
        options = []
        for line in response.splitlines():
            if line.strip().startswith(tuple(str(i) for i in range(1, 10))):
                option = line.split('.', 1)[-1].strip()
                if option:
                    options.append(option)
        return options[:5]


    # -------------------------------------------------------------------------
    # Core: build clear prompt for LLM, integrating retrieved knowledge
    # -------------------------------------------------------------------------
    def _build_clear_prompt(self, user_role, completed_modules, long_term_summary, short_term_summary):
        # Step 1: build context
        user_context = self._build_user_context(user_role, long_term_summary, short_term_summary)

        # Step 2: embed and retrieve from Weaviate
        user_vector = self._embed_text(user_context)
        retrieved = self._retrieve_related_items(user_vector)

        # But now we IGNORE concepts entirely
        use_cases = retrieved["use_cases"]

        # Debug print to confirm Weaviate results
        print("\n========== WEAVIATE DEBUG ==========")
        print("USE CASES:", use_cases)
        print("====================================\n")

        # Step 3: Format use case info ONLY
        use_case_text = "\n".join(
            f"- {item['title']}: {item['application']}"
            for item in use_cases
        ) if use_cases else "None found"

        # =========================================
        # 🔥 New Prompt (only use cases, strong AI constraints)
        # =========================================
        full_prompt = f"""
You are an AI Learning Navigator. Your job is to recommend *AI-powered* tasks a non-technical user can learn.

IMPORTANT RULES:
- Format MUST be EXACTLY:
  1. <task> 
  2. <task> 
  3. <task> 
  4. <task>
  5. <task> 
- Keep <task> SHORT (2-4 words max)
- Each task MUST be inspired directly by the relevant use cases below
- Do NOT suggest generic business topics (e.g., project management, leadership)
- Make each suggestion UNIQUE and cover different aspects of AI usage
- Use verb phrases (e.g., "Summarize documents", "Analyze feedback", "Generate reports")

GOOD EXAMPLES:
1. Summarize documents 
2. Analyze customer feedback
3. Generate sales reports 
4. Create marketing content 
5. Automate data entry 


BAD EXAMPLES (too long):
1. How to use AI to summarize long documents for quick insights using AI

======= USER CONTEXT =======
Role: {user_role}
Completed modules: {', '.join(completed_modules) if completed_modules else "None"}
Long-term memory: {long_term_summary}
Short-term memory: {short_term_summary}

======= RELEVANT USE CASES (from Vector DB) =======
{use_case_text}

======= ACTION =======
Based on the user's role and the use cases above, generate EXACTLY 5 suggestions:

1. <task> 
2. <task> 
3. <task>
4. <task>
5. <task> 

Return ONLY the numbered list. No explanation.
"""

        # Debug print
        print("\n===== NAVIGATOR PROMPT =====\n")
        print(full_prompt)
        print("\n=============================\n")

        return full_prompt



    # -------------------------------------------------------------------------
    # Main function: get next learning options
    # ------------------------------------------------------------------------- 
    def get_next_learning_options(self, user_id, user_role, completed_modules):
        try:
            # Fetch summaries using SummaryAgent
            long_term_summary = self.summary_agent.get_long_term_summary(user_id)
            short_term_summary = self.summary_agent.get_short_term_summary(user_id)

            prompt = self._build_clear_prompt(
                user_role, completed_modules, long_term_summary, short_term_summary
            )
            response = self._query_llm(prompt)
            return self._parse_response(response)
        except Exception as e:
            logging.error(f"Failed to get next learning options: {e}")
            return ["Error generating learning options. Please try again later."]

def main():
    """Main function for testing NavigatorAgent"""
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']

    dotenv.load_dotenv()

    # Set up environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    postgres_conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

    llm_client = OpenAI(api_key=OPENAI_API_KEY)
    summary = SummaryAgent(postgres_conn, llm_client)
    
    # Sample data
    sample_user_id = "426b13de-66a6-4b45-8631-0ead896d7d54"
    sample_user_role = "Data Scientist"
    sample_completed_modules = ["Introduction to AI", "Machine Learning Basics"]

    # Initialize NavigatorAgent
    agent = NavigatorAgent(llm_client, summary)

    print("Getting next learning options...")
    options = agent.get_next_learning_options(
        user_id=sample_user_id,
        user_role=sample_user_role,
        completed_modules=sample_completed_modules
    )

    print("\nNext learning options:")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    
if __name__ == "__main__":
    main()