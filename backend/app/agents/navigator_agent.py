class NavigatorAgent:
    def __init__(self, llm_client, summary_agent, model="gpt-4"):
        self.llm_client = llm_client
        self.summary_agent = summary_agent
        self.model = model

    def get_next_learning_options(self, user_id, user_role, completed_modules):
        # Fetch summaries using SummaryAgent
        long_term_summary = self.summary_agent.get_long_term_summary(user_id)
        short_term_summary = self.summary_agent.get_short_term_summary(user_id)

        prompt = self._build_clear_prompt(
            user_role, completed_modules, long_term_summary, short_term_summary
        )
        response = self._query_llm(prompt)
        return self._parse_response(response)

    def _build_clear_prompt(self, user_role, completed_modules, long_term_summary, short_term_summary):
        return (
            "You are an AI learning navigator for a corporate training platform. "
            "Follow the CLEAR methodology (Context, Learning objective, Examples, Action, Review) to suggest the next 3 learning options for the user.\n\n"
            "C - Context:\n"
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

    def _query_llm(self, prompt):
        response = self.llm_client.ChatCompletion.create(
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
