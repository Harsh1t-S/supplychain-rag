"""
Central configuration for the Meridian supply chain RAG system.

Every tunable lives here so that ingest.py, rag.py, app.py and the FastAPI
service all agree on chunk sizes, model names and where Chroma stores itself.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- paths -----------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# --- chunking --------------------------------------------------------------
# 1200 characters is the top of the range the brief allows. The two Meridian
# PDFs are dominated by tables (supplier scorecard, approval limits, safety
# stock floors). At 800 characters those tables split across chunk boundaries
# and the retriever returns half a table, which is worse than useless for a
# question like "what is the approval authority for a 1.4 crore PO". At 1200
# each table survives inside a single chunk.
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# --- models ----------------------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"
TEMPERATURE = 0.0

# --- retrieval -------------------------------------------------------------
# Questions 5-9 of the assignment need a number from the quarterly review AND
# a clause from the policy handbook in the same context window. With top_k=3
# all three chunks routinely come from whichever document is the stronger
# semantic match, and the cross-document answers fail. 6 is the smallest value
# that reliably pulls from both.
DEFAULT_TOP_K = 6

COLLECTION_NAME = "meridian_supply_chain"

# --- API key ---------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def require_api_key() -> str:
    """Fail loudly and early rather than deep inside an OpenAI call."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and put your "
            "key in it, or export OPENAI_API_KEY in your shell."
        )
    return OPENAI_API_KEY
