"""
R-03 in-memory cache for recommendation results.

Strategy:
  - Key  : SHA-256(user_id + ":" + query_text)  — unique per buyer per profile state
  - TTL  : 5 minutes (300 s)
  - Hit  : return stored RecommendationCard list immediately, skipping ChromaDB + LLM
  - Miss : run full pipeline, store result before returning

R-03 flow:
  1. ChromaDB query capped at 1.5 s via asyncio.wait_for in vector.py.
  2. If ChromaDB times out → serve from cache (this module).
  3. If cache is also empty → return [] with a warning log.
  4. Subsequent requests for the same profile state serve from cache in <50 ms.
"""
import hashlib
import time
from typing import Any, Optional

_CACHE_TTL_SECONDS = 300  # 5 minutes
_store: dict[str, tuple[Any, float]] = {}


def _key(user_id: str, query_text: str) -> str:
    raw = f"{user_id}:{query_text}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get(user_id: str, query_text: str) -> Optional[Any]:
    """Return cached value if present and not expired, else None."""
    k = _key(user_id, query_text)
    entry = _store.get(k)
    if entry is None:
        return None
    value, ts = entry
    if time.monotonic() - ts > _CACHE_TTL_SECONDS:
        del _store[k]
        return None
    return value


def set_result(user_id: str, query_text: str, value: Any) -> None:
    """Store a result. Overwrites any existing entry for the same key."""
    _store[_key(user_id, query_text)] = (value, time.monotonic())


def evict_expired() -> int:
    """Remove all expired entries. Returns count of evicted entries."""
    now = time.monotonic()
    expired = [k for k, (_, ts) in _store.items() if now - ts > _CACHE_TTL_SECONDS]
    for k in expired:
        del _store[k]
    return len(expired)


def size() -> int:
    return len(_store)
