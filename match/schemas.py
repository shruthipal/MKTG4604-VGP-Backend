"""
Pydantic schemas for the match pipeline.

RecommendationCard    — buyer-facing match result with LLM recommendation text.
RetailerAlertResponse — retailer-facing alert; contains no buyer data.
MatchResponse         — wraps RecommendationCard list for the buyer response.
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
    retailer_id: str
    similarity_score: float
    composite_score: float
    recommendation_text: str


class MatchResponse(BaseModel):
    """Top-5 recommendations returned to the buyer after the full pipeline."""
    recommendations: list[RecommendationCard]
    buyer_segment: str
    total_found: int
    generated_at: datetime
    served_from_cache: bool


# ── Business-facing (buyer demand search) ─────────────────────────────────────

class BuyerInterestCard(BaseModel):
    """One buyer/org interested in a given surplus item type — shown on business side."""
    org_name: str
    segment: str          # "nonprofit" | "reseller" | "smb"
    location: Optional[str]
    wants: str            # human-readable summary of what they want
    preferences: list[str]
    match_strength: str   # "Strong" | "Good" | "Moderate"


class BuyerSearchResponse(BaseModel):
    buyers: list[BuyerInterestCard]
    total_found: int
    query: str


# ── Retailer-facing ────────────────────────────────────────────────────────────

class RetailerAlertResponse(BaseModel):
    """Retailer dashboard alert — contains no buyer data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    item_title: str
    match_score_label: str  # "Strong" | "Good" | "Moderate"
    match_count: int
    is_read: bool
    created_at: datetime
