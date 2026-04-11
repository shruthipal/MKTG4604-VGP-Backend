"""
Match pipeline routes.

POST /match/recommendations  — buyer JWT (R-06: retailers blocked at dependency level)
  Full pipeline:
    1. Segment check     — load buyer profile + segment from DB via JWT sub
    2. Cache check       — return immediately if R-03 cache hit
    3. Vector search     — query inventory ChromaDB (1.5 s timeout, R-03)
    4. Inventory load    — fetch item details from SQLite (available only)
    5. R-04 check        — load segment rejection counts per retailer
    6. Rank + filter     — composite score (similarity + price fit + qty + R-04)
    7. R-01 reorder      — nonprofits: free/discounted items always first
    8. LLM generation    — parallel Ollama llama3 calls (R-01 prompt enforcement)
    9. Persist results   — store MatchResult rows + retailer alerts
   10. Cache + return    — cache cards, return MatchResponse to buyer

GET  /match/alerts           — retailer JWT; R-02 compliant dashboard alerts
PATCH /match/alerts/{id}/read — retailer JWT; mark alert as read
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_utils import require_buyer_role, require_retailer_role
from . import cache as result_cache
from .database import get_db
from .llm import generate_recommendation
from .models import MatchResult, RetailerAlert
from .ranker import RankedItem, rank_and_filter
from .schemas import MatchResponse, RecommendationCard, RetailerAlertResponse
from .vector import query_inventory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["match"])

_TOP_N = 5
_CHROMADB_FETCH_N = 20  # fetch more than needed so ranker has room to filter


# ── POST /match/recommendations ───────────────────────────────────────────────

@router.post(
    "/recommendations",
    response_model=MatchResponse,
    summary=(
        "Run the full match pipeline for the authenticated buyer. "
        "Returns top-5 ranked, LLM-personalised recommendation cards. "
        "[R-06: retailer JWTs blocked]"
    ),
)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),  # R-06 enforced here
):
    t0 = time.monotonic()
    user_id: str = current_user["sub"]

    # ── Step 1: Segment check — load buyer profile ─────────────────────────
    buyer = await _load_buyer_profile(user_id, db)
    segment: str = buyer["segment"]

    # ── Step 2: Build query text + check R-03 cache ────────────────────────
    query_text = _build_query_text(buyer)
    cached_cards = result_cache.get(user_id, query_text)

    if cached_cards is not None:
        logger.info("[R-03] Cache hit for user %s — returning %d cards.", user_id, len(cached_cards))
        return MatchResponse(
            recommendations=cached_cards,
            buyer_segment=segment,
            total_found=len(cached_cards),
            generated_at=datetime.now(timezone.utc),
            served_from_cache=True,
        )

    # ── Step 3: Vector similarity search (1.5 s timeout — R-03) ───────────
    chroma_result = await query_inventory(query_text, n_results=_CHROMADB_FETCH_N)
    ids: list[str] = chroma_result["ids"][0]
    distances: list[float] = chroma_result["distances"][0]

    if not ids:
        logger.warning(
            "[R-03] ChromaDB returned no results for user %s "
            "(timeout or empty collection). Cache also empty.", user_id,
        )
        return MatchResponse(
            recommendations=[],
            buyer_segment=segment,
            total_found=0,
            generated_at=datetime.now(timezone.utc),
            served_from_cache=False,
        )

    # ── Step 4: Load inventory details from SQLite (available items only) ──
    inventory = await _load_inventory_items(ids, db)

    # ── Step 5: R-04 — load same-segment rejection counts per retailer ─────
    rejection_counts = await _load_rejection_counts(segment, db)

    # ── Step 6 + 7: Rank, filter, R-01 nonprofit reorder ──────────────────
    ranked: list[RankedItem] = rank_and_filter(ids, distances, inventory, buyer, rejection_counts)
    top: list[RankedItem] = ranked[:_TOP_N]

    if not top:
        return MatchResponse(
            recommendations=[],
            buyer_segment=segment,
            total_found=0,
            generated_at=datetime.now(timezone.utc),
            served_from_cache=False,
        )

    # ── Step 8: LLM personalisation — parallel calls ──────────────────────
    rec_texts: list[str] = await asyncio.gather(*[
        generate_recommendation(r.item_data, segment, r.composite_score)
        for r in top
    ])

    # ── Step 9a: Build recommendation cards ───────────────────────────────
    cards: list[RecommendationCard] = [
        RecommendationCard(
            item_id=r.item_id,
            title=r.item_data.get("title", ""),
            category=r.item_data.get("category", ""),
            price=float(r.item_data.get("price", 0)),
            condition=r.item_data.get("condition", ""),
            quantity=int(r.item_data.get("quantity", 0)),
            retailer_id=r.item_data.get("retailer_id", ""),
            similarity_score=round(r.similarity_score, 4),
            composite_score=round(r.composite_score, 4),
            recommendation_text=rec_text,
        )
        for r, rec_text in zip(top, rec_texts)
    ]

    # ── Step 9b: Persist match results + retailer alerts ──────────────────
    await _store_match_results(user_id, cards, db)
    await _create_retailer_alerts(cards, db)

    # ── Step 10: Cache + return ────────────────────────────────────────────
    result_cache.set_result(user_id, query_text, cards)

    elapsed = time.monotonic() - t0
    if elapsed > 2.0:
        logger.warning("[R-03] Match pipeline took %.2f s (exceeds 2 s target).", elapsed)
    else:
        logger.info("[R-03] Match pipeline completed in %.2f s.", elapsed)

    return MatchResponse(
        recommendations=cards,
        buyer_segment=segment,
        total_found=len(ranked),
        generated_at=datetime.now(timezone.utc),
        served_from_cache=False,
    )


# ── GET /match/alerts ─────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=list[RetailerAlertResponse],
    summary=(
        "Return match alerts for the authenticated retailer's dashboard. "
        "[R-02: no buyer segment, preferences, or history returned]"
    ),
)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    """
    R-02: RetailerAlertResponse contains item info + match_score_label only.
    buyer_user_id (stored in match_results) is never included here.
    """
    retailer_id: str = current_user["sub"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    result = await db.execute(
        text("""
            SELECT id, retailer_id, item_id, item_title,
                   match_score_label, match_count, is_read, created_at
            FROM   retailer_alerts
            WHERE  retailer_id = :rid
              AND  created_at  >= :cutoff
            ORDER  BY created_at DESC
        """),
        {"rid": retailer_id, "cutoff": cutoff},
    )
    rows = result.fetchall()
    return [
        RetailerAlertResponse(
            id=row.id,
            item_id=row.item_id,
            item_title=row.item_title,
            match_score_label=row.match_score_label,
            match_count=row.match_count,
            is_read=bool(row.is_read),
            created_at=row.created_at,
        )
        for row in rows
    ]


# ── PATCH /match/alerts/{alert_id}/read ──────────────────────────────────────

@router.patch(
    "/alerts/{alert_id}/read",
    response_model=RetailerAlertResponse,
    summary="Mark a retailer dashboard alert as read",
)
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    result = await db.execute(
        text("""
            SELECT id, retailer_id, item_id, item_title,
                   match_score_label, match_count, is_read, created_at
            FROM   retailer_alerts
            WHERE  id = :aid AND retailer_id = :rid
        """),
        {"aid": alert_id, "rid": current_user["sub"]},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    await db.execute(
        text("UPDATE retailer_alerts SET is_read = 1 WHERE id = :aid"),
        {"aid": alert_id},
    )
    await db.commit()

    return RetailerAlertResponse(
        id=row.id,
        item_id=row.item_id,
        item_title=row.item_title,
        match_score_label=row.match_score_label,
        match_count=row.match_count,
        is_read=True,
        created_at=row.created_at,
    )


# ── Private helpers ────────────────────────────────────────────────────────────

async def _load_buyer_profile(user_id: str, db: AsyncSession) -> dict:
    """
    Load buyer profile from buyer_profiles table (cross-module via raw SQL).
    Raises 404 with onboarding hint if no profile exists.
    """
    result = await db.execute(
        text("SELECT * FROM buyer_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer profile not found. Complete onboarding at POST /buyer/onboarding first.",
        )
    profile = dict(row._mapping)
    # Deserialize preferences JSON if stored as string (SQLite TEXT fallback)
    prefs = profile.get("preferences")
    if isinstance(prefs, str):
        try:
            profile["preferences"] = json.loads(prefs)
        except (json.JSONDecodeError, TypeError):
            profile["preferences"] = []
    return profile


def _build_query_text(buyer: dict) -> str:
    """
    Construct the text used to query the inventory ChromaDB collection.
    Mirrors the document format used when embedding inventory items so that
    cosine similarity is meaningful across both collections.
    """
    prefs = buyer.get("preferences") or []
    if isinstance(prefs, str):
        prefs = json.loads(prefs)
    prefs_str = ", ".join(prefs) if prefs else ""

    parts = [
        f"Segment: {buyer.get('segment', '')}",
        f"Category preferences: {prefs_str}",
        f"Budget: ${float(buyer.get('budget_min', 0)):.2f} "
        f"to ${float(buyer.get('budget_max', 0)):.2f}",
    ]
    if buyer.get("notes"):
        parts.append(f"Notes: {buyer['notes']}")
    return "\n".join(parts)


async def _load_inventory_items(
    item_ids: list[str],
    db: AsyncSession,
) -> dict[str, dict]:
    """
    Fetch full item rows from inventory_items for the given IDs.
    Filters to status = 'available' only — respects R-05 interim state.
    """
    if not item_ids:
        return {}
    placeholders = ", ".join(f":id{i}" for i in range(len(item_ids)))
    params = {f"id{i}": iid for i, iid in enumerate(item_ids)}
    result = await db.execute(
        text(
            f"SELECT * FROM inventory_items "
            f"WHERE id IN ({placeholders}) AND status = 'available'"
        ),
        params,
    )
    return {row.id: dict(row._mapping) for row in result.fetchall()}


async def _load_rejection_counts(
    segment: str,
    db: AsyncSession,
) -> dict[str, int]:
    """
    R-04: Count how many times buyers in `segment` have rejected items
    from each retailer. Returns {retailer_id: count}.
    Only retailers with count >= 3 will be penalised by the ranker.
    """
    try:
        result = await db.execute(
            text("""
                SELECT   i.retailer_id, COUNT(*) AS cnt
                FROM     behavior_logs  bl
                JOIN     inventory_items i  ON bl.item_id  = i.id
                JOIN     buyer_profiles bp  ON bl.user_id  = bp.user_id
                WHERE    bl.action    = 'rejected'
                  AND    bp.segment   = :segment
                GROUP BY i.retailer_id
            """),
            {"segment": segment},
        )
        return {row.retailer_id: row.cnt for row in result.fetchall()}
    except Exception:
        # Tables may not exist yet in a fresh environment — degrade gracefully
        logger.debug("[R-04] Could not load rejection counts — defaulting to empty.")
        return {}


async def _store_match_results(
    user_id: str,
    cards: list[RecommendationCard],
    db: AsyncSession,
) -> None:
    """Persist one MatchResult row per recommendation card (analytics + CTR tracking)."""
    for card in cards:
        db.add(MatchResult(
            buyer_user_id=user_id,
            item_id=card.item_id,
            similarity_score=card.similarity_score,
            composite_score=card.composite_score,
            recommendation_text=card.recommendation_text,
        ))
    await db.commit()


async def _create_retailer_alerts(
    cards: list[RecommendationCard],
    db: AsyncSession,
) -> None:
    """
    Create one RetailerAlert per matched item.

    Deduplication: if an alert for the same item_id was created within the
    last hour, increment its match_count instead of inserting a new row.

    R-02: alert rows store item info + match_score_label only — no buyer data.
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    for card in cards:
        score_label = (
            "Strong" if card.composite_score >= 0.75
            else "Good" if card.composite_score >= 0.50
            else "Moderate"
        )
        # Check for recent duplicate
        existing = await db.execute(
            text("""
                SELECT id, match_count FROM retailer_alerts
                WHERE  item_id     = :iid
                  AND  retailer_id = :rid
                  AND  created_at  >= :cutoff
                ORDER  BY created_at DESC
                LIMIT  1
            """),
            {"iid": card.item_id, "rid": card.retailer_id, "cutoff": one_hour_ago},
        )
        row = existing.fetchone()

        if row:
            await db.execute(
                text("UPDATE retailer_alerts SET match_count = :cnt WHERE id = :aid"),
                {"cnt": row.match_count + 1, "aid": row.id},
            )
        else:
            db.add(RetailerAlert(
                retailer_id=card.retailer_id,
                item_id=card.item_id,
                item_title=card.title,
                match_score_label=score_label,
            ))

    await db.commit()
