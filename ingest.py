"""
Ingestion pipeline: PDF -> text -> chunks -> embeddings -> ChromaDB.

Run directly to index everything sitting in data/:

    python ingest.py

Or import `ingest_files` and hand it a list of paths (this is what the
Streamlit app and the FastAPI service both do).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Iterable

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    EMBEDDING_MODEL,
    require_api_key,
)

# Batch size for the embeddings endpoint. Well under the request limit, and
# keeps a failed batch cheap to retry.
EMBED_BATCH = 64


# --- Chroma ----------------------------------------------------------------


def get_collection():
    """
    Open (or create) the persistent Chroma collection.

    PersistentClient writes to CHROMA_DIR on disk, which is what makes the
    index survive a restart of the app -- requirement 7 in the brief.
    """
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# --- PDF loading -----------------------------------------------------------


def load_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """
    Extract text page by page.

    Returning (page_number, text) pairs rather than one big string is the
    whole reason we can cite a page number later. Page numbers are 1-based so
    they line up with what a buyer sees in a PDF viewer.
    """
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    if not pages:
        raise ValueError(
            f"No selectable text found in {path.name}. It is probably a scanned "
            f"image. OCR is out of scope for this assignment."
        )
    return pages


def make_splitter() -> RecursiveCharacterTextSplitter:
    """
    Recursive character splitting, as mandated by the brief.

    The separator list is ordered most-natural-break-first, so the splitter
    prefers to cut on a blank line, then a newline, then a sentence, and only
    falls back to a hard character cut when it has no choice.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_pages(
    filename: str, pages: list[tuple[int, str]]
) -> tuple[list[str], list[dict], list[str]]:
    """
    Split each page independently so that page provenance is never lost.

    If we concatenated the whole document first and then split, a chunk could
    straddle a page boundary and we would not know which page to cite.
    """
    splitter = make_splitter()
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for page_no, page_text in pages:
        for piece in splitter.split_text(page_text):
            piece = piece.strip()
            if len(piece) < 40:  # drop headers/footers that split off alone
                continue
            # Deterministic ID: re-ingesting an unchanged file upserts over the
            # same rows instead of creating duplicates. Without this, clicking
            # "Index" twice would double every chunk and skew retrieval.
            digest = hashlib.sha256(
                f"{filename}|{page_no}|{piece}".encode("utf-8")
            ).hexdigest()[:24]
            documents.append(piece)
            metadatas.append(
                {"source": filename, "page": page_no, "chars": len(piece)}
            )
            ids.append(digest)

    return documents, metadatas, ids


# --- Embeddings ------------------------------------------------------------


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed in batches with text-embedding-3-small."""
    client = OpenAI(api_key=require_api_key())
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = texts[start : start + EMBED_BATCH]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
    return vectors


# --- Public entry point ----------------------------------------------------


def ingest_files(paths: Iterable[Path | str]) -> dict:
    """
    Index one or more PDFs into the persistent Chroma collection.

    Returns a summary dict the UI and the /ingest endpoint both render.
    """
    collection = get_collection()

    all_docs: list[str] = []
    all_meta: list[dict] = []
    all_ids: list[str] = []
    per_file: list[dict] = []

    for raw_path in paths:
        path = Path(raw_path)
        pages = load_pdf_pages(path)
        docs, meta, ids = chunk_pages(path.name, pages)
        per_file.append(
            {"file": path.name, "pages": len(pages), "chunks": len(docs)}
        )
        all_docs.extend(docs)
        all_meta.extend(meta)
        all_ids.extend(ids)

    if not all_docs:
        return {"files": 0, "chunks": 0, "detail": [], "total_in_store": collection.count()}

    embeddings = embed_texts(all_docs)

    # Upsert in batches -- Chroma is happier with moderate payloads.
    for start in range(0, len(all_docs), 256):
        end = start + 256
        collection.upsert(
            ids=all_ids[start:end],
            documents=all_docs[start:end],
            metadatas=all_meta[start:end],
            embeddings=embeddings[start:end],
        )

    return {
        "files": len(per_file),
        "chunks": len(all_docs),
        "detail": per_file,
        "total_in_store": collection.count(),
    }


def stats() -> dict:
    """Collection-level facts, surfaced in the UI sidebar and GET /stats."""
    collection = get_collection()
    sources: dict[str, int] = {}
    total = collection.count()
    if total:
        got = collection.get(include=["metadatas"])
        for meta in got["metadatas"]:
            sources[meta["source"]] = sources.get(meta["source"], 0) + 1
    return {
        "collection": COLLECTION_NAME,
        "total_chunks": total,
        "documents": sources,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "persist_directory": str(CHROMA_DIR),
    }


def reset() -> None:
    """Drop the collection. Handy while debugging chunk sizes."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
        print("Collection dropped.")

    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {DATA_DIR}")
        raise SystemExit(1)

    print(f"Indexing {len(pdfs)} file(s) from {DATA_DIR} ...")
    result = ingest_files(pdfs)
    for row in result["detail"]:
        print(f"  {row['file']}: {row['pages']} pages -> {row['chunks']} chunks")
    print(
        f"\n{result['files']} files processed, {result['chunks']} chunks stored."
    )
    print(f"Collection now holds {result['total_in_store']} chunks total.")
