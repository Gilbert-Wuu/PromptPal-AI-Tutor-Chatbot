import re
import psycopg2
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import weaviate
import logging
import os
from openai import OpenAI
from pydantic import BaseModel


class Citation(BaseModel):
    id: int
    url: str


class Summary(BaseModel):
    citations: List[Citation]
    summary: str


class TrainerAgent:
    def __init__(self, postgres_client, weaviate_client, summary_agent, llm_client, llm_model, config, grounding_tool,
                 openai_client=None, openai_model="gpt-4"):
        self.postgres_client = postgres_client
        self.weaviate_client = weaviate_client
        self.summary_agent = summary_agent
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.config = config
        self.grounding_tool = grounding_tool
        self.openai_client = openai_client
        self.openai_model = openai_model

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

    def _search_user_documents(self, query, document_ids, limit=5):
        """Search user's uploaded documents in Weaviate"""
        try:
            print(f"Searching for user documents: {document_ids}")

            if hasattr(self.weaviate_client, 'collections'):
                # ===== Weaviate v4 client =====
                print("Using Weaviate v4 client")
                user_doc_collection = self.weaviate_client.collections.get("UserDocument")

                results = user_doc_collection.query.near_text(
                    query=query,
                    limit=limit * 3,
                    return_properties=["chunk_text", "filename", "chunk_index", "document_id"]
                )

                filtered_results = []
                for obj in results.objects:
                    props = obj.properties
                    doc_id = props.get("document_id", "")

                    if doc_id in document_ids:
                        filtered_results.append({
                            "title": f"{props.get('filename', 'Document')} (Chunk {props.get('chunk_index', 0)})",
                            "content": props.get("chunk_text", ""),
                            "tags": [props.get("filename", "")],
                            "type": "user_document"
                        })

                        if len(filtered_results) >= limit:
                            break

                print(f"Found {len(filtered_results)} relevant chunks from user documents (v4)")
                return filtered_results
            else:
                # ===== Weaviate v3 client =====
                print("Using Weaviate v3 client")

                # Build where filter for document IDs
                where_filter = {
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["document_id"],
                            "operator": "Equal",
                            "valueText": doc_id
                        }
                        for doc_id in document_ids
                    ]
                }

                # Query Weaviate v3
                result = (
                    self.weaviate_client.query
                    .get("UserDocument", ["content", "filename", "chunk_index", "document_id"])
                    .with_near_text({"concepts": [query]})
                    .with_where(where_filter)
                    .with_limit(limit)
                    .do()
                )

                # Extract results
                filtered_results = []
                if "data" in result and "Get" in result["data"] and "UserDocument" in result["data"]["Get"]:
                    for item in result["data"]["Get"]["UserDocument"]:
                        filtered_results.append({
                            "title": f"{item.get('filename', 'Document')} (Chunk {item.get('chunk_index', 0)})",
                            "content": item.get("chunk_text", ""),
                            "tags": [item.get("filename", "")],
                            "type": "user_document"
                        })

                print(f"Found {len(filtered_results)} relevant chunks from user documents (v3)")
                return filtered_results

        except Exception as e:
            logging.error(f"Error searching user documents: {e}")
            print(f"Error searching user documents: {e}")
            return []

    def _search_knowledge_base(self, user_id, user_role, query, short_term, long_term):
        """
        Enhanced RAG search:
        - If query relates to Prompt Engineering → PromptGuide is prioritized
        - Otherwise search CoreConcept + PromptGuide with weighted scoring
        """

        try:
            print("\n🔍 Enhanced RAG Knowledge Base Search")

            # --- Identify user intent ---
            prompt_keywords = [
                "prompt engineering", "prompt", "use AI tools", "comparing",
                "few-shot", "Key principles", "context", "copilot", "rag prompt"
            ]

            is_prompt_query = any(k in query.lower() for k in prompt_keywords)

            # --- Get collections ---
            concept_collection = self.weaviate_client.collections.get("CoreConcept")
            prompt_collection = self.weaviate_client.collections.get("PromptGuide")

            # --- Build combined query text ---
            combined_query = " ".join([
                query or "",
                short_term or "",
                long_term or "",
            ])

            # -------------------------
            # CASE 1: Prompt Query → ONLY PromptGuide
            # -------------------------
            if is_prompt_query:
                print("  → Detected prompt-engineering intent. Prioritizing PromptGuide.")

                guide_results = prompt_collection.query.near_text(
                    query=combined_query,
                    limit=10  # get more since it's single source
                )

                learning_content = []
                for obj in guide_results.objects:
                    props = obj.properties
                    # FIX: Handle None distance
                    distance = getattr(obj.metadata, 'distance', None) if hasattr(obj, 'metadata') else None
                    score = distance if distance is not None else 0.5

                    learning_content.append({
                        "title": props.get("title", "Prompt Engineering Guide"),
                        "content": props.get("content"),
                        "tags": props.get("tags", []),
                        "type": "prompt_guide",
                        "score": score  # lower score = better
                    })
                return learning_content

            # -------------------------
            # CASE 2: Normal query → MIX CoreConcept + PromptGuide (with weights)
            # -------------------------
            concept_results = concept_collection.query.near_text(
                query=combined_query,
                limit=5
            )

            guide_results = prompt_collection.query.near_text(
                query=combined_query,
                limit=5
            )

            # Weighted scoring
            def normalize_score(distance):
                """Convert Weaviate cosine distance into 0-1 relevancy"""
                if distance is None:
                    return 0.5  # default mid-range score if distance unavailable
                return max(0.0001, 1 - distance)  # avoid 0

            learning_content = []

            # --- Core Concepts（normal weight = 1.0）---
            for obj in concept_results.objects:
                props = obj.properties
                # FIX: Safe distance extraction
                distance = getattr(obj.metadata, 'distance', None) if hasattr(obj, 'metadata') else None
                score = normalize_score(distance)
                learning_content.append({
                    "title": props.get("title"),
                    "content": props.get("content"),
                    "tags": props.get("tags", []),
                    "type": "core_concept",
                    "weighted_score": score * 1.0
                })

            # --- PromptGuide（boost = 1.4x weight）---
            for obj in guide_results.objects:
                props = obj.properties
                # FIX: Safe distance extraction
                distance = getattr(obj.metadata, 'distance', None) if hasattr(obj, 'metadata') else None
                score = normalize_score(distance)
                learning_content.append({
                    "title": props.get("title", "Prompt Engineering Guide"),
                    "content": props.get("content"),
                    "tags": props.get("tags", []),
                    "type": "prompt_guide",
                    "weighted_score": score * 1.4  # BOOST HERE
                })

            # --- Sort by weighted scores ---
            learning_content = sorted(
                learning_content,
                key=lambda x: x["weighted_score"],
                reverse=True
            )

            # Return top 5
            return learning_content[:5]

        except Exception as e:
            print(f"✗ Error in enhanced KB search: {e}")
            import traceback
            traceback.print_exc()
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

    def generate_learning_content(self, user_id, user_role, query, selected_document_ids=None):
        """Generate comprehensive learning response using RAG approach"""
        try:
            # Get user summaries
            long_term = self.summary_agent.get_long_term_summary(user_id)
            short_term = self.summary_agent.get_short_term_summary(user_id)

            # Determine which source to search
            results = []

            # If user selected documents, search their documents
            if selected_document_ids:
                print(f"Searching {len(selected_document_ids)} selected user documents")
                results = self._search_user_documents(query, selected_document_ids, limit=5)
                print(f"✅ Found {len(results)} chunks from user documents")

            # If no results from user documents, or no documents selected, search knowledge base
            if not results:
                print("Searching general knowledge base")
                results = self._search_knowledge_base(
                    user_id=user_id,
                    user_role=user_role,
                    query=query,
                    short_term=short_term,
                    long_term=long_term
                )
                print(f"✅ Found {len(results)} results from knowledge base")

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
            prompt_keywords = [
                "prompt", "prompt engineering", "few-shot", "zero-shot",
                "instruction", "rewrite", "system prompt", "copilot"
            ]
            is_prompt_query = any(k in query.lower() for k in prompt_keywords)

            if is_prompt_query:
                prompt = self._build_promptcoach_prompt(user_role, query, learning_content)
            else:
                prompt = self._build_clear_prompt(user_role, query, short_term, long_term, learning_content)

            try:
                # FIX: Correct Gemini API format - use string directly, not list of dicts
                response = self.llm_client.models.generate_content(
                    model=self.llm_model,
                    contents=prompt,  # Pass string directly
                    config=self.config
                )

                conversational_response = response.text
            except Exception as e:
                logging.error(f"LLM response generation failed: {e}")
                import traceback
                traceback.print_exc()
                conversational_response = (
                    "I'm sorry — I ran into a technical issue generating your AI learning answer. "
                    "Please try again in a moment!"
                )
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
            import traceback
            traceback.print_exc()
            return {
                "user_id": user_id,
                "role": user_role,
                "query": query,
                "error": str(e),
                "conversational_response": "I'm sorry, I encountered an error while processing your request."
            }

    def add_citations(self, response):
        text = response.text
        supports = response.candidates[0].grounding_metadata.grounding_supports
        chunks = response.candidates[0].grounding_metadata.grounding_chunks

        # Sort supports by end_index in descending order to avoid shifting issues when inserting.
        sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

        for support in sorted_supports:
            end_index = support.segment.end_index
            if support.grounding_chunk_indices:
                # Create citation string like [1](link1)[2](link2)
                citation_links = []
                for i in support.grounding_chunk_indices:
                    if i < len(chunks):
                        uri = chunks[i].web.uri
                        citation_links.append(f"[{i + 1}]({uri})")

                citation_string = ", ".join(citation_links)
                text = text[:end_index] + citation_string + text[end_index:]

        return text

    def generate_follow_up_questions(self, user_id: str, user_role: str, current_topic: str,
                                     lesson_content: str) -> list:
        """Generate 3 follow-up questions to dive deeper into current topic"""
        try:
            # Get user context
            long_term = self.summary_agent.get_long_term_summary(user_id)
            short_term = self.summary_agent.get_short_term_summary(user_id)

            prompt = f"""
    You are an AI learning assistant. The user just learned about: "{current_topic}"

    User role: {user_role}
    Recent learning: {short_term}
    Learning history: {long_term}

    Lesson content summary:
    {lesson_content[:500]}...

    Generate EXACTLY 3 short, actionable follow-up prompts (5-6 words each) that help the user dive deeper into this topic.

    Requirements:
    - Each prompt should be 5-6 words maximum
    - Focus on practical, role-specific applications
    - Use imperative or noun phrases (not full questions)
    - Be specific to what they just learned

    Format:
    1. <short prompt>
    2. <short prompt>
    3. <short prompt>

    Good examples:
    1. Implement churn prediction model
    2. Common ML pitfalls to avoid
    3. Real-world customer retention examples

    Bad examples (too long):
    1. How can I implement this machine learning approach in my sales workflow?
    2. What are some of the common mistakes that I should avoid?

    Return ONLY the 3 numbered questions, nothing else.
    """

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )

            text = response.choices[0].message.content
            print(f"✅ Follow-up questions response:\n{text}")

            # Parse response
            questions = []
            for line in text.strip().split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove number prefix
                    question = line.split('.', 1)[-1].strip()
                    if question:
                        questions.append({
                            "id": f"followup_{len(questions) + 1}",
                            "text": question
                        })

            return questions[:3]

        except Exception as e:
            logging.error(f"Error generating follow-up questions: {e}")
            # Fallback
            topic_words = current_topic.split()[:3]  # Take first 3 words
            topic_short = " ".join(topic_words)

            return [
                {"id": "followup_1", "text": f"Deep dive into {topic_short}"},
                {"id": "followup_2", "text": f"Practical {topic_short} examples"},
                {"id": "followup_3", "text": f"Common {topic_short} mistakes"}
            ]

    def update_user_learning_progress(self, user_id: str, completed_module: str) -> bool:
        """Update user's learning progress when they complete a module"""
        cursor = self.postgres_client.cursor()
        try:
            # Use the helper function from init_database.sql
            cursor.execute("""
                SELECT add_completed_module(%s, %s)
            """, (user_id, completed_module))

            self.postgres_client.commit()
            return True

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
            # Fixed query - use interaction_id from interactions table
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
                    # PostgreSQL returns JSONB as list already
                    completed_modules = result[2] if isinstance(result[2], list) else []
                except (TypeError, ValueError):
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

    def _build_promptcoach_prompt(self, user_role, query, learning_content):
        """
        Prompt Engineering conversational coach:
        - short
        - interactive
        - uses CTA
        - uses retrieved PromptGuide content
        - NEVER uses CLEAR
        """

        content_str = ""
        for item in learning_content:
            content_str += f"- {item.get('content', '')}\n"

        prompt = f"""
    You are PromptCoach — a friendly, interactive assistant who helps users learn to use AI tools
(Copilot, ChatGPT, Gemini) AND helps them improve the prompts they give those tools.
    STYLE:
    - Conversational, helpful, concise (6–9 sentences)
    - No academic tone
    - No CLEAR methodology
    - Never ignore the user's question
    - Never teach prompt engineering instead of answering the question

    USER:
    - Role: {user_role}
    - Query: "{query}"

    RETRIEVED PROMPT ENGINEERING KNOWLEDGE:
    {content_str}

    INSTRUCTIONS:
    Create an interactive coaching-style response:
    1. ALWAYS answer the user's actual question FIRST.
       - Explain the tool or concept clearly
       - Give examples relevant to the user’s role
       - Use content retrieved from PromptGuide where helpful

    2. AFTER answering the question, THEN add a short prompt-engineering insight.
       - 1–2 sentences only
       - Explain how the user could delegate this task to AI more effectively
       - Reference PromptGuide content naturally
    
    3. Provide ONE ready-to-copy prompt based on the user's query.
       - Make it specific to the user’s role
       - Do NOT output a generic template
    
    4. End with ONE friendly CTA question.
        Now generate the PromptCoach response.
        """
        return prompt

