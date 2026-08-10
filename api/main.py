"""
FastAPI backend (the optional bonus in section 6 of the brief).

    uvicorn api.main:app --reload

Then open http://localhost:8000/docs and exercise all three endpoints from
the automatic documentation page.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Allow `uvicorn api.main:app` to import the modules at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from config import DEFAULT_TOP_K, LLM_MODEL  # noqa: E402
from ingest import ingest_files, stats  # noqa: E402
from rag import answer_question  # noqa: E402

app = FastAPI(
    title="Meridian Supply Chain RAG API",
    description=(
        "Retrieval augmented generation over the Meridian quarterly supply "
        "chain review and the procurement policy handbook."
    ),
    version="1.0.0",
)


# --- schemas ---------------------------------------------------------------


class IngestResponse(BaseModel):
    files: int
    chunks: int
    detail: list[dict]
    total_in_store: int


class AskRequest(BaseModel):
    question: str = Field(..., examples=["What is the approval authority for a purchase order worth ₹1.4 crore?"])
    top_k: int = Field(DEFAULT_TOP_K, ge=1, le=20)


class Source(BaseModel):
    file: str
    page: int
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class StatsResponse(BaseModel):
    collection: str
    total_chunks: int
    documents: dict
    embedding_model: str
    llm_model: str
    chunk_size: int
    chunk_overlap: int


# --- endpoints -------------------------------------------------------------


@app.post("/ingest", response_model=IngestResponse, summary="Index one or more PDFs")
async def ingest_endpoint(files: list[UploadFile] = File(...)) -> IngestResponse:
    """Upload PDFs, chunk and embed them, and persist them into Chroma."""
    if not files:
        raise HTTPException(status_code=400, detail="No files supplied.")

    tmpdir = Path(tempfile.mkdtemp())
    paths: list[Path] = []
    for upload in files:
        if not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail=f"{upload.filename} is not a PDF."
            )
        target = tmpdir / upload.filename
        target.write_bytes(await upload.read())
        paths.append(target)

    try:
        result = ingest_files(paths)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IngestResponse(**result)


@app.post("/ask", response_model=AskResponse, summary="Ask a grounded question")
async def ask_endpoint(payload: AskRequest) -> AskResponse:
    """Retrieve the closest chunks and answer strictly from them."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    try:
        result = answer_question(payload.question.strip(), top_k=payload.top_k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AskResponse(answer=result["answer"], sources=result["sources"])


@app.get("/stats", response_model=StatsResponse, summary="Collection statistics")
async def stats_endpoint() -> StatsResponse:
    """Collection name, chunk count, and the models in use."""
    s = stats()
    return StatsResponse(
        collection=s["collection"],
        total_chunks=s["total_chunks"],
        documents=s["documents"],
        embedding_model=s["embedding_model"],
        llm_model=LLM_MODEL,
        chunk_size=s["chunk_size"],
        chunk_overlap=s["chunk_overlap"],
    )


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"service": "Meridian Supply Chain RAG API", "docs": "/docs"}
