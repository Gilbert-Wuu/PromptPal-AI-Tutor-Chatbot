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
        """Create Weaviate collection for user documents if it doesn't exist"""
        try:
            # Check if collection exists using exists() method
            if not self.weaviate_client.collections.exists(self.collection_name):
                # Create collection
                self.weaviate_client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(),
                    properties=[
                        Property(name="user_id", data_type=DataType.TEXT),
                        Property(name="document_id", data_type=DataType.TEXT),
                        Property(name="filename", data_type=DataType.TEXT),
                        Property(name="chunk_text", data_type=DataType.TEXT),
                        Property(name="chunk_index", data_type=DataType.INT),
                        Property(name="upload_date", data_type=DataType.DATE),
                    ]
                )
                print(f"Created Weaviate collection: {self.collection_name}")
            else:
                print(f"Weaviate collection '{self.collection_name}' already exists")
        except Exception as e:
            print(f"Warning: Could not initialize Weaviate collection: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 20) -> List[str]:
        """
        Split text into overlapping chunks
        chunk_size: number of words per chunk (reduced to stay under token limits)
        overlap: number of words to overlap between chunks
        """
        words = text.split()
        chunks = []
        max_chars = 3000  # Safety limit: ~750 tokens (1 token ≈ 4 chars)
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            
            # If chunk is too long, split it further by characters
            if len(chunk) > max_chars:
                # Split large chunk into smaller pieces
                for j in range(0, len(chunk), max_chars - 200):
                    sub_chunk = chunk[j:j + max_chars]
                    if sub_chunk.strip():
                        chunks.append(sub_chunk)
            elif chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def upload_document(self, user_id: str, filename: str, file_content: str, 
                       file_type: str, file_size: int) -> Dict:
        """
        Process and upload a document
        Returns: dict with status and document_id
        """
        try:
            print(f"Starting upload for '{filename}' (user: {user_id})")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Chunk the document
            chunks = self.chunk_text(file_content)
            print(f"Split into {len(chunks)} chunks")
            
            # Store metadata in PostgreSQL
            print(f"Storing metadata in PostgreSQL...")
            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_documents 
                (document_id, user_id, filename, file_type, file_size, status, chunk_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING document_id
                """,
                (document_id, user_id, filename, file_type, file_size, 'active', len(chunks))
            )
            self.pg_conn.commit()
            cursor.close()
            print(f"Saved metadata to PostgreSQL")
            
            # Store chunks in Weaviate if available
            if self.weaviate_client:
                print(f"Storing chunks in Weaviate...")
                collection = self.weaviate_client.collections.get(self.collection_name)
                
                for idx, chunk in enumerate(chunks):
                    collection.data.insert({
                        "user_id": user_id,
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_text": chunk,
                        "chunk_index": idx,
                        "upload_date": datetime.now(timezone.utc)
                    })
                print(f"Stored {len(chunks)} chunks in Weaviate")
            
            print(f"Upload complete for '{filename}'")
            return {
                "success": True,
                "document_id": document_id,
                "chunk_count": len(chunks),
                "message": f"Document '{filename}' uploaded successfully"
            }
            
        except Exception as e:
            print(f"Error in upload_document: {str(e)}")
            import traceback
            traceback.print_exc()
            self.pg_conn.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to upload document"
            }
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get all documents for a user"""
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
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "document_id": str(row[0]),
                    "filename": row[1],
                    "file_type": row[2],
                    "file_size": row[3],
                    "upload_date": row[4].isoformat() if row[4] else None,
                    "status": row[5],
                    "chunk_count": row[6]
                })
            
            cursor.close()
            return documents
            
        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []
    
    def delete_document(self, document_id: str, user_id: str) -> Dict:
        """Delete a document (soft delete in PostgreSQL, hard delete in Weaviate)"""
        try:
            print(f"Attempting to delete document_id={document_id}, user_id={user_id}")
            
            # Soft delete in PostgreSQL
            cursor = self.pg_conn.cursor()
            cursor.execute(
                """
                UPDATE user_documents 
                SET status = 'deleted'
                WHERE document_id::text = %s AND user_id::text = %s AND status = 'active'
                RETURNING document_id, filename
                """,
                (document_id, user_id)
            )
            result = cursor.fetchone()
            self.pg_conn.commit()
            cursor.close()
            
            if not result:
                print(f"Document not found in database")
                return {"success": False, "message": "Document not found or already deleted"}
            
            deleted_doc_id = str(result[0])
            filename = result[1]
            print(f"Marked document '{filename}' as deleted in PostgreSQL")
            
            # Delete from Weaviate if available
            if self.weaviate_client:
                try:
                    collection = self.weaviate_client.collections.get(self.collection_name)
                    deleted = collection.data.delete_many(
                        where={
                            "path": ["document_id"],
                            "operator": "Equal",
                            "valueText": document_id
                        }
                    )
                    print(f"Deleted chunks from Weaviate")
                except Exception as wv_error:
                    print(f"Weaviate delete warning: {wv_error}")
            
            print(f"Document '{filename}' deleted successfully")
            return {"success": True, "message": "Document deleted successfully"}
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            import traceback
            traceback.print_exc()
            self.pg_conn.rollback()
            return {"success": False, "message": f"Error deleting document: {str(e)}", "error": str(e)}
    
    def query_documents(self, user_id: str, query: str, limit: int = 5) -> Dict:
        """
        Query user's documents using RAG
        Returns relevant chunks and generated answer
        """
        try:
            if not self.weaviate_client:
                return {
                    "answer": "Document search is not available (Weaviate not connected)",
                    "sources": []
                }
            
            # Search Weaviate for relevant chunks
            collection = self.weaviate_client.collections.get(self.collection_name)
            
            response = collection.query.near_text(
                query=query,
                limit=limit,
                where={
                    "path": ["user_id"],
                    "operator": "Equal",
                    "valueText": user_id
                }
            )
            
            # Extract relevant chunks
            sources = []
            context_chunks = []
            
            for obj in response.objects:
                sources.append({
                    "filename": obj.properties.get("filename"),
                    "chunk_text": obj.properties.get("chunk_text")[:200] + "...",
                    "chunk_index": obj.properties.get("chunk_index")
                })
                context_chunks.append(obj.properties.get("chunk_text"))
            
            # Generate answer using LLM
            if context_chunks:
                context = "\n\n".join(context_chunks)
                prompt = f"""Based on the following documents, answer the question.
                
Context:
{context}

Question: {query}

Answer:"""
                
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = response.choices[0].message.content
            else:
                answer = "I couldn't find relevant information in your uploaded documents."
            
            return {
                "answer": answer,
                "sources": sources,
                "context_found": len(sources) > 0
            }
            
        except Exception as e:
            return {
                "answer": f"Error querying documents: {str(e)}",
                "sources": []
            }

