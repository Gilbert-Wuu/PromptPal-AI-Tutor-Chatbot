import logging
from ..state import PromptPalState

PROMPT_KEYWORDS = [
    "prompt", "prompt engineering", "few-shot", "zero-shot",
    "instruction", "rewrite", "system prompt", "copilot",
]


def make_trainer_node(trainer_agent):
    """
    Factory returning the trainer_node function.

    Key difference from the old generate_learning_content():
    - Reads short_term_summary and long_term_summary directly from state
      (already fetched by fetch_summaries_node) instead of calling
      summary_agent again — removes 2 redundant DB + LLM calls per request.
    """

    def trainer_node(state: PromptPalState) -> dict:
        user_id = state["user_id"]
        user_role = state["user_role"]
        query = state["query"]
        short_term = state.get("short_term_summary", "")
        long_term = state.get("long_term_summary", "")
        selected_document_ids = state.get("selected_document_ids") or []

        # ── RAG search ────────────────────────────────────────────────────
        results = []
        if selected_document_ids:
            results = trainer_agent._search_user_documents(query, selected_document_ids, limit=5)
        if not results:
            results = trainer_agent._search_knowledge_base(query, short_term, long_term)

        if not results:
            learning_content = [{
                "title": f"Learning: {query}",
                "content": f"Based on your query about '{query}', a topic worth exploring for a {user_role}.",
                "tags": [],
                "type": "generated",
            }]
        else:
            learning_content = [
                {
                    "title": r.get("title"),
                    "content": r.get("content"),
                    "tags": r.get("tags", []),
                    "type": r.get("type"),
                }
                for r in results
            ]

        # ── Prompt selection & Gemini call ────────────────────────────────
        is_prompt_query = any(k in query.lower() for k in PROMPT_KEYWORDS)
        if is_prompt_query:
            prompt = trainer_agent._build_promptcoach_prompt(user_role, query, learning_content)
        else:
            prompt = trainer_agent._build_clear_prompt(user_role, query, short_term, long_term, learning_content)

        try:
            response = trainer_agent.llm_client.models.generate_content(
                model=trainer_agent.llm_model,
                contents=prompt,
                config=trainer_agent.config,
            )
            conversational_response = response.text
        except Exception as e:
            logging.error(f"[trainer_node] Gemini call failed: {e}")
            conversational_response = (
                "I'm sorry — I ran into a technical issue generating your answer. "
                "Please try again in a moment!"
            )

        trainer_agent._store_conversation(user_id, query, conversational_response)

        return {
            "conversational_response": conversational_response,
            "learning_content": learning_content,
        }

    return trainer_node
