"""
Composite scoring, ranking, and segment-specific filtering.

Scoring weights
───────────────
  base          = cosine similarity from ChromaDB (0 – 1)
  price_fit     = +0.10 in-budget / +0.05 below budget / -0.20 over budget / +0.10 free
  quantity      = +0.05 if qty ≥ 10  |  no change if 1–9  |  -0.50 if qty == 0
  R-04 penalty  = -0.30 if retailer has ≥ 3 same-segment rejections
  final         = clamp(sum, 0.0, 1.0)

R-01 (nonprofit sort override)
───────────────────────────────
  After scoring, nonprofit buyers get a SORT OVERRIDE (not just a score bump):
    1. free items (price == 0) → top
    2. discounted items (price ≤ 25 % of buyer's budget_max) → second tier
    3. remaining items → ranked by composite score as usual
  This guarantees nonprofits always see free/discounted inventory first regardless
  of similarity score. Per spec: "Never use profit-margin framing for nonprofits"
  is enforced separately in the LLM prompt layer (llm.py).

R-04 (segment rejection de-prioritization)
───────────────────────────────────────────
  rejection_counts: dict[retailer_id, count] loaded from behavior_logs × buyer_profiles join.
  If count ≥ 3 for the buyer's segment: subtract 0.30 from composite score.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RankedItem:
    item_id: str
    item_data: dict
    similarity_score: float
    composite_score: float


def compute_composite_score(
    similarity: float,
    item: dict,
    buyer: dict,
    rejection_counts: dict[str, int],
) -> float:
    score = similarity  # base: cosine similarity 0–1

    price = float(item.get("price", 0))
    budget_min = float(buyer.get("budget_min", 0))
    budget_max = float(buyer.get("budget_max", 0))

    # ── Price fit ──────────────────────────────────────────────────────────
    if price == 0:
        score += 0.10          # free item — always a fit
    elif budget_min <= price <= budget_max:
        score += 0.10          # in-budget bonus
    elif price < budget_min:
        score += 0.05          # below budget — still affordable
    else:
        score -= 0.20          # over budget — significant penalty

    # ── Quantity alignment ─────────────────────────────────────────────────
    qty = int(item.get("quantity", 0))
    if qty == 0:
        score -= 0.50          # out of stock — should be filtered upstream but penalise
    elif qty >= 10:
        score += 0.05          # healthy stock level

    # ── R-04: retailer segment de-prioritization ───────────────────────────
    retailer_id = str(item.get("retailer_id", ""))
    rejection_count = rejection_counts.get(retailer_id, 0)
    if rejection_count >= 3:
        score -= 0.30
        logger.debug(
            "[R-04] De-prioritized retailer %s (segment rejections: %d)",
            retailer_id,
            rejection_count,
        )

    return max(0.0, min(1.0, score))


def _nonprofit_reorder(ranked: list[RankedItem], budget_max: float) -> list[RankedItem]:
    """
    R-01: Nonprofits always see free/discounted inventory first.
    Discount threshold: price ≤ 25 % of the buyer's budget_max.
    Each tier is sorted by composite_score descending within itself.
    """
    threshold = budget_max * 0.25 if budget_max > 0 else 0.0

    free: list[RankedItem] = []
    discounted: list[RankedItem] = []
    regular: list[RankedItem] = []

    for item in ranked:
        price = float(item.item_data.get("price", 999))
        if price == 0:
            free.append(item)
        elif threshold > 0 and price <= threshold:
            discounted.append(item)
        else:
            regular.append(item)

    logger.info(
        "[R-01] Nonprofit reorder — free: %d, discounted: %d, regular: %d",
        len(free), len(discounted), len(regular),
    )
    return free + discounted + regular


def rank_and_filter(
    ids: list[str],
    distances: list[float],
    inventory: dict[str, dict],   # {item_id: item_row_dict} — available items only
    buyer: dict,
    rejection_counts: dict[str, int],
) -> list[RankedItem]:
    """
    Score every ChromaDB result, sort by composite_score descending, then
    apply R-01 nonprofit reorder if applicable.

    Items missing from `inventory` (sold/expired between ChromaDB query and
    SQLite load) are silently skipped — they will be de-indexed by R-05.
    """
    ranked: list[RankedItem] = []

    for item_id, distance in zip(ids, distances):
        item_data = inventory.get(item_id)
        if not item_data:
            continue  # sold/expired since ChromaDB query — skip

        similarity = max(0.0, 1.0 - float(distance))  # cosine distance → similarity
        composite = compute_composite_score(similarity, item_data, buyer, rejection_counts)
        ranked.append(RankedItem(item_id, item_data, similarity, composite))

    # Sort by composite score descending
    ranked.sort(key=lambda r: r.composite_score, reverse=True)

    # R-01: nonprofit sort override
    if buyer.get("segment") == "nonprofit":
        ranked = _nonprofit_reorder(ranked, float(buyer.get("budget_max", 0)))

    return ranked
