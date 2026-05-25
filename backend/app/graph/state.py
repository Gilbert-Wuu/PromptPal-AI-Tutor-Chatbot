from typing import TypedDict, List, Optional


class PromptPalState(TypedDict):
    # ── Inputs (set at request time) ──────────────────────────────────────
    user_id: str
    user_role: str
    query: str
    selected_document_ids: List[str]

    # ── From fetch_summaries_node (fetched once, shared by all later nodes) ─
    short_term_summary: str
    long_term_summary: str
    completed_modules: List[str]

    # ── From trainer_node ─────────────────────────────────────────────────
    learning_content: List[dict]
    conversational_response: str

    # ── From parallel nodes ───────────────────────────────────────────────
    follow_up_questions: List[dict]       # written by follow_up_node
    next_topic_suggestions: List[dict]    # written by navigator_node

    # ── From save_module_node ─────────────────────────────────────────────
    module_save_result: dict
