"""
R-02 notice: Both tables in this module are BUYER-PRIVATE.
- BuyerProfile: segment, preferences, and budget are never returned to retailers.
- BehaviorLog: interaction history is never returned to retailers.
Only BuyerMatchSummary (defined in schemas.py) may appear in retailer-facing responses.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String, Text

from .database import Base


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # user_id maps to JWT sub — unique per account
    user_id = Column(String, unique=True, nullable=False, index=True)

    # ── Required profile fields ────────────────────────────────────────────
    # segment: reseller | nonprofit | smb | consumer
    segment = Column(String, nullable=False)
    # preferences: JSON list of category strings e.g. ["electronics","apparel"]
    preferences = Column(JSON, nullable=False)
    budget_min = Column(Float, nullable=False)
    budget_max = Column(Float, nullable=False)

    # ── Optional ───────────────────────────────────────────────────────────
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    # ── Internal state ─────────────────────────────────────────────────────
    # True once successfully upserted into ChromaDB buyer_profiles collection
    embedded = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BehaviorLog(Base):
    """
    R-02: Behavioral history is platform-internal only.
    Never surfaced to retailers in any form.
    Used by the Match pipeline to re-rank recommendations for a buyer.
    """
    __tablename__ = "behavior_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    # action: viewed | clicked | purchased | rejected
    action = Column(String, nullable=False)
    item_id = Column(String, nullable=True)
    item_category = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
