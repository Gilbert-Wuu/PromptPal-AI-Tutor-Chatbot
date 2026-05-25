import logging
from ..state import PromptPalState


def make_follow_up_node(trainer_agent):
    """
    Factory returning the follow_up_node function.

    Reads short_term_summary and long_term_summary from shared state
    instead of calling summary_agent internally (removes 2 redundant calls).
    Runs in parallel with navigator_node after trainer_node completes.
    """

    def follow_up_node(state: PromptPalState) -> dict:
        user_role = state["user_role"]
        query = state["query"]
        short_term = state.get("short_term_summary", "")
        long_term = state.get("long_term_summary", "")
        lesson_content = state.get("conversational_response", "")[:500]

        prompt = f"""
You are an AI learning assistant. The user just learned about: "{query}"

User role: {user_role}
Recent learning: {short_term}
Learning history: {long_term}

Lesson content summary:
{lesson_content}...

Generate EXACTLY 3 short, actionable follow-up prompts (5-6 words each) that help the user dive deeper into this topic.

Requirements:
- Each prompt should be 5-6 words maximum
- Focus on practical, role-specific applications
- Use imperative or noun phrases (not full questions)
- Be specific to what they just learned

Format:
1. <short prompt>
2. <short prompt>
3. <short prompt>

Return ONLY the 3 numbered prompts, nothing else.
"""

        try:
            response = trainer_agent.openai_client.chat.completions.create(
                model=trainer_agent.openai_model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )
            text = response.choices[0].message.content

            questions = []
            for line in text.strip().split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    question = line.split(".", 1)[-1].strip()
                    if question:
                        questions.append({"id": f"followup_{len(questions) + 1}", "text": question})

            return {"follow_up_questions": questions[:3]}

        except Exception as e:
            logging.error(f"[follow_up_node] GPT-4 call failed: {e}")
            topic_words = query.split()[:3]
            topic_short = " ".join(topic_words)
            return {
                "follow_up_questions": [
                    {"id": "followup_1", "text": f"Deep dive into {topic_short}"},
                    {"id": "followup_2", "text": f"Practical {topic_short} examples"},
                    {"id": "followup_3", "text": f"Common {topic_short} mistakes"},
                ]
            }

    return follow_up_node
