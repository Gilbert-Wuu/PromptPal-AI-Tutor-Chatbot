import logging
from ..state import PromptPalState


def make_fetch_summaries_node(summary_agent, postgres_conn):
    """
    Factory that returns the fetch_summaries_node function.
    Closes over the agent + connection so the node is a plain callable.

    Fetches short-term summary, long-term summary, and completed_modules
    ONCE per request and places them in shared state. All downstream nodes
    (trainer, follow_up, navigator) read from state instead of re-querying
    the database — eliminating the 6x redundant DB calls in the old flow.
    """

    def fetch_summaries_node(state: PromptPalState) -> dict:
        user_id = state["user_id"]

        short_term = summary_agent.get_short_term_summary(user_id)
        long_term = summary_agent.get_long_term_summary(user_id)

        try:
            cursor = postgres_conn.cursor()
            cursor.execute(
                "SELECT completed_modules FROM progress WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            completed_modules = row[0] if row and row[0] else []
            cursor.close()
        except Exception as e:
            logging.error(f"[fetch_summaries_node] Failed to fetch completed_modules: {e}")
            completed_modules = []

        return {
            "short_term_summary": short_term,
            "long_term_summary": long_term,
            "completed_modules": completed_modules,
        }

    return fetch_summaries_node
