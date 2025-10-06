'''
a helper that decides whether to call OpenAI or Perplexity
'''
class LLMRouterService:
    def route_request(self, model, prompt):
        if model.lower() in ['openai', 'gpt-3', 'gpt-4']:
            openai_service = OpenAIService()
            return openai_service.query_openai(prompt)
        elif model.lower() == 'perplexity':
            perplexity_service = PerplexityService()
            return perplexity_service.query_perplexity(prompt)
        else:
            raise ValueError(f"Unsupported model: {model}")