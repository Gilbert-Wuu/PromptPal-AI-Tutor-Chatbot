"""
Document Agent - Handles document ingestion, chunking, and RAG queries
"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timezone
import weaviate
from weaviate.classes.config import Configure, Property, DataType


class DocumentAgent:
    """Agent for managing document uploads and RAG queries"""
    
    def __init__(self, weaviate_client, postgres_conn, llm_client):
        self.weaviate_client = weaviate_client
        self.pg_conn = postgres_conn
        self.llm_client = llm_client
        self.collection_name = "UserDocument"
        
        # Initialize Weaviate collection if it doesn't exist
        if weaviate_client:
            self._initialize_collection()
    
    def _initialize_collection(self):
        try:
            if not self.weaviate_client.collections.exists(self.collection_name):
                self.weaviate_client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-small"
                    ),
                    properties=[
                        Property(name="user_id", data_type=DataType.TEXT),
                        Property(name="document_id", data_type=DataType.TEXT),
                        Property(name="filename", data_type=DataType.TEXT),
                        Property(name="chunk_text", data_type=DataType.TEXT),
                        Property(name="chunk_index", data_type=DataType.INT),
                        Property(name="upload_date", data_type=DataType.DATE),
                    ]
                )
        except Exception as e:
            print(f"Warning initializing collection: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 20) -> List[str]:
        words = text.split()
        chunks = []
        max_chars = 3000

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk) > max_chars:
                for j in range(0, len(chunk), max_chars - 200):
                    sub = chunk[j:j + max_chars]
                    if sub.strip():
                        chunks.append(sub)
            elif chunk.strip():
                chunks.append(chunk)

        return chunks
    
    def upload_document(self, user_id: str, filename: str, file_content: str,
                        file_type: str, file_size: int) -> Dict:

        try:
            document_id = str(uuid.uuid4())
            chunks = self.chunk_text(file_content)

            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_documents 
                (document_id, user_id, filename, file_type, file_size, status, chunk_count)
                VALUES (%s, %s, %s, %s, %s, 'active', %s)
                """,
                (document_id, user_id, filename, file_type, file_size, len(chunks))
            )
            self.pg_conn.commit()
            cursor.close()

            if self.weaviate_client:
                collection = self.weaviate_client.collections.get(self.collection_name)

                for idx, chunk in enumerate(chunks):
                    collection.data.insert({
                        "user_id": user_id,
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_text": chunk,
                        "chunk_index": idx,
                        "upload_date": datetime.now(timezone.utc).isoformat()
                    })

            return {"success": True, "document_id": document_id, "chunk_count": len(chunks)}

        except Exception as e:
            self.pg_conn.rollback()
            return {"success": False, "error": str(e)}
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                SELECT document_id, filename, file_type, file_size, 
                       upload_date, status, chunk_count
                FROM user_documents
                WHERE user_id = %s AND status = 'active'
                ORDER BY upload_date DESC
                """,
                (user_id,)
            )

            docs = []
            for row in cursor.fetchall():
                docs.append({
                    "document_id": str(row[0]),
                    "filename": row[1],
                    "file_type": row[2],
                    "file_size": row[3],
                    "upload_date": row[4].isoformat() if row[4] else None,
                    "status": row[5],
                    "chunk_count": row[6]
                })

            cursor.close()
            return docs

        except Exception:
            return []
    
    def delete_document(self, document_id: str, user_id: str) -> Dict:
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                UPDATE user_documents
                SET status = 'deleted'
                WHERE document_id::text = %s AND user_id::text = %s AND status = 'active'
                RETURNING document_id
                """,
                (document_id, user_id)
            )
            result = cursor.fetchone()
            self.pg_conn.commit()
            cursor.close()

            if not result:
                return {"success": False, "message": "Not found"}

            if self.weaviate_client:
                collection = self.weaviate_client.collections.get(self.collection_name)
                collection.data.delete_many(
                    where={
                        "path": ["document_id"],
                        "operator": "Equal",
                        "valueText": document_id
                    }
                )

            return {"success": True}

        except Exception as e:
            self.pg_conn.rollback()
            return {"success": False, "error": str(e)}

    def query_documents(self, user_id: str, query: str, limit: int = 5) -> Dict:
        try:
            if not self.weaviate_client:
                return {
                    "answer": "Document search is not available (Weaviate not connected)",
                    "sources": []
                }

            collection = self.weaviate_client.collections.get(self.collection_name)

            # FIXED — 正確的 near_text 語法
            response = collection.query.near_text(
                query,
                where={
                    "path": ["user_id"],
                    "operator": "Equal",
                    "valueText": user_id
                },
                limit=limit
            )

            sources = []
            context_chunks = []

            for obj in response.objects:
                chunk = obj.properties.get("chunk_text")
                sources.append({
                    "filename": obj.properties.get("filename"),
                    "chunk_text": chunk[:200] + "...",
                    "chunk_index": obj.properties.get("chunk_index")
                })
                context_chunks.append(chunk)

            if context_chunks:
                context = "\n\n".join(context_chunks)
                prompt = f"""Based on the following documents, answer the question.

    Context:
    {context}

    Question: {query}

    Answer:"""

                llm_resp = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = llm_resp.choices[0].message.content
            else:
                answer = "I couldn't find relevant information in your uploaded documents."

            return {"answer": answer, "sources": sources, "context_found": bool(sources)}

        except Exception as e:
            return {"answer": f"Error querying documents: {str(e)}", "sources": []}


