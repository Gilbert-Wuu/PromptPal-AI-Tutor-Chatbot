import logging
from ..state import PromptPalState


def make_save_module_node(summary_agent):
    """
    Factory returning the save_module_node function.

    Join point after the parallel follow_up / navigator branches.
    Saves the user's query to completed_modules if semantically unique
    (cosine similarity < 0.75 vs. existing modules).
    """

    def save_module_node(state: PromptPalState) -> dict:
        user_id = state["user_id"]
        query = state["query"]

        try:
            result = summary_agent.save_completed_module(
                user_id=user_id,
                user_query=query,
                similarity_threshold=0.75,
            )
            return {"module_save_result": result}
        except Exception as e:
            logging.error(f"[save_module_node] Failed: {e}")
            return {"module_save_result": {"success": False, "message": str(e)}}

    return save_module_node
