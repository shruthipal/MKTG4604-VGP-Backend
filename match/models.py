"""Match pipeline database models — MatchResult and RetailerAlert."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from .database import Base


class MatchResult(Base):
    """Audit log of every recommendation served — used for analytics and CTR tracking."""
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
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
    """Dashboard notification for retailers — stores match label only, no buyer data."""
    __tablename__ = "retailer_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    retailer_id = Column(String, nullable=False, index=True)
    item_id = Column(String, nullable=False, index=True)
    item_title = Column(String, nullable=False)  # denormalized to avoid joining buyer data
    match_score_label = Column(String, nullable=False)
    match_count = Column(Integer, nullable=False, default=1)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
