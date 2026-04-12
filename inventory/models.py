import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from .database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    retailer_id = Column(String, nullable=False, index=True)  # JWT sub
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    condition = Column(String, nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, nullable=False, default="available")
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
