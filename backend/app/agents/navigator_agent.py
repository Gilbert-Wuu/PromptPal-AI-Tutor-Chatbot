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
    def _retrieve_related_items(self, user_vector, top_k=3):
        try:
            if not user_vector:
                return {"use_cases": [], "concepts": []}

            if not self.weaviate_client:
                logging.warning("Weaviate client not available")
                return {"use_cases": [], "concepts": []}
        
            # Search UseCase
            usecase_collection = self.weaviate_client.collections.get("UseCase")
            usecase_query = usecase_collection.query.near_vector(
                near_vector=user_vector,
                limit=top_k
            )

            # Search CoreConcept
            concept_collection = self.weaviate_client.collections.get("CoreConcept")
            concept_query = concept_collection.query.near_vector(
                near_vector=user_vector,
                limit=top_k
            )
            
            # process results
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

            return {
                "use_cases": use_cases,
                "concepts": concepts
            }
        except Exception as e:
            logging.error(f"Failed to retrieve related items from Weaviate: {e}")
            return {"use_cases": [], "concepts": []}

    def _query_llm(self, prompt):
        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=350,
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
        return options[:3]

    # -------------------------------------------------------------------------
    # Core: build clear prompt for LLM, integrating retrieved knowledge
    # -------------------------------------------------------------------------
    def _build_clear_prompt(self, user_role, completed_modules, long_term_summary, short_term_summary):
        # Step 1: build context
        user_context = self._build_user_context(user_role, long_term_summary, short_term_summary)

        # Step 2: embed and retrieve from Weaviate
        user_vector = self._embed_text(user_context)
        retrieved = self._retrieve_related_items(user_vector)

        # Step 3: prepare contextual information
        use_cases = "\n".join(
            f"- Title: {item['title']}, Application: {item['application']}, "
            f"AI Concepts: {item['ai_concepts']}, Role: {item['role']}"
            for item in retrieved["use_cases"]
        ) if retrieved["use_cases"] else "No relevant use cases found."

        concepts = "\n".join(
            f"- Title: {item['title']}, Concept: {item['concept']}, Role: {item['role']}"
            for item in retrieved["concepts"]
        ) if retrieved["concepts"] else "No related AI concepts found."

        return (
            "You are an AI learning navigator for a corporate training platform. "
            "Follow the CLEAR methodology (Context, Learning objective, Examples, Action, Review) to suggest the next 3 learning options for the user.\n\n"
            "C - Context:\n"
            f"{user_context}\n\n"
            "Relevant Use Cases (from vector DB):\n"
            f"{use_cases}\n\n"
            "Related AI Concepts:\n"
            f"{concepts}\n"
            f"- User role: {user_role}\n"
            f"- Completed modules: {', '.join(completed_modules) if completed_modules else 'None'}\n"
            f"- Long-term learning summary: {long_term_summary}\n"
            f"- Short-term summary (recent focus): {short_term_summary}\n\n"
            "L - Learning Objective:\n"
            "Identify what the user should learn next to maximize their growth, based on their history and current focus. "
            "If the short-term summary shows a topic in progress, consider suggesting ways to deepen that topic.\n\n"
            "E - Examples:\n"
            "Good examples of learning options:\n"
            "1. How to craft effective prompts?\n"
            "2. What is predictive analytics?\n"
            "3. Build an AI customer chatbot\n\n"
            "Bad examples (too long, avoid these):\n"
            "1. Crafting prompts for an AI customer service chatbot to improve customer interactions.\n"
            "2. Designing prompts to refine predictive sales analytics for better business decisions.\n\n"
            "A - Action:\n"
            "Generate 3 SHORT, CLEAR learning options. Each option must be:\n"
            "- Maximum 5-6 words\n"
            "- Simple and actionable\n"
            "- Use question format when possible (How to...? What is...?)\n"
            "- Focus on ONE core concept per option\n"
            "- Avoid long explanations - be concise!\n\n"
            "R - Review:\n"
            "Return ONLY 3 short learning options as a numbered list. Each should be a brief, clear title that a user can immediately understand.\n"
            )

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