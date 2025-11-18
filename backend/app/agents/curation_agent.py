import requests
from pydantic import BaseModel
from typing import List

class CurationResponse(BaseModel):
    key_points: List[str]
    resources: List[str]

class CurationAgent:
    """Agent for curating external content using Perplexity API"""

    def __init__(self, llm_client, model="sonar-medium-online"):
        self.llm_client = llm_client
        self.model = model
        # Perplexity API key is optional - if not available, use OpenAI fallback
        import os
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

    def curate_content(self, query):
        """Curate content for the given query"""
        prompt = (
            f"You are a curation agent. Given the query: '{query}', "
            "provide:\n"
            "1. 3-5 key points that summarize the most important information.\n"
            "2. A list of high-quality learning resources that would help understand this topic.\n"
            "Return your answer as:\n"
            "Key Points:\n- ...\n- ...\nResources:\n- [Title] - Type (video/article/tutorial)\n"
        )
        
        # If Perplexity API key available, use it for web search
        if self.perplexity_api_key:
            try:
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
                if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
                else:
                    # Fallback to OpenAI
                    content = self._use_openai_fallback(prompt)
            except Exception as e:
                print(f"Perplexity API error: {e}")
                content = self._use_openai_fallback(prompt)
        else:
            # Use OpenAI as fallback
            content = self._use_openai_fallback(prompt)

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
    
    def _use_openai_fallback(self, prompt):
        """Fallback to OpenAI if Perplexity is not available"""
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI fallback error: {e}")
            return "Key Points:\n- Unable to generate content\nResources:\n- N/A"
