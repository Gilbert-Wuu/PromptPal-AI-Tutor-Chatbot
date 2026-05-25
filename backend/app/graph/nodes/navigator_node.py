import logging
from ..state import PromptPalState


def make_navigator_node(navigator_agent):
    """
    Factory returning the navigator_node function.

    Reads short_term_summary, long_term_summary, and completed_modules from
    shared state — bypasses the internal summary_agent calls inside
    get_next_learning_options() that would cause 2 more redundant DB hits.

    Runs in parallel with follow_up_node after trainer_node completes.
    """

    def navigator_node(state: PromptPalState) -> dict:
        user_role = state["user_role"]
        short_term = state.get("short_term_summary", "")
        long_term = state.get("long_term_summary", "")
        completed_modules = state.get("completed_modules", [])

        try:
            # _build_clear_prompt internally embeds + searches Weaviate
            prompt = navigator_agent._build_clear_prompt(
                user_role, completed_modules, long_term, short_term
            )
            response = navigator_agent._query_llm(prompt)
            options = navigator_agent._parse_response(response)

            suggestions = [
                {"id": f"newtopic_{i}", "text": opt}
                for i, opt in enumerate(options, 1)
            ]
            return {"next_topic_suggestions": suggestions}

        except Exception as e:
            logging.error(f"[navigator_node] Failed: {e}")
            return {"next_topic_suggestions": []}

    return navigator_node
