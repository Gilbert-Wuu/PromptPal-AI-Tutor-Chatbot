from urllib import response
from xmlrpc import client
from openai import OpenAI
import weaviate
import os

class NavigatorAgent:
    def __init__(self, model="gpt-4"):
        self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.weaviate_client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
        )

    # -------------------------------------------------------------------------
    # Helper: build user context from profile memory
    # -------------------------------------------------------------------------
    def _build_user_context(user_role, long_term, short_term):
        return f"""
        Role: {user_role}
        Long-term memory: {long_term}
        Short-term memory: {short_term}
        """
    
    # -------------------------------------------------------------------------
    # Helper: embed text using OpenAI embedding model
    # -------------------------------------------------------------------------
    def _embed_text(self, text):
        response = self.llm.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    # -------------------------------------------------------------------------
    # Helper: retrieve relevant AI Concepts + Use Cases from Weaviate
    # -------------------------------------------------------------------------
    def _retrieve_related_items(self, user_vector, top_k=3):
        # Search UseCases
        usecase_query = self.weaviate_client.query.get("UseCases", ["title", "application", "ai_concepts", "role"]) \
            .with_near_vector({"vector": user_vector}) \
            .with_limit(top_k) \
            .do()

        # Search AIConcepts
        concept_query = self.weaviate_client.query.get("AIConcepts", ["title", "concept", "role"]) \
            .with_near_vector({"vector": user_vector}) \
            .with_limit(top_k) \
            .do()

        return {
            "use_cases": usecase_query["data"]["Get"]["UseCases"],
            "concepts": concept_query["data"]["Get"]["AIConcepts"]
        }

    def _query_llm(self, prompt):
        response = self.llm.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=350,
            temperature=0.7,
        )
        return response.choices[0].message["content"]

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
        retrieved = self._retrieve_relevant_items(user_vector)

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
            "- If the user is learning about prompt engineering, suggest advanced prompt techniques or related use cases.\n"
            "- If a module is completed, suggest a practical exercise or a new concept that builds on it.\n\n"
            "A - Action:\n"
            "Generate 3 actionable, specific, and relevant next-step learning prompts. Each should be clear and tailored to the user's context. "
            "If the user is already engaged with a topic, it is valid to suggest 3 prompts that help them dive deeper.\n\n"
            "R - Review:\n"
            "Return the options as a numbered list. Each option should be a single sentence, actionable, and directly related to the user's learning journey.\n"
        )

    # -------------------------------------------------------------------------
    # Main function: get next learning options
    # ------------------------------------------------------------------------- 
    def get_next_learning_options(self, user_id, user_role, completed_modules):
        # Fetch summaries using SummaryAgent
        long_term_summary = self.summary_agent.get_long_term_summary(user_id)
        short_term_summary = self.summary_agent.get_short_term_summary(user_id)

        prompt = self._build_clear_prompt(
            user_role, completed_modules, long_term_summary, short_term_summary
        )
        response = self._query_llm(prompt)
        return self._parse_response(response)