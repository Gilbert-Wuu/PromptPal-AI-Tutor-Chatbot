from fastapi import FastAPI, HTTPException
from app.agents import summary_agent, trainer_agent, navigator_agent, assessment_agent, curation_agent
from app.services.llm_router import LLMRouterService
from app.services.openai_service import OpenAIService
from app.services.perplexity_service import PerplexityService
from weaviate import Client
import psycopg2

# Initialize dependencies
weaviate_client = Client("http://localhost:8080")  # Example Weaviate client
postgres_conn = psycopg2.connect(
    dbname="your_db", user="your_user", password="your_password", host="localhost"
)
llm_client = OpenAIService()  # Replace with actual LLM client
perplexity_api_key = "your_perplexity_api_key"

# Initialize agents
summary = summary_agent.SummaryAgent(weaviate_client, postgres_conn)
curation = curation_agent.CurationAgent(perplexity_api_key)
trainer = trainer_agent.TrainerAgent(weaviate_client, summary, curation, llm_client)
navigator = navigator_agent.NavigatorAgent(llm_client, summary)
assessment = assessment_agent.AssessmentAgent()

app = FastAPI()

@app.get("/api/summary/{user_id}")
async def get_summary(user_id: str):
    try:
        long_term_summary = summary.get_long_term_summary(user_id)
        short_term_summary = summary.get_short_term_summary(user_id)
        return {"long_term_summary": long_term_summary, "short_term_summary": short_term_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/train")
async def train_agent(data: dict):
    try:
        response = trainer.generate_learning_content(
            user_id=data.get("user_id"),
            user_role=data.get("user_role"),
            query=data.get("query")
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assessment")
async def generate_assessment(data: dict):
    try:
        request = assessment_agent.AssessmentRequest(**data)
        response = assessment.generate_question(request)
        return response.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/curation")
async def curate_content(data: dict):
    try:
        query = data.get("query")
        response = curation.curate_content(query)
        return response.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/navigate")
async def navigate_learning(data: dict):
    try:
        user_id = data.get("user_id")
        user_role = data.get("user_role")
        completed_modules = data.get("completed_modules", [])
        options = navigator.get_next_learning_options(user_id, user_role, completed_modules)
        return {"next_steps": options}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))