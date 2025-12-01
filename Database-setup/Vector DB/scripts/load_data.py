"""
Load Data into Weaviate
Load core concepts and use cases from CSV files
Run this after setup_weaviate.py
"""

import weaviate
from weaviate.classes.init import Auth
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables
load_dotenv()

# Get project paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

# Data files
CORE_CONCEPTS_CSV = DATA_DIR / "ai_concepts.csv"
USE_CASES_CSV = DATA_DIR / "use_case.csv"

# Environment variables
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Collection names
CORE_CONCEPT_COLLECTION = "CoreConcept"
USE_CASE_COLLECTION = "UseCase"

# Validate
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env file")

if not CORE_CONCEPTS_CSV.exists():
    raise FileNotFoundError(f"CSV file not found: {CORE_CONCEPTS_CSV}")

if not USE_CASES_CSV.exists():
    raise FileNotFoundError(f"CSV file not found: {USE_CASES_CSV}")

print("=" * 60)
print("WEAVIATE DATA LOADING")
print("=" * 60)
print(f"Weaviate URL: {WEAVIATE_URL}")
print(f"Data Directory: {DATA_DIR}")
print("=" * 60)

# ============================================
# Connect to Weaviate
# ============================================
print("\nConnecting to Weaviate...")

if "localhost" in WEAVIATE_URL or "127.0.0.1" in WEAVIATE_URL:
    print("  Using LOCAL Weaviate")
    weaviate_client = weaviate.connect_to_local(
        host="localhost",
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
# Load Core Concepts from CSV
# ============================================
print("Loading Core Concepts...")

try:
    # Read CSV
    df_concepts = pd.read_csv(CORE_CONCEPTS_CSV)
    print(f"  Found {len(df_concepts)} concepts in CSV")

    # Get collection
    core_concept_collection = weaviate_client.collections.get(CORE_CONCEPT_COLLECTION)

    # Insert each row
    success_count = 0
    for idx, row in df_concepts.iterrows():
        try:
            data_object = {
                "content_id": row['content_id'],
                "title": row['title'],
                "content": row['content'],
                "topic": row['topic'],
                "role": row['role'],
                "content_type": row['content_type'],
                "tags": row['tags'].split(',') if pd.notna(row['tags']) else []
            }

            # Weaviate will automatically generate embeddings
            core_concept_collection.data.insert(properties=data_object)
            success_count += 1
            print(f"  ✓ [{success_count}/{len(df_concepts)}] {row['content_id']}")

        except Exception as e:
            print(f"  ✗ Error inserting {row['content_id']}: {e}")

    print(f"\n✓ Successfully loaded {success_count}/{len(df_concepts)} core concepts")

except Exception as e:
    print(f"✗ Error loading core concepts: {e}")

# ============================================
# Load Use Cases from CSV
# ============================================
print("\nLoading Use Cases...")

try:
    # Read CSV
    df_usecases = pd.read_csv(USE_CASES_CSV)
    print(f"  Found {len(df_usecases)} use cases in CSV")

    # Get collection
    use_case_collection = weaviate_client.collections.get(USE_CASE_COLLECTION)

    # Insert each row
    success_count = 0
    for idx, row in df_usecases.iterrows():
        try:
            data_object = {
                "content_id": row['content_id'],
                "title": row['title'],
                "application": row['application'],
                "ai_concepts": row['ai_concepts'],
                "business_value": row['business_value'],
                "data_sources": row['data_sources'],
                "role": row['role'],
                "content_type": row['content_type'],
                "tags": row['tags'].split(',') if pd.notna(row['tags']) else [],
                "related_concepts": row['related_concepts'].split(',') if pd.notna(row['related_concepts']) else []
            }

            # Weaviate will automatically generate embeddings
            use_case_collection.data.insert(properties=data_object)
            success_count += 1
            print(f"  ✓ [{success_count}/{len(df_usecases)}] {row['content_id']}")

        except Exception as e:
            print(f"  ✗ Error inserting {row['content_id']}: {e}")

    print(f"\n✓ Successfully loaded {success_count}/{len(df_usecases)} use cases")

except Exception as e:
    print(f"✗ Error loading use cases: {e}")

# ============================================
# Load FHI Prompt Engineering Guide (PDF)
# ============================================
print("\nLoading FHI Prompt Engineering Guide...")


PDF_PATH = DATA_DIR / "FHI Prompt Engineering Guide v1.5.pdf"

if not PDF_PATH.exists():
    print(f"✗ PDF not found at: {PDF_PATH}")
else:
    try:
        reader = PdfReader(str(PDF_PATH))
        pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # chunk text
        def chunk_text(text, chunk_size=1000):
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        chunks = chunk_text(pdf_text)
        prompt_collection = weaviate_client.collections.get("PromptGuide")

        for i, chunk in enumerate(chunks):
            obj = {
                "content_id": f"fhi_prompt_{i}",
                "title": "FHI Prompt Engineering Guide",
                "content": chunk,
                "section": f"Section {i}",
                "tags": ["prompt", "prompt-engineering", "FHI-guide"]
            }
            prompt_collection.data.insert(properties=obj)
            print(f"  ✓ Inserted PromptGuide chunk {i+1}/{len(chunks)}")

        print(f"\n✓ Successfully loaded {len(chunks)} PromptGuide entries")

    except Exception as e:
        print(f"✗ Error loading PDF: {e}")


# ============================================
# Verify Data
# ============================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

try:
    # Count objects in each collection
    core_concepts = weaviate_client.collections.get(CORE_CONCEPT_COLLECTION)
    use_cases = weaviate_client.collections.get(USE_CASE_COLLECTION)

    concept_count = len(core_concepts.query.fetch_objects().objects)
    usecase_count = len(use_cases.query.fetch_objects().objects)

    print(f"\nTotal in Weaviate:")
    print(f"  Core Concepts: {concept_count}")
    print(f"  Use Cases: {usecase_count}")

    # Show sample data
    if concept_count > 0:
        print("\n--- Sample Core Concept ---")
        sample_concept = core_concepts.query.fetch_objects(limit=1).objects[0]
        print(f"  ID: {sample_concept.properties['content_id']}")
        print(f"  Title: {sample_concept.properties['title']}")
        print(f"  Topic: {sample_concept.properties['topic']}")
        print(f"  Tags: {', '.join(sample_concept.properties['tags'])}")

    if usecase_count > 0:
        print("\n--- Sample Use Case ---")
        sample_usecase = use_cases.query.fetch_objects(limit=1).objects[0]
        print(f"  ID: {sample_usecase.properties['content_id']}")
        print(f"  Title: {sample_usecase.properties['title']}")
        print(f"  Role: {sample_usecase.properties['role']}")
        print(f"  Related Concepts: {', '.join(sample_usecase.properties['related_concepts'])}")

except Exception as e:
    print(f"✗ Error during verification: {e}")

# ============================================
# Close Connection
# ============================================
print("\n" + "=" * 60)
weaviate_client.close()
print("✓ Data loading complete!")
print("=" * 60)
