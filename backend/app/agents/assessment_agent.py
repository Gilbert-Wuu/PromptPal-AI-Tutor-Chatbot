
from __future__ import annotations

import json
import dotenv
import asyncio
import re

from openai import OpenAI

dotenv.load_dotenv()


class AssessmentAgent:
    def __init__(self, llm_client: OpenAI, postgres_conn):
        self.pg_conn = postgres_conn
        self.client = llm_client
        self.model = "gpt-5-mini"

    def _extract_response_text(self, response):
        """
        Extracts text from the LLM response object.
        """
        try:
            if response is None:
                return None

            # 1) SDK attribute: output_text
            if hasattr(response, "output_text") and response.output_text:
                return str(response.output_text).strip()

            # 2) SDK attribute: output (list/dict/str)
            if hasattr(response, "output") and response.output:
                out = response.output
                # list-like
                if isinstance(out, (list, tuple)) and len(out) > 0:
                    first = out[0]
                    # dict-like first item
                    if isinstance(first, dict):
                        content = first.get("content")
                        if isinstance(content, (list, tuple)) and len(content) > 0:
                            c0 = content[0]
                            if isinstance(c0, dict) and c0.get("text"):
                                return str(c0.get("text")).strip()
                        if first.get("text"):
                            return str(first.get("text")).strip()
                    elif isinstance(first, str):
                        return first.strip()
                    else:
                        # Try attribute-based extraction
                        content_attr = getattr(first, "content", None)
                        if isinstance(content_attr, (list, tuple)) and len(content_attr) > 0:
                            c0 = content_attr[0]
                            if isinstance(c0, dict) and c0.get("text"):
                                return str(c0.get("text")).strip()
                            if hasattr(c0, "text") and getattr(c0, "text"):
                                return str(getattr(c0, "text")).strip()
                        if hasattr(first, "text") and getattr(first, "text"):
                            return str(getattr(first, "text")).strip()
                # if output is plain string
                if isinstance(out, str) and out:
                    return out.strip()

            # 3) dict-like response (raw)
            if isinstance(response, dict):
                if response.get("output_text"):
                    return str(response.get("output_text")).strip()
                out = response.get("output")
                if out and isinstance(out, str):
                    return out.strip()

            # 4) Fallback: stringify
            return str(response).strip()
        except Exception as e:
            print(f"Failed to extract text from LLM response: {e}")
            return None

    async def create_quiz(self, topic: str, modules: str) -> dict | None:
        """
        Generates a 5-question multiple-choice quiz on a given topic.
        """
        # 1. Construct the prompt with strict JSON output instructions
        prompt = (
            f"You are a quiz generation assistant. Your task is to create a 5-question multiple-choice quiz.\n\n"
            "Topic:\n"
            f"{topic}\n\n"
            "Previous Modules that the test taker has completed:\n"
            f"{modules}\n"
            "Instructions:\n"
            "- The quiz must have exactly 5 questions.\n"
            "- Each question must have 4 options (a, b, c, d).\n"
            "- Indicate the correct answer for each question.\n"
            "- Your output MUST be a single, valid JSON object. Do not include any text before or after the JSON.\n\n"
            "JSON Format:\n"
            "{\n"
            f'  "topic": "{topic}",\n'
            '  "questions": [\n'
            '    {\n'
            '      "question_text": "...",\n'
            '      "options": { "a": "...", "b": "...", "c": "...", "d": "..." },\n'
            '      "correct_answer": "c",\n'
            '      "explanation": "..."\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            "Action:\n"
            "Generate the quiz following the exact format above."
        )

        # 2. Call OpenAI and parse the JSON response
        try:
            response = await asyncio.to_thread(
                self.client.responses.create,
                input=prompt,
                model=self.model
            )
            print("Raw response:", response.text)
            response_text = self._extract_response_text(response)
            if not response_text:
                print("❌ LLM returned empty response")
                return None

            print("Raw response:", response_text)

            # Clean up markdown code blocks if present
            if response_text.startswith("```"):
                response_text = re.sub(r"^```[a-zA-Z]*\s*", "", response_text)
                response_text = re.sub(r"\s*```$", "", response_text)

            print("Cleaned response:", response_text)
            return json.loads(response_text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ Assessment Agent failed to generate or parse quiz JSON: {e}")
            return None

    def _getModules(self, user_id: str) -> str:
        """
        Retrieves the list of modules completed by the user from PostgreSQL.
        """
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT completed_modules FROM progress WHERE user_id = %s",
                    (user_id,)
                )
                rows = cursor.fetchall()
                modules = [row[0] for row in rows]
                return ", ".join(modules)
        except Exception as e:
            print(f"❌ Failed to retrieve modules for user {user_id}: {e}")
            return ""


def main():
    import os
    import psycopg2

    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']

    dotenv.load_dotenv()

    # Set up environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    print(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")

    # Initialize dependencies
    postgres_conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT
    )

    llm_client = OpenAI(api_key=OPENAI_API_KEY)
    sample_user_id = "426b13de-66a6-4b45-8631-0ead896d7d54"

    agent = AssessmentAgent(llm_client)

    print("\n=== Testing Quiz Generation ===")

    # Get modules for the user
    modules = agent._getModules(sample_user_id)
    print(f"User completed modules: {modules}")

    # Generate a quiz
    topic = "Python basics"
    print(f"\nGenerating quiz on topic: {topic}")

    quiz = asyncio.run(agent.create_quiz(topic, modules))

    if quiz:
        print("\n✅ Quiz generated successfully:")
        print(json.dumps(quiz, indent=2))
    else:
        print("\n❌ Failed to generate quiz")

    postgres_conn.close()


if __name__ == "__main__":
    main()
