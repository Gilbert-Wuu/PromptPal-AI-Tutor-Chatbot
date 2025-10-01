# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Weaviate Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate configuration
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env file")

print(f"✓ Configuration loaded")
print(f"  - Weaviate URL: {WEAVIATE_URL}")
print(f"  - OpenAI API Key: {'*' * 20}{OPENAI_API_KEY[-4:]}")