def main():
    """Simplified main function for testing generate_follow_up_questions"""
    import dotenv
    dotenv.load_dotenv()

    # Set up environment variables
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Supabase PostgreSQL connection (already deployed)
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")

    print("🔧 Testing TrainerAgent with Document Selection...")
    print(f"   PostgreSQL (Supabase): {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"   Weaviate: {WEAVIATE_URL}")

    # Connect to Supabase PostgreSQL
    try:
        postgres_conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            sslmode='require'  # Supabase requires SSL
        )
        print("✅ Connected to Supabase PostgreSQL")
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return

    # Connect to Weaviate
    try:
        weaviate_client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            headers={"X-OpenAI-Api-Key": OPENAI_API_KEY} if OPENAI_API_KEY else None
        )
        print("✅ Connected to Weaviate")
    except Exception as e:
        print(f"❌ Weaviate connection error: {e}")
        postgres_conn.close()
        return

    # Initialize Gemini client (for main generation)
    try:
        from google import genai
        from google.genai import types
        
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        model = "gemini-2.5-pro"
        config = types.GenerateContentConfig(tools=[grounding_tool])
        
        print(f"✅ Gemini client initialized (model: {model})")
    except Exception as e:
        print(f"❌ Gemini client error: {e}")
        postgres_conn.close()
        return

    # Initialize OpenAI client
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"✅ OpenAI client initialized (model: gpt-4)")
    except Exception as e:
        print(f"❌ OpenAI client error: {e}")
        postgres_conn.close()
        return

    # Initialize SummaryAgent (needed for TrainerAgent)
    try:
        # Try relative import first, fallback to absolute
        try:
            from .summary_agent import SummaryAgent
        except ImportError:
            from summary_agent import SummaryAgent
        
        summary_agent = SummaryAgent(postgres_conn, openai_client)
        print("✅ SummaryAgent initialized")
    except Exception as e:
        print(f"❌ SummaryAgent initialization error: {e}")
        postgres_conn.close()
        return

    # Initialize TrainerAgent (minimal - no Weaviate needed for this test)
    try:
        # Create a minimal TrainerAgent with required parameters
        config = types.GenerateContentConfig()
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        
        trainer = TrainerAgent(
            postgres_client=postgres_conn,
            weaviate_client=weaviate_client,
            summary_agent=summary_agent,
            llm_client=gemini_client,  # Gemini for main generation
            llm_model=model,
            config=config,
            grounding_tool=grounding_tool,
            openai_client=openai_client,  # 🔥 OpenAI for follow-up questions
            openai_model="gpt-4"
        )
        print("✅ TrainerAgent initialized")
    except Exception as e:
        print(f"❌ TrainerAgent initialization error: {e}")
        postgres_conn.close()
        return

    # Test data
    test_user_id = "11cf9348-8507-4877-b324-d82eedf4c6b1"
    test_user_role = "Sales"
    
    # =========================================================================
    # TEST 1: List user's documents
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 1: Listing user's documents")
    print("="*60)
    
    cursor = postgres_conn.cursor()
    try:
        cursor.execute("""
            SELECT document_id, filename, file_type, upload_date
            FROM user_documents
            WHERE user_id = %s
            ORDER BY upload_date DESC
        """, (test_user_id,))
        
        documents = cursor.fetchall()
        
        if not documents:
            print("⚠️  No documents found for this user")
            print("   Please upload some documents first using the UI")
            cursor.close()
            postgres_conn.close()
            weaviate_client.close()
            return
        
        print(f"Found {len(documents)} document(s):\n")
        for i, doc in enumerate(documents, 1):
            doc_id, filename, file_type, upload_date = doc
            print(f"   {i}. {filename} ({file_type})")
            print(f"      ID: {doc_id}")
            print(f"      Uploaded: {upload_date}\n")
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        cursor.close()
        postgres_conn.close()
        weaviate_client.close()
        return
    finally:
        cursor.close()

    # =========================================================================
    # DEBUG: Check Weaviate data
    # =========================================================================
    print("\n" + "="*60)
    print("DEBUG: Checking Weaviate UserDocument data")
    print("="*60)

    if documents:
        print("\n" + "="*60)
        print("🔍 DEBUG: Checking Weaviate UserDocument data")
        print("="*60)

        selected_doc_ids = [documents[0][0]]  # First document ID

        try:
            # 🔥 使用 v4 API
            user_doc_collection = weaviate_client.collections.get("UserDocument")
            
            # 1. Get total count
            aggregate_result = user_doc_collection.aggregate.over_all(total_count=True)
            total_count = aggregate_result.total_count
            print(f"✅ Total UserDocument chunks in Weaviate: {total_count}")
            
            # 2. Get sample documents for selected document_id
            from weaviate.classes.query import Filter
            
            response = user_doc_collection.query.fetch_objects(
                filters=Filter.by_property("document_id").equal(selected_doc_ids[0]),
                limit=5,
                return_properties=["document_id", "filename", "chunk_index", "chunk_text"]
            )
            
            if response.objects:
                print(f"\n✅ Sample chunks for document {selected_doc_ids[0][:8]}...:\n")
                for obj in response.objects:
                    props = obj.properties
                    print(f"   - {props['filename']} (Chunk {props['chunk_index']})")
                    print(f"     Content preview: {props['chunk_text'][:100]}...\n")
            else:
                print(f"\n⚠️  No chunks found for document {selected_doc_ids[0]}")
                print(f"   Document might not be embedded yet")
                
        except Exception as e:
            print(f"❌ Error checking Weaviate data: {e}")
            import traceback
            traceback.print_exc()

    # =========================================================================
    # TEST 2: Generate learning content WITH selected documents
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 2: Generate learning content WITH selected documents")
    print("="*60)
    
    # Use the first document for testing
    selected_doc_ids = [documents[0][0]]  # Take first document ID
    test_query = "How can AI help with sales reporting?"
    
    print(f"   Query: {test_query}")
    print(f"   Selected documents: {documents[0][1]}")  # Show filename
    print(f"   Document IDs: {selected_doc_ids}\n")
    
    try:
        result_with_docs = trainer.generate_learning_content(
            user_id=test_user_id,
            user_role=test_user_role,
            query=test_query,
            selected_document_ids=selected_doc_ids
        )
        
        print("✅ Learning content generated WITH documents")
        print("\n📝 Response preview:")
        # response = result_with_docs.get("conversational_response", "")
        print(result_with_docs[:500] + "..." if len(result_with_docs) > 500 else result_with_docs)
        
        # Check if document content was used
        learning_content = result_with_docs.get("learning_content", [])
        print(f"\n📚 Learning content sources: {len(learning_content)} item(s)")
        for item in learning_content:
            print(f"   - {item.get('title', 'Untitled')} (type: {item.get('type', 'unknown')})")
        
    except Exception as e:
        print(f"❌ Error generating content with documents: {e}")
        import traceback
        traceback.print_exc()

    # =========================================================================
    # TEST 3: Generate learning content WITHOUT selected documents (baseline)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 3: Generate learning content WITHOUT selected documents (baseline)")
    print("="*60)
    
    print(f"   Query: {test_query}")
    print(f"   Selected documents: None\n")
    
    try:
        result_without_docs = trainer.generate_learning_content(
            user_id=test_user_id,
            user_role=test_user_role,
            query=test_query,
            selected_document_ids=None
        )
        
        print("✅ Learning content generated WITHOUT documents")
        print("\n📝 Response preview:")
        # response = result_without_docs.get("conversational_response", "")
        print(result_without_docs[:500] + "..." if len(result_without_docs) > 500 else result_without_docs)
        
        # Check sources
        learning_content = result_without_docs.get("learning_content", [])
        print(f"\n📚 Learning content sources: {len(learning_content)} item(s)")
        for item in learning_content:
            print(f"   - {item.get('title', 'Untitled')} (type: {item.get('type', 'unknown')})")
        
    except Exception as e:
        print(f"❌ Error generating content without documents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()