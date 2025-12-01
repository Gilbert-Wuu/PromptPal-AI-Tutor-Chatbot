"""
Load data into Weaviate (v4 API)
"""

import os
import pandas as pd
from pypdf import PdfReader
from pathlib import Path
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter

# Load environment variables
load_dotenv()

# Paths inside Docker container
DATA_DIR = Path("/data")

CORE_CONCEPTS_CSV = DATA_DIR / "ai_concepts.csv"
USE_CASES_CSV = DATA_DIR / "use_case.csv"
PDF_PATH = DATA_DIR / "FHI Prompt Engineering Guide v1.5.pdf"

# Weaviate environment
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

print("=" * 60)
print("WEAVIATE LOAD DATA (v4)")
print("=" * 60)

# Connect to Weaviate (v4)
if "localhost" in WEAVIATE_URL or "weaviate" in WEAVIATE_URL:
    print("Connecting to LOCAL Weaviate...")
    client = weaviate.connect_to_local(
        host="weaviate",
        port=8080,
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
    )
else:
    print("Connecting to CLOUD Weaviate...")
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
    )

print("✓ Connected\n")

# ================================
# Insert Core Concepts
# ================================
print("Loading Core Concepts...")

if not CORE_CONCEPTS_CSV.exists():
    raise FileNotFoundError(f"Missing: {CORE_CONCEPTS_CSV}")

df = pd.read_csv(CORE_CONCEPTS_CSV)
collection = client.collections.get("CoreConcept")

success = 0
for _, row in df.iterrows():
    obj = {
        "content_id": row["content_id"],
        "title": row["title"],
        "content": row["content"],
        "topic": row["topic"],
        "role": row["role"],
        "content_type": row["content_type"],
        "tags": row["tags"].split(",") if pd.notna(row["tags"]) else []
    }

    collection.data.insert(properties=obj)
    success += 1
    print(f" ✓ CoreConcept: {row['content_id']}")

print(f"Inserted {success} Core Concepts\n")

# ================================
# Insert Use Cases
# ================================
print("\nLoading Use Cases...")

try:
    df_usecases = pd.read_csv(USE_CASES_CSV)
    print(f"  Found {len(df_usecases)} use cases in CSV")

    use_case_collection = client.collections.get("useCase")

    success_count = 0
    for idx, row in df_usecases.iterrows():
        try:
            data_object = {
                "content_id": row.get("content_id", ""),
                "title": row.get("title", ""),
                "application": row.get("application", ""),
                "content": row.get("description", ""),
                "business_value": row.get("business_value", ""),
                "data_sources": row.get("data_sources", ""),
                "role": row.get("suggested_roles", "general"),
                "example_prompts": row.get("example_prompts", ""),
                "difficulty": row.get("difficulty_level", "unknown"),
                "tags": row.get("tags", "").split(",") if pd.notna(row.get("tags")) else [],
                "related_concepts": row.get("related_concepts", "").split(",")
                    if pd.notna(row.get("related_concepts")) else [],
                "content_type": "use_case"
            }

            use_case_collection.data.insert(properties=data_object)
            success_count += 1
            print(f"  ✓ [{success_count}/{len(df_usecases)}] {data_object['content_id']}")

        except Exception as e:
            print(f"  ✗ Error inserting row {idx}: {e}")

    print(f"\n✓ Successfully loaded {success_count}/{len(df_usecases)} use cases")

except Exception as e:
    print(f"✗ Error loading use cases: {e}")


# ================================
# Insert PDF (PromptGuide)
# ================================
print("Loading Prompt Engineering PDF...")

if not PDF_PATH.exists():
    print(f" ✗ PDF not found: {PDF_PATH}")
else:
    reader = PdfReader(str(PDF_PATH))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    # Split into 1,000 char chunks
    def chunk(text, size=1000):
        return [text[i:i + size] for i in range(0, len(text), size)]

    chunks = chunk(text)
    collection = client.collections.get("PromptGuide")

    for i, ch in enumerate(chunks):
        obj = {
            "content_id": f"fhi_prompt_{i}",
            "title": "FHI Prompt Engineering Guide",
            "content": ch,
            "section": f"Section {i}",
            "tags": ["prompt", "prompt-engineering", "FHI"]
        }
        collection.data.insert(properties=obj)
        print(f" ✓ PromptGuide chunk {i + 1}/{len(chunks)}")

    print(f"Inserted {len(chunks)} PromptGuide entries\n")

# ================================
# Verification (v4 syntax)
# ================================
print("=" * 60)
print("VERIFY INSERTED COUNTS")
print("=" * 60)

for name in ["CoreConcept", "UseCase", "PromptGuide"]:
    col = client.collections.get(name)
    count = col.aggregate.over_all(total_count=True).total_count
    print(f" {name}: {count} objects")

client.close()
print("\n✓ All data load completed")
print("=" * 60)
