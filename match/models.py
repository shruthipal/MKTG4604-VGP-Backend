"""
Match pipeline DB models.

MatchResult — one row per recommendation card delivered to a buyer.
              buyer_user_id is stored for analytics (sell-through, CTR tracking).
              R-02: buyer_user_id is NEVER forwarded to retailers.

RetailerAlert — dashboard notification for a retailer when one of their items
                is matched to a buyer. Contains no buyer data whatsoever (R-02).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from .database import Base


class MatchResult(Base):
    """Audit log of every recommendation served — used for analytics KPIs."""
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # R-02: internal only — never returned to retailers
    buyer_user_id = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    recommendation_text = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RetailerAlert(Base):
    """
    R-02 compliant dashboard alert for retailers.
    Stores match_score_label only — no segment, no buyer_id, no preferences.
    """
    __tablename__ = "retailer_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    retailer_id = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=False, index=True)
    # Denormalized title so dashboard renders without a join on buyer-side data
    item_title = Column(String, nullable=False)
    # R-02: score summary only (Strong / Good / Moderate) — no raw buyer metrics
    match_score_label = Column(String, nullable=False)
    match_count = Column(Integer, nullable=False, default=1)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
