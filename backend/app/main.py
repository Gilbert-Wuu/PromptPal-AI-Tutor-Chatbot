from datetime import datetime, timedelta
import uuid
import jwt

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from psycopg2._json import Json
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types

from backend.app.agents import summary_agent, trainer_agent, navigator_agent, assessment_agent, document_agent
import weaviate
import psycopg2
import os
import dotenv

# Load environment variables
# Load from project root .env file
dotenv.load_dotenv()

# Set up environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "168"))

google_api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=google_api_key)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
model = "gemini-2.5-pro"
config = types.GenerateContentConfig(tools=[grounding_tool])

# Initialize dependencies
# Use Weaviate v4 API - connect to local instance
try:
    weaviate_client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY} if OPENAI_API_KEY else None
    )
    print("Connected to Weaviate")
except Exception as e:
    print(f"Warning: Could not connect to Weaviate: {e}")
    print("  Weaviate features will be disabled")
    weaviate_client = None

postgres_conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT
)
print("Connected to PostgreSQL")

llm_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize agents (handle case where Weaviate might not be available)
summary = summary_agent.SummaryAgent(postgres_conn, llm_client)
trainer = trainer_agent.TrainerAgent(postgres_client=postgres_conn, weaviate_client=weaviate_client,
                                     summary_agent=summary, llm_client=client, llm_model=model, config=config,
                                     grounding_tool=grounding_tool) if weaviate_client else None
