"""
Composite scoring, ranking, and segment-specific filtering.

Scoring formula (each additive, result clamped to [0.0, 1.0]):
  base       = keyword similarity (neutral 0.5 for all keyword matches)
  price fit  = +0.10 in-budget | +0.05 below budget | -0.20 over budget | +0.10 free
  quantity   = +0.05 if qty >= 10 | -0.50 if qty == 0
  rejection  = -0.30 if retailer has >= 3 same-segment rejections

Nonprofit sort override: after scoring, free items surface first, then discounted
(price <= 25% of budget_max), then the rest sorted by composite score.
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

    if price == 0:
        score += 0.10
    elif budget_min <= price <= budget_max:
        score += 0.10
    elif price < budget_min:
        score += 0.05
    else:
        score -= 0.20

    qty = int(item.get("quantity", 0))
    if qty == 0:
        score -= 0.50
    elif qty >= 10:
        score += 0.05

    retailer_id = str(item.get("retailer_id", ""))
    rejection_count = rejection_counts.get(retailer_id, 0)
    if rejection_count >= 3:
        score -= 0.30
        logger.debug("De-prioritized retailer %s (segment rejections: %d)", retailer_id, rejection_count)

    return max(0.0, min(1.0, score))


def _nonprofit_reorder(ranked: list[RankedItem], budget_max: float) -> list[RankedItem]:
    """
    Nonprofits always see free/discounted items first.
    Discount threshold: price <= 25% of budget_max.
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
        "Nonprofit reorder — free: %d, discounted: %d, regular: %d",
        len(free), len(discounted), len(regular),
    )
    return free + discounted + regular


def rank_and_filter(
    ids: list[str],
    distances: list[float],
    inventory: dict[str, dict],
    buyer: dict,
    rejection_counts: dict[str, int],
) -> list[RankedItem]:
    """
    Score and sort results by composite_score, then apply nonprofit reorder.
    Items missing from inventory (sold/expired since search) are silently skipped.
    """
    ranked: list[RankedItem] = []

    for item_id, distance in zip(ids, distances):
        item_data = inventory.get(item_id)
        if not item_data:
            continue  # sold/expired since search — skip

        similarity = max(0.0, 1.0 - float(distance))  # cosine distance → similarity
        composite = compute_composite_score(similarity, item_data, buyer, rejection_counts)
        ranked.append(RankedItem(item_id, item_data, similarity, composite))

    # Sort by composite score descending
    ranked.sort(key=lambda r: r.composite_score, reverse=True)

    # R-01: nonprofit sort override
    if buyer.get("segment") == "nonprofit":
        ranked = _nonprofit_reorder(ranked, float(buyer.get("budget_max", 0)))

    return ranked
