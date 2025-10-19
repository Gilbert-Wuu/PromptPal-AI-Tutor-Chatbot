import os

import dotenv
import psycopg2
from openai import OpenAI
import logging

class SummaryAgent:
    def __init__(self, postgres_conn, llm_client: OpenAI):
        self.pg_conn = postgres_conn
        self.llm_client = llm_client

    def _fetch_interactions(self, user_id, limit=None):
        try:
            with self.pg_conn.cursor() as cur:
                query = (
                    "SELECT log, timestamp "
                    "FROM interactions "
                    "WHERE user_id = %s "
                    "ORDER BY timestamp DESC"
                )
                params = [user_id]
                if limit is not None:
                    try:
                        limit_val = int(limit)
                    except (TypeError, ValueError):
                        logging.warning("Invalid limit provided, ignoring limit.")
                        limit_val = None
                    if limit_val and limit_val > 0:
                        query += " LIMIT %s"
                        params.append(limit_val)

                cur.execute(query, tuple(params))
                results = cur.fetchall()
                return [{"log": r[0], "timestamp": r[1]} for r in results]
        except Exception as e:
            logging.error(f"PostgreSQL interaction fetch failed: {e}")
            return []

    def _compose_interaction_text(self, interactions):
        texts = []
        for item in interactions:
            log = item.get("log", "")
            timestamp = item.get("timestamp", "")
            texts.append(f"[{timestamp}] {log}")
        return "\n\n".join(texts)

    def _summarize_long_term(self, previous_summary, recent_interactions, max_tokens=1024):
        prompt = (
            "You are a learning platform assistant. Update the user's long-term learning summary based on their previous summary and recent interactions.\n\n"
            f"Previous Summary:\n{previous_summary}\n\n"
            f"Recent Interactions:\n{recent_interactions}\n\n"
            "Examples:\n"
            "This user has covered these main concepts, asked questions about user questions.\n\n"
            f"Action:\nUpdate the summary to reflect new learning, but keep it concise and cumulative (max {max_tokens} tokens).\n\n"
            "Review:\n"
            "Return your response as a plain text summary."
        )
        try:
            response = self.llm_client.responses.create(
                model="gpt-5-mini",
                input=prompt,
                max_output_tokens=max_tokens,
            )
            return response.output[0].content[0].text.strip()
        except Exception as e:
            logging.error(f"LLM long-term summarization failed: {e}")
            return "Summary generation failed due to an internal error."

    def _summarize_with_llm(self, text, summary_type, max_tokens=512):
        instructions = (
            f"You are a learning platform assistant. Your task is to generate a {summary_type} summary of the following user interactions.\n\n"
            "Context:\n"
            f"{text}\n\n"
            "Learning Objective:\n"
            f"Summarize the user's learning journey and key points discussed.\n\n"
            "Examples:\n"
            "Focus on main concepts, user questions, and agent responses.\n\n"
            "Action:\n"
            f"Create a concise summary (max {max_tokens} tokens).\n\n"
            "Review:\n"
            "Return your response as a plain text summary."
        )
        try:
            response = self.llm_client.responses.create(
                model="gpt-5-mini",
                input=instructions,
                max_output_tokens=max_tokens,
            )
            return response.output[0].content[0].text.strip()
        except Exception as e:
            logging.error(f"LLM summarization failed: {e}")
            return "Summary generation failed due to an internal error."


    def _fetch_long_term_summary(self, user_id):
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(
                    "SELECT long_term_summary FROM users WHERE user_id = %s",
                    (user_id,)
                )
                result = cur.fetchone()
                return result[0] if result else ""
        except Exception as e:
            logging.error(f"PostgreSQL long-term summary fetch failed: {e}")
            return ""

    def get_long_term_summary(self, user_id):
        return self._fetch_long_term_summary(user_id)

    def update_long_term_summary(self, user_id, num_recent=10, max_tokens=256):
        try:
            previous_summary = self._fetch_long_term_summary(user_id)
            interactions = self._fetch_interactions(user_id, limit=num_recent)
            interaction_text = self._compose_interaction_text(interactions)
            updated_summary = self._summarize_long_term(previous_summary, interaction_text, max_tokens=max_tokens)

            # Update summary in PostgreSQL
            with self.pg_conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET long_term_summary = %s WHERE user_id = %s",
                    (updated_summary, user_id)
                )
                self.pg_conn.commit()
            return updated_summary
        except Exception as e:
            logging.error(f"Failed to update long-term summary: {e}")
            return ""

    def get_short_term_summary(self, user_id, max_tokens=512):
        interactions = self._fetch_interactions(user_id, limit=5)
        text = self._compose_interaction_text(interactions)
        return self._summarize_with_llm(text, "short-term", max_tokens=max_tokens)

# summary = SummaryAgent(postgres_conn)

import uuid


# def main():
#     dotenv.load_dotenv()
#
#     # Set up environment variables
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#
#     POSTGRES_HOST = os.getenv("POSTGRES_HOST")
#     POSTGRES_DB = os.getenv("POSTGRES_DB")
#     POSTGRES_USER = os.getenv("POSTGRES_USER")
#     POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
#     POSTGRES_PORT = os.getenv("POSTGRES_PORT")
#     print(POSTGRES_PASSWORD)
#     print(POSTGRES_USER)
#
#     # Initialize dependencies
#     postgres_conn = psycopg2.connect(
#         dbname=POSTGRES_DB,
#         user=POSTGRES_USER,
#         password=POSTGRES_PASSWORD,
#         host=POSTGRES_HOST,
#         port=POSTGRES_PORT
#     )
#
#     lllm_client = OpenAI(api_key=OPENAI_API_KEY)
#     sample_user_id = uuid.UUID("426b13de-66a6-4b45-8631-0ead896d7d54")
#
#     agent = SummaryAgent(postgres_conn, lllm_client)
#
#     print("Short-term summary:")
#     short_summary = agent.get_short_term_summary(sample_user_id)
#     print(short_summary)
#
#     print("\nLong-term summary:")
#     long_summary = agent.get_long_term_summary(sample_user_id)
#     print(long_summary)
#
#     print("\nUpdating long-term summary...")
#     updated_summary = agent.update_long_term_summary(sample_user_id)
#     print("Updated long-term summary:")
#     print(updated_summary)
#
#
# if __name__ == "__main__":
#     main()
