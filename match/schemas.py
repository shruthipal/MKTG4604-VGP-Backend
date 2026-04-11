"""
R-02 schema boundary — match pipeline
──────────────────────────────────────────────────────────────────────────────
RecommendationCard    → returned to BUYER only (buyer-authenticated route).
                        Contains item info + LLM rec text. No buyer data leaked back.
RetailerAlertResponse → returned to RETAILER dashboard (retailer-authenticated route).
                        Contains item info + match_score_label ONLY.
                        Structurally cannot contain: buyer_id, segment, preferences,
                        budget, behavioral history, or any other buyer attribute.
MatchResponse         → wraps RecommendationCard list for buyer response.
──────────────────────────────────────────────────────────────────────────────
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Buyer-facing ───────────────────────────────────────────────────────────────

class RecommendationCard(BaseModel):
    """One matched inventory item with LLM-generated recommendation text."""
    item_id: str
    title: str
    category: str
    price: float
    condition: str
    quantity: int
    retailer_id: str        # item provenance — not buyer data
    similarity_score: float  # cosine similarity (0–1)
    composite_score: float   # weighted composite (0–1)
    recommendation_text: str # segment-aware LLM output (R-01 enforced in prompt)


class MatchResponse(BaseModel):
    """Top-5 recommendations returned to the buyer after the full pipeline."""
    recommendations: list[RecommendationCard]
    buyer_segment: str   # echoed back to buyer — fine, it's their own data
    total_found: int
    generated_at: datetime
    served_from_cache: bool


# ── Retailer-facing ────────────────────────────────────────────────────────────

class RetailerAlertResponse(BaseModel):
    """
    R-02 compliant dashboard alert.

    This is the ONLY match-pipeline object returned to retailers.
    It contains NO buyer_id, NO segment, NO preferences, NO budget, NO history.
    match_score_label is the only buyer-derived value — expressed as a category
    (Strong / Good / Moderate), never as a raw score or buyer attribute.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    item_title: str          # retailer's own item — not buyer data
    match_score_label: str   # "Strong" | "Good" | "Moderate"
    match_count: int         # how many buyer matches hit this item
    is_read: bool
    created_at: datetime
