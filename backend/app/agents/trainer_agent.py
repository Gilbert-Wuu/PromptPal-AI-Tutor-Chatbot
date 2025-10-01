import re

class TrainerAgent:
    def __init__(self, weaviate_client, summary_agent, curation_agent, llm_client, llm_model="gpt-4"):
        self.weaviate_client = weaviate_client
        self.summary_agent = summary_agent
        self.curation_agent = curation_agent
        self.llm_client = llm_client
        self.llm_model = llm_model

    def _is_content_rich(self, results):
        min_links = 1
        min_relevance = 0.5
        link_pattern = re.compile(r'https?://')
        links = 0
        for item in results:
            content = item.get("content", "") + " " + item.get("application", "")
            if link_pattern.search(content):
                links += 1
            if float(item.get("importance_score", 1)) < min_relevance:
                return False
        return links >= min_links

    def _store_curated_content(self, curated, user_role, query):
        for idx, point in enumerate(curated.key_points):
            self.weaviate_client.collections.get("CoreConcept").data.insert({
                "content_id": f"curated_{hash(point)}",
                "title": f"Curated: {query} (Point {idx+1})",
                "content": point,
                "topic": "curated",
                "role": user_role,
                "content_type": "concept",
                "tags": ["curated", query]
            })
        for res in curated.resources:
            self.weaviate_client.collections.get("CoreConcept").data.insert({
                "content_id": f"curated_{hash(res)}",
                "title": f"Curated Resource: {query}",
                "content": res,
                "topic": "curated",
                "role": user_role,
                "content_type": "resource",
                "tags": ["curated", "resource", query]
            })

    def _build_clear_prompt(self, user_role, query, short_term, long_term, learning_content):
        # Format RAG content for context
        content_str = ""
        for item in learning_content:
            content_str += f"- {item.get('title', '')}: {item.get('content', '')}\n"
        prompt = (
            "You are an expert AI learning assistant. Use the CLEAR methodology (Context, Learning objective, Examples, Action, Review) to generate a helpful, conversational response for the user.\n\n"
            "C - Context:\n"
            f"- User role: {user_role}\n"
            f"- User query: {query}\n"
            f"- Short-term summary: {short_term}\n"
            f"- Long-term summary: {long_term}\n"
            f"- Retrieved content:\n{content_str}\n\n"
            "L - Learning Objective:\n"
            "Help the user understand the topic in their query, using both foundational knowledge and real-world examples. Tailor the explanation to their role and recent learning history.\n\n"
            "E - Examples:\n"
            "Include practical examples, links, or case studies from the retrieved content if available.\n\n"
            "A - Action:\n"
            "Write a clear, engaging, and concise response that teaches the concept, references the provided content, and encourages further exploration.\n\n"
            "R - Review:\n"
            "End with a summary or a follow-up question to keep the user engaged.\n"
        )
        return prompt

    def generate_learning_content(self, user_id, user_role, query):
        long_term = self.summary_agent.get_long_term_summary(user_id)
        short_term = self.summary_agent.get_short_term_summary(user_id)

        results = self.weaviate_client.query.get(
            "CoreConcept",
            ["content_id", "title", "content", "topic", "role", "content_type", "tags", "importance_score"]
        ).with_near_text({
            "concepts": [query, short_term, long_term]
        }).with_where({
            "path": ["role"],
            "operator": "Equal",
            "valueText": user_role
        }).with_limit(5).do().get("data", {}).get("Get", {}).get("CoreConcept", [])

        if not self._is_content_rich(results):
            curated = self.curation_agent.curate_content(query)
            self._store_curated_content(curated, user_role, query)
            results = self.weaviate_client.query.get(
                "CoreConcept",
                ["content_id", "title", "content", "topic", "role", "content_type", "tags", "importance_score"]
            ).with_near_text({
                "concepts": [query, short_term, long_term]
            }).with_where({
                "path": ["role"],
                "operator": "Equal",
                "valueText": user_role
            }).with_limit(5).do().get("data", {}).get("Get", {}).get("CoreConcept", [])

        learning_content = []
        for item in results:
            learning_content.append({
                "title": item.get("title"),
                "content": item.get("content"),
                "tags": item.get("tags", []),
                "type": item.get("content_type")
            })

        prompt = self._build_clear_prompt(user_role, query, short_term, long_term, learning_content)
        response = self.llm_client.ChatCompletion.create(
            model=self.llm_model,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
        )
        conversational_response = response.choices[0].message["content"]

        return {
            "user_id": user_id,
            "role": user_role,
            "query": query,
            "short_term_summary": short_term,
            "long_term_summary": long_term,
            "learning_content": learning_content,
            "conversational_response": conversational_response
        }
