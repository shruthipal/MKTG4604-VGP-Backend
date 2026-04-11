"""
ChromaDB embedding layer for buyer profiles.

Collection: buyer_profiles  (separate from the 'inventory' collection)
Model:      all-MiniLM-L6-v2 (same model, shared on-disk cache)

R-02 notice:
  - Metadata stored in ChromaDB (user_id, segment, budget) is PLATFORM-INTERNAL.
  - The match pipeline may read this metadata for ranking (R-01 nonprofit priority,
    R-04 rejection de-prioritization) but must NEVER forward it to retailers.
  - query_buyers() is exported for the match pipeline's internal use only.
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
BUYER_COLLECTION = "buyer_profiles"
EMBED_TIMEOUT_SECONDS = 1.5  # R-03 threshold

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chroma-buyer")

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        _collection = client.get_or_create_collection(
            name=BUYER_COLLECTION,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def warmup() -> None:
    """Pre-load the model (shared cache with inventory service)."""
    _get_collection()
    logger.info("Buyer ChromaDB collection warm — model loaded.")


# ── Document text builder ──────────────────────────────────────────────────────

def _build_doc_text(d: dict) -> str:
    prefs = ", ".join(d.get("preferences") or [])
    parts = [
        f"Segment: {d.get('segment', '')}",
        f"Category preferences: {prefs}",
        f"Budget: ${float(d.get('budget_min', 0)):.2f} to ${float(d.get('budget_max', 0)):.2f}",
    ]
    if d.get("notes"):
        parts.append(f"Notes: {d['notes']}")
    if d.get("location"):
        parts.append(f"Location: {d['location']}")
    return "\n".join(parts)


# ── Sync helpers ───────────────────────────────────────────────────────────────

def _upsert_sync(profile_id: str, data: dict) -> None:
    col = _get_collection()
    col.upsert(
        ids=[profile_id],
        documents=[_build_doc_text(data)],
        metadatas=[
            {
                # R-02: this metadata is INTERNAL to the platform.
                # Never forward these fields to retailer-facing responses.
                "user_id": data.get("user_id", ""),
                "segment": data.get("segment", ""),
                "budget_min": float(data.get("budget_min", 0)),
                "budget_max": float(data.get("budget_max", 0)),
            }
        ],
    )


def _query_sync(query_text: str, n_results: int, where: Optional[dict]) -> dict:
    col = _get_collection()
    kwargs = {"query_texts": [query_text], "n_results": n_results}
    if where:
        kwargs["where"] = where
    return col.query(**kwargs)


def _delete_sync(profile_id: str) -> None:
    _get_collection().delete(ids=[profile_id])


# ── Async public API ───────────────────────────────────────────────────────────

async def upsert_buyer(profile_id: str, data: dict) -> bool:
    """
    Embed and upsert a buyer profile.
    Returns True on success; False on R-03 timeout (item stays in DB, embedded=False).
    """
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(_executor, _upsert_sync, profile_id, data),
            timeout=EMBED_TIMEOUT_SECONDS,
        )
        return True
    except asyncio.TimeoutError:
        logger.warning(
            "[R-03] ChromaDB upsert timed out (>1.5s) for buyer profile %s.", profile_id
        )
        return False


async def query_buyers(
    query_text: str,
    n_results: int = 10,
    where: Optional[dict] = None,
) -> dict:
    """
    Query the buyer_profiles collection by similarity to query_text.

    For MATCH PIPELINE USE ONLY.

    Returns raw ChromaDB result dict:
      { "ids": [[...]], "distances": [[...]], "metadatas": [[...]] }

    R-02 reminder: the caller (match pipeline) must strip segment / budget from
    any dict that will be sent to a retailer. Use BuyerMatchSummary exclusively.
    """
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_executor, _query_sync, query_text, n_results, where),
            timeout=EMBED_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("[R-03] ChromaDB buyer query timed out (>1.5s) — returning empty.")
        return {"ids": [[]], "distances": [[]], "metadatas": [[]]}


async def delete_buyer(profile_id: str) -> None:
    """Remove a buyer profile from ChromaDB (e.g. account deletion)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _delete_sync, profile_id)
    logger.info("Deleted buyer profile %s from ChromaDB.", profile_id)
