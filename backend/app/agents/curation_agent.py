import requests
from pydantic import BaseModel
from typing import List

class CurationResponse(BaseModel):
    key_points: List[str]
    resources: List[str]

class CurationAgent(BaseModel):

    def __init__(self, perplexity_api_key, model="sonar-medium-online"):
        self.perplexity_api_key = perplexity_api_key
        self.model = model

    def curate_content(self, query):
        prompt = (
            f"You are a curation agent. Given the query: '{query}', "
            "perform a web search and extract:\n"
            "1. 3-5 key points that summarize the most important and up-to-date information.\n"
            "2. A list of high-quality resources (videos, blogs, podcasts) with their URLs that best illustrate the concept.\n"
            "Return your answer as:\n"
            "Key Points:\n- ...\n- ...\nResources:\n- [Title](URL) - Type (video/blog/podcast)\n"
        )
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return CurationResponse(key_points=[], resources=[])
        content = response.json()["choices"][0]["message"]["content"]

        # Simple parsing
        key_points = []
        resources = []
        in_key_points = False
        in_resources = False
        for line in content.splitlines():
            if line.strip().startswith("Key Points:"):
                in_key_points = True
                in_resources = False
                continue
            if line.strip().startswith("Resources:"):
                in_key_points = False
                in_resources = True
                continue
            if in_key_points and line.strip().startswith("-"):
                key_points.append(line.strip()[1:].strip())
            if in_resources and line.strip().startswith("-"):
                resources.append(line.strip()[1:].strip())
        return CurationResponse(key_points=key_points, resources=resources)
