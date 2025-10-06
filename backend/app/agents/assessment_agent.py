import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
import json
import openai
import logging

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CORE_CONCEPT_COLLECTION = "CoreConcept"

class AssessmentRequest(BaseModel):
    userId: str
    sessionId: str
    query: str
    userProfile: dict
    learningContext: dict

class AssessmentResponse(BaseModel):
    responseId: str
    userId: str
    sessionId: str
    question: str
    options: List[str]
    correctOption: str
    explanation: str
    timestamp: str
    assessmentMode: bool = True

class AssessmentAgent:
    def __init__(self):
        import weaviate  # Lazy import to avoid circular dependency
        if "localhost" in WEAVIATE_URL or "127.0.0.1" in WEAVIATE_URL:
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080,
                headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
            )
        else:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=WEAVIATE_URL,
                auth_credentials=weaviate.Auth.api_key(WEAVIATE_API_KEY),
                headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
            )

    def fetch_core_concepts(self, topic, role):
        query = {
            "where": {
                "operator": "And",
                "operands": [
                    {"path": ["topic"], "operator": "Equal", "valueText": topic},
                    {"path": ["role"], "operator": "Equal", "valueText": role}
                ]
            },
            "limit": 5
        }
        results = self.client.collections.get(CORE_CONCEPT_COLLECTION).query.fetch_objects(query)
        concepts = [item.get("title", "") for item in results.get("objects", [])]
        return concepts

    def call_llm_for_question(self, topic, user_profile, learning_context, concepts):
        prompt = (
            "You are an expert assessment generator for an adaptive learning platform.\n\n"
            "Context:\n"
            f"- User profile: {json.dumps(user_profile)}\n"
            f"- Learning history: {json.dumps(learning_context)}\n"
            f"- Relevant concepts for topic \"{topic}\": {concepts}\n\n"
            "Learning Objective:\n"
            f"Generate a multiple-choice question for the topic \"{topic}\" tailored to the user's role and proficiency.\n\n"
            "Examples:\n"
            "Use the provided concepts as possible answer options.\n\n"
            "Action:\n"
            "Create one clear, challenging question with 4 answer options (one correct). Specify:\n"
            "- question\n"
            "- options (list)\n"
            "- correct_option (exact match from options)\n"
            "- explanation (why the correct option is right)\n\n"
            "Review:\n"
            "Return your response as a JSON object with keys: question, options, correct_option, explanation."
        )

        openai.api_key = OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.7
            )
            content = response.choices[0].message["content"]
            result = json.loads(content)
            return {
                "question": result.get("question", ""),
                "options": result.get("options", []),
                "correctOption": result.get("correct_option", ""),
                "explanation": result.get("explanation", "")
            }
        except Exception as e:
            logging.error(f"LLM question generation failed: {e}")
            return {
                "question": "Sorry, we could not generate a question at this time.",
                "options": [],
                "correctOption": "",
                "explanation": "An internal error occurred during question generation."
            }

    def generate_question(self, request: AssessmentRequest) -> AssessmentResponse:
        role = request.userProfile.get("role", "general")
        topic = request.query.split("for topic:")[-1].strip() if "for topic:" in request.query else request.query

        concepts = self.fetch_core_concepts(topic, role)
        llm_result = self.call_llm_for_question(topic, request.userProfile, request.learningContext, concepts)

        response = AssessmentResponse(
            responseId=str(uuid.uuid4()),
            userId=request.userId,
            sessionId=request.sessionId,
            question=llm_result["question"],
            options=llm_result["options"],
            correctOption=llm_result["correctOption"],
            explanation=llm_result["explanation"],
            timestamp=datetime.utcnow().isoformat(),
            assessmentMode=True
        )
        return response
