"""
Setup Weaviate Collections
Run this once to create the schema for all collections
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Collection names
CORE_CONCEPT_COLLECTION = "CoreConcept"
USE_CASE_COLLECTION = "UseCase"
INTERACTION_LOG_COLLECTION = "InteractionLog"
EMBEDDING_MODEL = "text-embedding-3-small"

# Validate
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env file")

print("=" * 60)
print("WEAVIATE SCHEMA SETUP")
print("=" * 60)
print(f"Weaviate URL: {WEAVIATE_URL}")
print(f"Embedding Model: {EMBEDDING_MODEL}")
print("=" * 60)

# ============================================
# Connect to Weaviate
# ============================================
print("\nConnecting to Weaviate...")

if "localhost" in WEAVIATE_URL or "127.0.0.1" in WEAVIATE_URL or "weaviate" in WEAVIATE_URL:
    print("  Using LOCAL Weaviate")

    # Determine host based on URL
    if "weaviate:" in WEAVIATE_URL or WEAVIATE_URL == "http://weaviate:8080":
        # Running in Docker, use service name
        host = "weaviate"
        print(f"  Docker mode: Connecting to {host}:8080")
    else:
        # Running locally
        host = "localhost"
        print(f"  Local mode: Connecting to {host}:8080")

    weaviate_client = weaviate.connect_to_local(
        host=host,
        port=8080,
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
    )
else:
    print("  Using CLOUD Weaviate")
    if not WEAVIATE_API_KEY:
        raise ValueError("WEAVIATE_API_KEY required for cloud connection")

    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
    )

print("✓ Connected successfully\n")

# ============================================
# Create CoreConcept Collection
# ============================================
print("Creating CoreConcept collection...")

try:
    if weaviate_client.collections.exists(CORE_CONCEPT_COLLECTION):
        weaviate_client.collections.delete(CORE_CONCEPT_COLLECTION)
        print("  Deleted existing collection")

    weaviate_client.collections.create(
        name=CORE_CONCEPT_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model=EMBEDDING_MODEL
        ),
        properties=[
            Property(name="content_id", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="topic", data_type=DataType.TEXT),
            Property(name="difficulty", data_type=DataType.TEXT),
            Property(name="role", data_type=DataType.TEXT),
            Property(name="content_type", data_type=DataType.TEXT),
            Property(name="tags", data_type=DataType.TEXT_ARRAY),
        ]
    )
    print("✓ CoreConcept collection created")

except Exception as e:
    print(f"✗ Error: {e}")


# ============================================
# Create UseCase Collection
# ============================================
print("\nCreating UseCase collection...")

try:
    if weaviate_client.collections.exists(USE_CASE_COLLECTION):
        weaviate_client.collections.delete(USE_CASE_COLLECTION)
        print("  Deleted existing collection")

    weaviate_client.collections.create(
        name=USE_CASE_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model=EMBEDDING_MODEL
        ),
        properties=[
            Property(name="content_id", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="application", data_type=DataType.TEXT),
            Property(name="ai_concepts", data_type=DataType.TEXT),
            Property(name="business_value", data_type=DataType.TEXT),
            Property(name="data_sources", data_type=DataType.TEXT),
            Property(name="role", data_type=DataType.TEXT),
            Property(name="content_type", data_type=DataType.TEXT),
            Property(name="tags", data_type=DataType.TEXT_ARRAY),
            Property(name="related_concepts", data_type=DataType.TEXT_ARRAY),
        ]
    )
    print("✓ UseCase collection created")

except Exception as e:
    print(f"✗ Error: {e}")

# ============================================
# Create InteractionLog Collection
# ============================================
print("\nCreating InteractionLog collection...")

try:
    if weaviate_client.collections.exists(INTERACTION_LOG_COLLECTION):
        weaviate_client.collections.delete(INTERACTION_LOG_COLLECTION)
        print("  Deleted existing collection")

    weaviate_client.collections.create(
        name=INTERACTION_LOG_COLLECTION,
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model=EMBEDDING_MODEL
        ),
        properties=[
            Property(name="user_id", data_type=DataType.TEXT),
            Property(name="session_id", data_type=DataType.TEXT),
            Property(name="interaction_type", data_type=DataType.TEXT),
            Property(name="action_status", data_type=DataType.TEXT),
            Property(name="content_type", data_type=DataType.TEXT),
            Property(name="content_id", data_type=DataType.TEXT),
            Property(name="user_message", data_type=DataType.TEXT),
            Property(name="agent_response", data_type=DataType.TEXT),
            Property(name="conversation_text", data_type=DataType.TEXT),
            Property(name="topic", data_type=DataType.TEXT),
            Property(name="difficulty", data_type=DataType.TEXT),
            Property(name="timestamp", data_type=DataType.DATE),
            Property(name="importance_score", data_type=DataType.NUMBER),
        ]
    )
    print("✓ InteractionLog collection created")

except Exception as e:
    print(f"✗ Error: {e}")

# ============================================
# Create UserDocument Collection
# ============================================
print("\nCreating UserDocument collection...")

try:
    if weaviate_client.collections.exists("UserDocument"):
        weaviate_client.collections.delete("UserDocument")
        print("  Deleted existing UserDocument")

    weaviate_client.collections.create(
        name="UserDocument",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model=EMBEDDING_MODEL
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
    print("✓ UserDocument collection created")

except Exception as e:
    print(f"✗ Error: {e}")

# ============================================
# Summary
# ============================================
print("\n" + "=" * 60)
print("SETUP COMPLETE")
print("=" * 60)

collections = weaviate_client.collections.list_all()
print(f"\nTotal collections: {len(collections)}")
for name in collections:
    print(f"  - {name}")

print("\nNext step: Run 'python load_data.py' to load CSV data")
print("=" * 60)

weaviate_client.close()
