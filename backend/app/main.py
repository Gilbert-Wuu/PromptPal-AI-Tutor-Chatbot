from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from backend.app.agents import summary_agent, trainer_agent, navigator_agent, assessment_agent
import weaviate
import psycopg2
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()


# Set up environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Initialize dependencies
# Use Weaviate v4 API - connect to local instance
try:
    weaviate_client = weaviate.connect_to_local(
        host="localhost",
        port=8080
    )
    print("✓ Connected to Weaviate")
except Exception as e:
    print(f"⚠ Warning: Could not connect to Weaviate: {e}")
    print("  Weaviate features will be disabled")
    weaviate_client = None

postgres_conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT
)
print("✓ Connected to PostgreSQL")

llm_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize agents (handle case where Weaviate might not be available)
summary = summary_agent.SummaryAgent(postgres_conn, llm_client)
trainer = trainer_agent.TrainerAgent(weaviate_client, summary, None, llm_client) if weaviate_client else None
navigator = navigator_agent.NavigatorAgent(llm_client, summary)
assessment = assessment_agent.AssessmentAgent()

app = FastAPI()

# CORS Middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ============================================
# AUTH ENDPOINTS
# ============================================

@app.post("/auth/signup")
async def signup(data: dict):
    """Create a new user account"""
    try:
        email = data.get("email")
        role = data.get("role")
        
        if not email or not role:
            raise HTTPException(status_code=400, detail="Email and role are required")
        
        cursor = postgres_conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            raise HTTPException(status_code=409, detail="User already exists")
        
        # Create new user
        cursor.execute(
            "INSERT INTO users (email, role) VALUES (%s, %s) RETURNING user_id, email, role, created_at",
            (email, role)
        )
        user = cursor.fetchone()
        postgres_conn.commit()
        cursor.close()
        
        return {
            "success": True,
            "user": {
                "user_id": str(user[0]),
                "email": user[1],
                "role": user[2],
                "created_at": user[3].isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        postgres_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(data: dict):
    """Login existing user"""
    try:
        email = data.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        cursor = postgres_conn.cursor()
        cursor.execute(
            "SELECT user_id, email, role, created_at FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update last login
        cursor = postgres_conn.cursor()
        cursor.execute(
            "UPDATE progress SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user[0],)
        )
        postgres_conn.commit()
        cursor.close()
        
        return {
            "success": True,
            "user": {
                "user_id": str(user[0]),
                "email": user[1],
                "role": user[2],
                "created_at": user[3].isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/user/{email}")
async def get_user(email: str):
    """Get user information by email"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute(
            """
            SELECT u.user_id, u.email, u.role, u.created_at, u.long_term_summary,
                   p.completed_modules, p.quiz_scores, p.last_login
            FROM users u
            LEFT JOIN progress p ON u.user_id = p.user_id
            WHERE u.email = %s
            """,
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": str(user[0]),
            "email": user[1],
            "role": user[2],
            "created_at": user[3].isoformat(),
            "long_term_summary": user[4],
            "completed_modules": user[5] if user[5] else [],
            "quiz_scores": user[6] if user[6] else {},
            "last_login": user[7].isoformat() if user[7] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CHAT ENDPOINTS (Frontend Integration)
# ============================================

@app.post("/chat/")
async def chat(data: dict):
    """Handle chat requests from frontend"""
    try:
        content = data.get("content")
        user_id = data.get("user_id")  # Optional, for logged-in users
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # For now, return a simple response with suggestions
        # You can integrate your trainer agent here
        return {
            "answer": f"I received your message: {content}. This is a placeholder response.",
            "suggestions": [
                "Tell me about prompt engineering",
                "How do I use AI for data analysis?",
                "Explain few-shot learning"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/topics/")
async def get_topics():
    """Get available quiz topics"""
    try:
        # Return some sample topics
        # You can integrate with your Weaviate database here
        return [
            {"id": "prompt_engineering", "name": "Prompt Engineering Basics"},
            {"id": "ai_concepts", "name": "AI Concepts"},
            {"id": "use_cases", "name": "Practical Use Cases"}
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))