from fastapi import FastAPI, HTTPException
from openai import OpenAI

from backend.app.agents import summary_agent, trainer_agent, navigator_agent, assessment_agent, curation_agent
from weaviate import Client
import psycopg2
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()


# Set up environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Initialize dependencies
weaviate_client = Client("http://localhost:8080")
postgres_conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT
)

llm_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize agents
summary = summary_agent.SummaryAgent(postgres_conn, llm_client)
curation = curation_agent.CurationAgent(llm_client)
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