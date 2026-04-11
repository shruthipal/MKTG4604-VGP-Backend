"""
ChromaDB embedding layer for inventory items.

R-03 enforcement: upsert calls run in a thread-pool executor with a 1.5-second
timeout. If the timeout fires, the item remains in SQLite (status=available,
embedded=False) and will be picked up on the next R-05 cleanup pass or a
manual re-index. The upload endpoint still returns 201 — the DB write succeeded.
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "inventory"
EMBED_TIMEOUT_SECONDS = 1.5  # R-03 threshold

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chroma")

# ── Singleton client + collection ─────────────────────────────────────────────
_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def warmup() -> None:
    """Pre-load the sentence-transformer model so the first upload is fast."""
    _get_collection()
    logger.info("ChromaDB collection warm — model loaded.")


# ── Document text builder ──────────────────────────────────────────────────────

def _build_doc_text(d: dict) -> str:
    parts = [
        f"Title: {d.get('title', '')}",
        f"Category: {d.get('category', '')}",
        f"Condition: {d.get('condition', '')}",
        f"Price: ${float(d.get('price', 0)):.2f}",
        f"Quantity: {int(d.get('quantity', 0))}",
    ]
    if d.get("description"):
        parts.append(f"Description: {d['description']}")
    if d.get("location"):
        parts.append(f"Location: {d['location']}")
    return "\n".join(parts)


# ── Sync helpers (run inside thread-pool) ─────────────────────────────────────

def _upsert_sync(item_id: str, item_data: dict) -> None:
    col = _get_collection()
    col.upsert(
        ids=[item_id],
        documents=[_build_doc_text(item_data)],
        metadatas=[
            {
                "retailer_id": item_data.get("retailer_id", ""),
                "category": item_data.get("category", ""),
                "condition": item_data.get("condition", ""),
                "price": float(item_data.get("price", 0)),
                "quantity": int(item_data.get("quantity", 0)),
                "status": item_data.get("status", "available"),
            }
        ],
    )


def _delete_sync(item_ids: list[str]) -> None:
    if not item_ids:
        return
    _get_collection().delete(ids=item_ids)


# ── Async public API ───────────────────────────────────────────────────────────

async def upsert_item(item_id: str, item_data: dict) -> bool:
    """
    Embed and upsert one inventory item.
    Returns True on success; False if ChromaDB exceeded the 1.5s R-03 threshold.
    """
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(_executor, _upsert_sync, item_id, item_data),
            timeout=EMBED_TIMEOUT_SECONDS,
        )
        return True
    except asyncio.TimeoutError:
        logger.warning(
            "[R-03] ChromaDB upsert timed out (>1.5s) for item %s. "
            "Falling back — item saved to DB, will be indexed on next pass.",
            item_id,
        )
        return False


async def delete_items(item_ids: list[str]) -> None:
    """
    Remove items from ChromaDB. Called by R-05 cleanup and the immediate
    sold/expired status-update path.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _delete_sync, item_ids)
    logger.info("[R-05] Deleted %d item(s) from ChromaDB: %s", len(item_ids), item_ids)
