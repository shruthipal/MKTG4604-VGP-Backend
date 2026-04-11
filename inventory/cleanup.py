"""
R-05: Sold or expired inventory must be de-indexed from the vector DB within 24 hours.

Strategy: an asyncio background task runs every hour. It queries SQLite for any item
where (status IN ('sold','expired') OR expiry_date <= now()) AND embedded = True,
removes those IDs from ChromaDB, then marks embedded=False in SQLite.

Running hourly guarantees a worst-case lag of ~1 hour — well within the 24-hour limit.
Immediate de-indexing also fires inline on the PATCH /{id}/status route for sold items.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import or_, select

from .database import AsyncSessionLocal
from .embeddings import delete_items
from .models import InventoryItem

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = 3600  # 1 hour


async def _run_deindex_pass() -> None:
    """Single pass: find stale embedded items, delete from ChromaDB, update DB."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.embedded == True,  # noqa: E712
                or_(
                    InventoryItem.status == "sold",
                    InventoryItem.status == "expired",
                    InventoryItem.expiry_date <= now,
                ),
            )
        )
        stale = result.scalars().all()

        if not stale:
            logger.debug("[R-05] Cleanup pass: no stale items found.")
            return

        ids = [item.id for item in stale]
        await delete_items(ids)

        for item in stale:
            item.embedded = False
            # Promote status to 'expired' if it slipped past via expiry_date
            if item.status == "available" and item.expiry_date <= now:
                item.status = "expired"

        await db.commit()
        logger.info("[R-05] Cleanup pass de-indexed %d item(s).", len(ids))


async def run_cleanup_loop() -> None:
    """
    Long-running async background task. Start this with asyncio.create_task()
    inside the FastAPI lifespan so it is tied to the server's event loop.
    """
    logger.info("[R-05] Cleanup loop started — interval: %ds.", _INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(_INTERVAL_SECONDS)
        try:
            await _run_deindex_pass()
        except Exception:
            logger.exception("[R-05] Error during cleanup pass — will retry next cycle.")
