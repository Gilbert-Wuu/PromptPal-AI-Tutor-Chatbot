"""
chat_graph.py — LangGraph graph factory for the /chat/ pipeline.

Graph shape (DAG):

    [fetch_summaries]
          │
       [trainer]
       /        \\
[follow_up]  [navigator]   ← parallel branches
       \\        /
     [save_module]
          │
         END

The parallel branches run concurrently (LangGraph fan-out) and merge
at save_module once both have written their respective state keys.
"""

from langgraph.graph import StateGraph, END

from .state import PromptPalState
from .nodes.summary_node import make_fetch_summaries_node
from .nodes.trainer_node import make_trainer_node
from .nodes.followup_node import make_follow_up_node
from .nodes.navigator_node import make_navigator_node
from .nodes.save_module_node import make_save_module_node

from ..agents.summary_agent import SummaryAgent
from ..agents.trainer_agent import TrainerAgent
from ..agents.navigator_agent import NavigatorAgent


def create_chat_graph(
    postgres_conn,
    weaviate_client,
    gemini_client,
    gemini_model,
    gemini_config,
    openai_client,
):
    """
    Build and compile the LangGraph chat pipeline.

    All agent dependencies are injected here via closures so each node
    remains a plain function (PromptPalState → dict).

    Returns a compiled LangGraph that accepts PromptPalState as input
    and returns the fully populated PromptPalState as output.
    """
    # ── Instantiate agents (shared across nodes) ─────────────────────────
    summary_agent = SummaryAgent(postgres_conn, openai_client)

    trainer_agent = TrainerAgent(
        postgres_client=postgres_conn,
        weaviate_client=weaviate_client,
        summary_agent=summary_agent,
        llm_client=gemini_client,
        llm_model=gemini_model,
        config=gemini_config,
        grounding_tool=None,
        openai_client=openai_client,
    )

    navigator_agent = NavigatorAgent(openai_client, summary_agent, weaviate_client)

    # ── Create node functions via factories ───────────────────────────────
    fetch_summaries = make_fetch_summaries_node(summary_agent, postgres_conn)
    trainer = make_trainer_node(trainer_agent)
    follow_up = make_follow_up_node(trainer_agent)
    navigator = make_navigator_node(navigator_agent)
    save_module = make_save_module_node(summary_agent)

    # ── Build the graph ───────────────────────────────────────────────────
    builder = StateGraph(PromptPalState)

    builder.add_node("fetch_summaries", fetch_summaries)
    builder.add_node("trainer", trainer)
    builder.add_node("follow_up", follow_up)
    builder.add_node("navigator", navigator)
    builder.add_node("save_module", save_module)

    builder.set_entry_point("fetch_summaries")
    builder.add_edge("fetch_summaries", "trainer")

    # Fan-out: trainer → both parallel nodes
    builder.add_edge("trainer", "follow_up")
    builder.add_edge("trainer", "navigator")

    # Fan-in: both parallel nodes → save_module (LangGraph waits for both)
    builder.add_edge("follow_up", "save_module")
    builder.add_edge("navigator", "save_module")

    builder.add_edge("save_module", END)

    return builder.compile()
