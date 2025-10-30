import re
import psycopg2
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import weaviate
import logging
import os
from openai import OpenAI

class TrainerAgent:
    def __init__(self, postgres_client, weaviate_client, summary_agent, llm_client, llm_model="gpt-4"):
        self.postgres_client = postgres_client
        self.weaviate_client = weaviate_client
        self.summary_agent = summary_agent
        self.llm_client = llm_client
        self.llm_model = llm_model

    def _is_content_rich(self, results):
        """Check if retrieved content is sufficient"""
        min_links = 1
        min_relevance = 0.5
        link_pattern = re.compile(r'https?://')
        links = 0
        for item in results:
            content = item.get("content", "") + " " + item.get("application", "")
            if link_pattern.search(content):
                links += 1
            if float(item.get("importance_score", 1)) < min_relevance:
                return False
        return links >= min_links

    def _build_clear_prompt(self, user_role, query, short_term, long_term, learning_content):
        """Build comprehensive prompt using CLEAR methodology"""
        # Format RAG content for context
        content_str = ""
        for item in learning_content:
            content_str += f"- {item.get('title', '')}: {item.get('content', '')}\n"
        
        prompt = (
            "You are an expert AI learning assistant. Use the CLEAR methodology (Context, Learning objective, Examples, Action, Review) to generate a helpful, conversational response for the user.\n\n"
            "C - Context:\n"
            f"- User role: {user_role}\n"
            f"- User query: {query}\n"
            f"- Short-term summary: {short_term}\n"
            f"- Long-term summary: {long_term}\n"
            f"- Retrieved content:\n{content_str}\n\n"
            "L - Learning Objective:\n"
            "Help the user understand the topic in their query, using both foundational knowledge and real-world examples. Tailor the explanation to their role and recent learning history.\n\n"
            "E - Examples:\n"
            "Include practical examples, links, or case studies from the retrieved content if available.\n\n"
            "A - Action:\n"
            "Write a clear, engaging, and concise response that teaches the concept, references the provided content, and encourages further exploration.\n\n"
            "R - Review:\n"
            "End with a summary or a follow-up question to keep the user engaged.\n"
        )
        return prompt

    def _search_knowledge_base(self, query, user_role, short_term, long_term):
        """Search Weaviate for relevant content - compatible with both v3 and v4 clients"""
        try:
            # Check if we have v4 client (with collections attribute)
            if hasattr(self.weaviate_client, 'collections'):
                # Weaviate v4 client
                try:
                    concept_collection = self.weaviate_client.collections.get("CoreConcept")
                    results = concept_collection.query.near_text(
                        query=[query, short_term, long_term],
                        where={"path": ["role"], "operator": "Equal", "valueText": user_role},
                        limit=5
                    )
                    
                    # Convert v4 results to expected format
                    formatted_results = []
                    for obj in results.objects:
                        props = obj.properties
                        formatted_results.append({
                            "content_id": props.get("content_id", ""),
                            "title": props.get("title", ""),
                            "content": props.get("content", ""),
                            "topic": props.get("topic", ""),
                            "role": props.get("role", ""),
                            "content_type": props.get("content_type", ""),
                            "tags": props.get("tags", []),
                            "importance_score": props.get("importance_score", 1.0)
                        })
                    return formatted_results
                except Exception:
                    # Fall through to v3 client if v4 fails
                    pass
            
            # Weaviate v3 client (original main.py uses this)
            try:
                results = self.weaviate_client.query.get(
                    "CoreConcept",
                    ["content_id", "title", "content", "topic", "role", "content_type", "tags", "importance_score"]
                ).with_near_text({
                    "concepts": [query, short_term, long_term]
                }).with_where({
                    "path": ["role"],
                    "operator": "Equal",
                    "valueText": user_role
                }).with_limit(5).do().get("data", {}).get("Get", {}).get("CoreConcept", [])
                return results if results else []
            except Exception as e:
                logging.error(f"Error with v3 client search: {e}")
                return []
                
        except Exception as e:
            logging.error(f"Error searching knowledge base: {e}")
            return []

    def _store_conversation(self, user_id, user_prompt, response_text):
        """Store conversation in interactions table"""
        cursor = self.postgres_client.cursor()
        try:
            conversation_log = f"User: {user_prompt}\nAI: {response_text}"
            cursor.execute(
                "INSERT INTO interactions (user_id, log, timestamp) VALUES (%s, %s, %s)",
                (user_id, conversation_log, datetime.now())
            )
            self.postgres_client.commit()
        except Exception as e:
            logging.error(f"Error storing conversation: {e}")
            self.postgres_client.rollback()
        finally:
            cursor.close()

    def generate_learning_content(self, user_id, user_role, query):
        """Generate comprehensive learning response using RAG approach"""
        try:
            # Get user summaries
            long_term = self.summary_agent.get_long_term_summary(user_id)
            short_term = self.summary_agent.get_short_term_summary(user_id)

            # Search knowledge base
            results = self._search_knowledge_base(query, user_role, short_term, long_term)

            # If no results found, create some basic learning content
            if not results:
                learning_content = [{
                    "title": f"Learning about: {query}",
                    "content": f"Based on your query about '{query}', this is a topic worth exploring for a {user_role}.",
                    "tags": [query.lower()],
                    "type": "generated"
                }]
            else:
                # Format learning content from search results
                learning_content = []
                for item in results:
                    learning_content.append({
                        "title": item.get("title"),
                        "content": item.get("content"),
                        "tags": item.get("tags", []),
                        "type": item.get("content_type")
                    })

            # Build prompt and generate response
            prompt = self._build_clear_prompt(user_role, query, short_term, long_term, learning_content)
            
            try:
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=600,
                    temperature=0.7,
                )
                conversational_response = response.choices[0].message.content
            except Exception as e:
                logging.error(f"LLM response generation failed: {e}")
                conversational_response = "I'm sorry, I'm having trouble generating a response right now. Please try again later."

            # Store conversation
            self._store_conversation(user_id, query, conversational_response)

            return {
                "user_id": user_id,
                "role": user_role,
                "query": query,
                "short_term_summary": short_term,
                "long_term_summary": long_term,
                "learning_content": learning_content,
                "conversational_response": conversational_response
            }

        except Exception as e:
            logging.error(f"Error in generate_learning_content: {e}")
            return {
                "user_id": user_id,
                "role": user_role,
                "query": query,
                "error": str(e),
                "conversational_response": "I'm sorry, I encountered an error while processing your request. Please try again later."
            }

    def update_user_learning_progress(self, user_id: str, completed_module: str) -> bool:
        """Update user's learning progress when they complete a module"""
        cursor = self.postgres_client.cursor()
        try:
            # Add completed module to progress
            cursor.execute("""
                UPDATE progress 
                SET completed_modules = 
                    CASE 
                        WHEN completed_modules @> to_jsonb(%s::text)
                        THEN completed_modules
                        ELSE completed_modules || to_jsonb(%s::text)
                    END,
                    last_login = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (completed_module, completed_module, user_id))
            
            self.postgres_client.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logging.error(f"Error updating learning progress: {e}")
            self.postgres_client.rollback()
            return False
        finally:
            cursor.close()

    def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics about user's learning progress"""
        cursor = self.postgres_client.cursor()
        try:
            # Get user progress and interaction count
            cursor.execute("""
                SELECT 
                    u.role,
                    u.created_at,
                    p.completed_modules,
                    p.last_login,
                    COUNT(i.interaction_id) as total_interactions
                FROM users u
                LEFT JOIN progress p ON u.user_id = p.user_id
                LEFT JOIN interactions i ON u.user_id = i.user_id
                WHERE u.user_id = %s
                GROUP BY u.user_id, u.role, u.created_at, p.completed_modules, p.last_login
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return {"error": "User not found"}
            
            # Handle JSONB data properly
            completed_modules = []
            if result[2]:
                try:
                    completed_modules = result[2] if isinstance(result[2], list) else json.loads(result[2])
                except (json.JSONDecodeError, TypeError):
                    completed_modules = []
            
            return {
                "user_role": result[0],
                "member_since": result[1],
                "total_interactions": result[4],
                "completed_modules": completed_modules,
                "modules_completed_count": len(completed_modules),
                "last_login": result[3],
                "learning_streak": self._calculate_learning_streak(user_id)
            }
            
        except Exception as e:
            logging.error(f"Error getting learning analytics: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()

    def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate user's learning streak (consecutive days with interactions)"""
        cursor = self.postgres_client.cursor()
        try:
            cursor.execute("""
                SELECT DATE(timestamp) as interaction_date
                FROM interactions 
                WHERE user_id = %s 
                ORDER BY timestamp DESC
                LIMIT 30
            """, (user_id,))
            
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            # Calculate consecutive days from most recent
            streak = 1
            current_date = dates[0]
            
            for i in range(1, len(dates)):
                previous_date = dates[i]
                if (current_date - previous_date).days == 1:
                    streak += 1
                    current_date = previous_date
                else:
                    break
            
            return streak
            
        except Exception as e:
            logging.error(f"Error calculating learning streak: {e}")
            return 0
        finally:
            cursor.close()

def main():
    """Main function for testing TrainerAgent"""
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
        
    import dotenv
    dotenv.load_dotenv()

    # Set up environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    print(f"🔧 Connecting to databases...")
    print(f"   PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"   Weaviate: {WEAVIATE_URL}")

    # Initialize dependencies with error handling
    postgres_conn = None
    weaviate_client = None
    
    try:
        postgres_conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        print("✅ PostgreSQL connected successfully")
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return

    try:
        weaviate_client = weaviate.connect_to_local()
        print("✅ Weaviate connected successfully")
    except Exception as e:
        print(f"❌ Weaviate connection error: {e}")
        if postgres_conn:
            postgres_conn.close()
        return

    try:
        llm_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Import and initialize other agents with fallback for standalone execution
        try:
            from .summary_agent import SummaryAgent
        except ImportError:
            from summary_agent import SummaryAgent
        
        summary = SummaryAgent(postgres_conn, llm_client)

        # Sample data
        sample_user_id = "426b13de-66a6-4b45-8631-0ead896d7d54"
        sample_user_role = "Data Scientist"
        sample_query = "What is machine learning and how does it work?"

        # Initialize TrainerAgent
        agent = TrainerAgent(postgres_conn, weaviate_client, summary, llm_client)

        print("🧪 Testing Trainer Agent Functionality...")
        print(f"User ID: {sample_user_id}")
        print(f"User Role: {sample_user_role}")
        print(f"Query: {sample_query}")
        print("-" * 60)

        # Test learning content generation
        response = agent.generate_learning_content(
            user_id=sample_user_id,
            user_role=sample_user_role,
            query=sample_query
        )

        print("✅ Learning content response generated:")
        print(f"Response keys: {list(response.keys())}")
        if "conversational_response" in response:
            print(f"Response preview: {response['conversational_response'][:200]}...")
        
        # Test learning analytics
        analytics = agent.get_learning_analytics(sample_user_id)
        print(f"✅ Learning analytics: {analytics}")
        
        # Test progress update
        progress_updated = agent.update_user_learning_progress(sample_user_id, "Machine Learning Basics")
        print(f"✅ Progress update result: {progress_updated}")

        print("🎉 Trainer agent test completed successfully!")
        
    finally:
        # Cleanup connections
        try:
            if postgres_conn:
                postgres_conn.close()
                print("🔧 PostgreSQL connection closed")
        except Exception as e:
            print(f"Warning: Error closing PostgreSQL connection: {e}")
        
        try:
            if weaviate_client:
                weaviate_client.close()
                print("🔧 Weaviate connection closed")
        except Exception as e:
            print(f"Warning: Error closing Weaviate connection: {e}")

if __name__ == "__main__":
    main()