"""
ChromaDB query interface — match pipeline reads the 'inventory' collection.

This module owns the read path for inventory similarity search.
It does NOT write to ChromaDB — that is owned by inventory/embeddings.py.

R-03: all queries are wrapped in asyncio.wait_for with a 1.5-second timeout.
      On timeout, an empty result dict is returned and the caller falls back
      to the in-memory cache (cache.py).
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
INVENTORY_COLLECTION = "inventory"
QUERY_TIMEOUT_SECONDS = 1.5  # R-03 threshold

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chroma-match")
_collection = None

_EMPTY_RESULT = {"ids": [[]], "distances": [[]], "metadatas": [[]]}


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        _collection = client.get_or_create_collection(
            name=INVENTORY_COLLECTION,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def warmup() -> None:
    """Pre-load model + open collection so first query is fast."""
    _get_collection()
    logger.info("Match vector layer warm — inventory collection ready.")


def _query_sync(
    query_text: str,
    n_results: int,
    where: Optional[dict],
) -> dict:
    col = _get_collection()
    # ChromaDB raises if n_results > collection size; clamp gracefully
    count = col.count()
    if count == 0:
        return _EMPTY_RESULT
    n = max(1, min(n_results, count))
    kwargs: dict = {"query_texts": [query_text], "n_results": n}
    if where:
        kwargs["where"] = where
    return col.query(**kwargs)


async def query_inventory(
    query_text: str,
    n_results: int = 20,
    where: Optional[dict] = None,
) -> dict:
    """
    Query the inventory ChromaDB collection for items similar to query_text.

    R-03: enforces 1.5-second timeout. On timeout returns _EMPTY_RESULT so
          the caller can immediately fall back to the in-memory cache.

    Returns ChromaDB result dict:
      { "ids": [[id, ...]], "distances": [[dist, ...]], "metadatas": [[{...}, ...]] }

    Distances are cosine distance in [0, 1].  similarity = 1 - distance.
    """
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, _query_sync, query_text, n_results, where),
            timeout=QUERY_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(
            "[R-03] inventory ChromaDB query timed out (>%.1fs). "
            "Returning empty — caller should use cache fallback.",
            QUERY_TIMEOUT_SECONDS,
        )
        return _EMPTY_RESULT