navigator = navigator_agent.NavigatorAgent(llm_client, summary, weaviate_client) if weaviate_client else None
assessment = assessment_agent.AssessmentAgent(llm_client, postgres_conn)
doc_agent = document_agent.DocumentAgent(weaviate_client, postgres_conn, llm_client) if weaviate_client else None

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
        if not trainer:
            raise HTTPException(status_code=503, detail="Trainer service is unavailable (Weaviate not connected)")

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
        user_id = data.get("user_id")
        topic = data.get("topic")
        response = await assessment.create_quiz(topic, assessment.getModules(user_id), user_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/navigate")
async def navigate_learning(data: dict):
    try:
        if not navigator:
            raise HTTPException(status_code=503, detail="Navigator service is unavailable (Weaviate not connected)")

        user_id = data.get("user_id")
        user_role = data.get("user_role")
        completed_modules = data.get("completed_modules", [])

        # Get raw navigator suggestions
        options = navigator.get_next_learning_options(
            user_id=user_id,
            user_role=user_role,
            completed_modules=completed_modules
        )

        # 💡 Format suggestions with "using AI"
        formatted = [f"How to {opt.lower()} using AI?" for opt in options]

        return {"next_steps": formatted}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ChatRequest(BaseModel):
    content: Optional[str] = None
    user_id: str
    user_role: str
    is_initial: bool = False
    selected_documents: Optional[list[str]] = None


class LoginRequest(BaseModel):
    email: str


class SignupRequest(BaseModel):
    email: str
    role: str


# ============================================
# AUTH ENDPOINTS
# ============================================

@app.post("/auth/signup")
async def signup(data: SignupRequest):
    """Create a new user account"""
    try:
        email = data.email
        role = data.role

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
        session_token = create_session_token(str(user[0]))

        return {
            "success": True,
            "user": {
                "user_id": str(user[0]),
                "email": user[1],
                "role": user[2],
                "created_at": user[3].isoformat()
            },
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception as e:
        postgres_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
async def login(data: LoginRequest):
    """Login existing user"""
    try:
        email = data.email

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
        session_token = create_session_token(str(user[0]))

        return {
            "success": True,
            "user": {
                "user_id": str(user[0]),
                "email": user[1],
                "role": user[2],
                "created_at": user[3].isoformat()
            },
            "session_token": session_token
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
            SELECT u.user_id,
                   u.email,
                   u.role,
                   u.created_at,
                   u.long_term_summary,
                   p.completed_modules,
                   p.quiz_scores,
                   p.last_login
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


def create_session_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
        "jti": str(uuid.uuid4())
    }
    print(payload)

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(token)
    cursor = postgres_conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (session_id, user_id, session_token, expires_at)
        VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO
        UPDATE SET
            session_token = EXCLUDED.session_token,
            expires_at = EXCLUDED.expires_at
            RETURNING session_id
        """,
        (str(uuid.uuid4()), user_id, token, payload["exp"])
    )
    print("Inserted session for user:", user_id)
    postgres_conn.commit()
    cursor.close()
    return token


def resolve_user_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid session token") from exc
    cursor = postgres_conn.cursor()
    cursor.execute(
        "SELECT user_id FROM sessions WHERE session_token = %s AND expires_at > NOW()",
        (token,)
    )
    row = cursor.fetchone()
    cursor.close()
    if not row:
        raise HTTPException(status_code=401, detail="Session expired or not found")
    return row[0]


@app.get("/auth/me")
async def auth_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ", 1)[1].strip()
    user_id = resolve_user_from_token(token)
    return {"user_id": user_id}


# ============================================
# CHAT ENDPOINTS (Frontend Integration)
# ============================================

@app.post("/chat/")
async def chat(data: ChatRequest):
    """Handle chat requests - integrate Trainer Agent and Navigator Agent"""
    try:
        content = data.content  # User's query or selected option
        user_id = data.user_id
        user_role = data.user_role
        is_initial = data.is_initial  # Frontend flag for initial request

        if not trainer:
            raise HTTPException(status_code=503, detail="Trainer agent not available")

        print(f"Chat request - User: {user_id}, Initial: {is_initial}, Query: {content[:50] if content else 'None'}...")

        # Case 1: Initial request (no content), return learning options only
        if is_initial or not content:
            print("Initial request - Getting learning options from Navigator...")

            try:
                # Get user's completed modules
                cursor = postgres_conn.cursor()
                cursor.execute(
                    "SELECT completed_modules FROM progress WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                completed_modules = result[0] if result and result[0] else []
                cursor.close()

                # Get learning options from Navigator (returns list of strings)
                options = navigator.get_next_learning_options(
                    user_id=user_id,
                    user_role=user_role,
                    completed_modules=completed_modules
                )

                # Format for frontend
                learning_options = [
                    {
                        "id": f"option_{i}",
                        "title": opt,
                    }
                    for i, opt in enumerate(options, 1)
                ]

                print(f"Got {len(learning_options)} learning options")

                return {
                    "answer": "Welcome! Please select a learning topic or enter your own question.",
                    "learning_options": learning_options,
                    "suggestions": [],
                    "sources": []
                }

            except Exception as e:
                print(f"Error getting initial options: {e}")
                import traceback
                traceback.print_exc()

                # Fallback options
                return {
                    "answer": "Welcome! Please select a learning topic to get started.",
                    "learning_options": [
                        {
                            "id": "option_1",
                            "title": "Prompt Engineering Basics"
                        },
                        {
                            "id": "option_2",
                            "title": "Core AI Concepts"
                        },
                        {
                            "id": "option_3",
                            "title": "Practical Applications"
                        }
                    ],
                    "suggestions": [],
                    "sources": []
                }

        # Case 2: User has selected an option or entered content
        print("Generating lesson with Trainer Agent...")

        # Check if user has selected documents
        selected_documents = data.selected_documents

        # Step 1: Use Trainer Agent to generate learning content
        trainer_response = trainer.generate_learning_content(
            user_id=user_id,
            user_role=user_role,
            query=content,
            selected_document_ids=selected_documents
        )

        lesson = trainer_response

        print(f"Lesson generated")

        # Step 2: Get next suggestions from Navigator
        suggestions = []
        try:
            print("Getting next suggestions from Navigator...")

            cursor = postgres_conn.cursor()
            cursor.execute(
                "SELECT completed_modules FROM progress WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            completed_modules = result[0] if result and result[0] else []
            cursor.close()

            # Get next learning options (returns list of strings)
            next_options = navigator.get_next_learning_options(
                user_id=user_id,
                user_role=user_role,
                completed_modules=completed_modules
            )

            # Format as suggestions (simple string format)
            suggestions = [
                {
                    "id": f"suggestion_{i}",
                    "text": opt
                }
                for i, opt in enumerate(next_options, 1)
            ]

            print(f"Got {len(suggestions)} suggestions")

        except Exception as e:
            print(f"Error getting suggestions: {e}")
            import traceback
            traceback.print_exc()

            # Fallback suggestions
            suggestions = [
                {"id": "suggestion_1", "text": "Continue learning this topic in depth"},
                {"id": "suggestion_2", "text": "Take a quiz to test understanding"},
                {"id": "suggestion_3", "text": "Explore related practical applications"}
            ]

        return {
            "answer": lesson,  # Lesson content from Trainer (string)
            "suggestions": suggestions,  # Next step suggestions from Navigator (list of dicts with id & text)
            "learning_options": []  # Only present in initial request
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topics/")
async def get_topics(user_id: str):
    """Get available quiz topics"""
    try:
        # Get completed modules from progress table
        cursor = postgres_conn.cursor()
        cursor.execute(
            "SELECT completed_modules FROM progress WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()

        completed_modules = result[0] if result and result[0] else []

        # Default topics
        topics = [
            {"id": "prompt_engineering", "topic": "Prompt Engineering Basics"},
            {"id": "ai_concepts", "topic": "AI Concepts"},
            {"id": "use_cases", "topic": "Practical Use Cases"}
        ]

        # Add completed modules as additional topics
        for module in completed_modules:
            topics.append({
                "id": module,
                "topic": module.replace("_", " ").title()
            })

        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class QuizScoreRequest(BaseModel):
    user_id: str
    topic: str
    score: int
    total_questions: int


@app.post("/api/quiz/score")
async def update_quiz_score(data: QuizScoreRequest):
    """Update quiz score in progress table"""
    try:
        user_id = data.user_id
        topic = data.topic
        score = data.score
        total_questions = data.total_questions

        cursor = postgres_conn.cursor()

        # Get current quiz_scores
        cursor.execute(
            "SELECT quiz_scores FROM progress WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        # Initialize quiz_scores dict
        quiz_scores = result[0] if result and result[0] else {}

        # Add/update the new score
        quiz_scores[topic] = {
            "score": score,
            "total": total_questions,
            "percentage": round((score / total_questions) * 100, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Update existing record - use Json() wrapper for JSONB
        cursor.execute(
            "UPDATE progress SET quiz_scores = %s WHERE user_id = %s",
            (Json(quiz_scores), user_id)
        )

        postgres_conn.commit()
        cursor.close()

        return {
            "success": True,
            "message": "Quiz score updated successfully",
            "quiz_scores": quiz_scores
        }

    except Exception as e:
        postgres_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================

@app.post("/api/documents/upload")
async def upload_document(data: dict):
    """Upload and process a document"""
    try:
        user_id = data.get("user_id")
        filename = data.get("filename")
        file_content = data.get("content")
        file_type = data.get("file_type", "text/plain")
        file_size = data.get("file_size", len(file_content))

        print(
            f"Upload request received: filename={filename}, user_id={user_id}, content_length={len(file_content) if file_content else 0}")

        if not all([user_id, filename, file_content]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        if not doc_agent:
            raise HTTPException(status_code=503, detail="Document service is unavailable (Weaviate not connected)")

        result = doc_agent.upload_document(
            user_id=user_id,
            filename=filename,
            file_content=file_content,
            file_type=file_type,
            file_size=file_size
        )

        if result["success"]:
            return result
        else:
            error_msg = result.get("error", result.get("message", "Unknown error"))
            print(f"Document upload failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload endpoint exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{user_id}")
async def get_user_documents(user_id: str):
    """Get all documents for a user"""
    try:
        if not doc_agent:
            raise HTTPException(status_code=503, detail="Document service is unavailable (Weaviate not connected)")

        documents = doc_agent.get_user_documents(user_id)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, user_id: str = None):
    """Delete a document"""
    try:
        print(f"Delete request: document_id={document_id}, user_id={user_id}")

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id query parameter is required")

        if not doc_agent:
            raise HTTPException(status_code=503, detail="Document service is unavailable (Weaviate not connected)")

        result = doc_agent.delete_document(document_id, user_id)
        if result["success"]:
            print(f"Document {document_id} deleted successfully")
            return result
        else:
            print(f"Delete failed: {result.get('message')}")
            raise HTTPException(status_code=404, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/query")
async def query_documents(data: dict):
    """Query user's documents using RAG"""
    try:
        user_id = data.get("user_id")
        query = data.get("query")
        limit = data.get("limit", 5)

        if not all([user_id, query]):
            raise HTTPException(status_code=400, detail="Missing user_id or query")

        if not doc_agent:
            raise HTTPException(status_code=503, detail="Document service is unavailable (Weaviate not connected)")

        result = doc_agent.query_documents(user_id, query, limit)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
