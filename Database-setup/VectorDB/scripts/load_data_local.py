"""
Load Weaviate data from local machine (not Docker).
Run from project root: python Database-setup/VectorDB/scripts/load_data_local.py
"""

import os
import sys
import pandas as pd
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Missing dependency: pip install pypdf")
    sys.exit(1)

import weaviate
from weaviate.classes.query import Filter
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[3] / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_DIR = Path(__file__).parent.parent / "data"

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not set in .env")
    sys.exit(1)

print("Connecting to Weaviate at localhost:8080...")
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    headers={"X-OpenAI-Api-Key": OPENAI_API_KEY},
)
print("Connected\n")

# CoreConcept
collection = client.collections.get("CoreConcept")
existing = collection.aggregate.over_all(total_count=True).total_count
if existing > 0:
    print(f"CoreConcept already has {existing} objects, clearing...")
    collection.data.delete_many(where=Filter.by_property("title").like("*"))

df = pd.read_csv(DATA_DIR / "ai_concepts.csv")
print(f"Loading {len(df)} CoreConcept records...")
with collection.batch.dynamic() as batch:
    for _, row in df.iterrows():
        tags_raw = str(row.get("tags", ""))
        tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
        batch.add_object({
            "title":   str(row.get("title", "")),
            "content": str(row.get("content", "")),
            "topic":   str(row.get("topic", "")),
            "role":    str(row.get("role", "")),
            "tags":    tags,
        })
count = collection.aggregate.over_all(total_count=True).total_count
print(f"✓ CoreConcept: {count} objects\n")

# UseCase
collection = client.collections.get("UseCase")
existing = collection.aggregate.over_all(total_count=True).total_count
if existing > 0:
    print(f"UseCase already has {existing} objects, clearing...")
    collection.data.delete_many(where=Filter.by_property("title").like("*"))

df = pd.read_csv(DATA_DIR / "use_case.csv")
print(f"Loading {len(df)} UseCase records...")
with collection.batch.dynamic() as batch:
    for _, row in df.iterrows():
        batch.add_object({
            "title":          str(row.get("title", "")),
            "application":    str(row.get("application", "")),
            "business_value": str(row.get("business_value", "")),
            "role":           str(row.get("role", "")),
            "difficulty":     str(row.get("difficulty", "")),
        })
count = collection.aggregate.over_all(total_count=True).total_count
print(f"✓ UseCase: {count} objects\n")

# PromptGuide
collection = client.collections.get("PromptGuide")
existing = collection.aggregate.over_all(total_count=True).total_count
if existing > 0:
    print(f"PromptGuide already has {existing} objects, clearing...")
    collection.data.delete_many(where=Filter.by_property("section").like("*"))

pdf_path = DATA_DIR / "FHI Prompt Engineering Guide v1.5.pdf"
reader = PdfReader(str(pdf_path))
full_text = " ".join(page.extract_text() or "" for page in reader.pages)
chunks = [full_text[i:i + 1000] for i in range(0, len(full_text), 1000)]
print(f"Loading {len(chunks)} PromptGuide chunks from PDF...")
with collection.batch.dynamic() as batch:
    for i, chunk in enumerate(chunks):
        batch.add_object({
            "content": chunk,
            "section": f"chunk_{i}",
            "tags":    ["prompt engineering"],
        })
count = collection.aggregate.over_all(total_count=True).total_count
print(f"✓ PromptGuide: {count} objects\n")

client.close()
print("✓ All data loaded successfully")
