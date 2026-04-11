from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ItemCondition(str, Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"
    poor = "poor"


class ItemStatus(str, Enum):
    available = "available"
    sold = "sold"
    expired = "expired"


class InventoryUploadRequest(BaseModel):
    """
    All five spec fields are required. Pydantic raises HTTP 422 automatically
    for missing keys; the app's exception handler converts those to HTTP 400.
    """

    title: str
    category: str
    quantity: int
    price: float
    condition: ItemCondition
    expiry_date: datetime
    description: Optional[str] = None
    location: Optional[str] = None

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("expiry_date")
    @classmethod
    def expiry_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= datetime.now(timezone.utc):
            raise ValueError("expiry_date must be in the future")
        return v


class StatusUpdateRequest(BaseModel):
    status: ItemStatus

    @field_validator("status")
    @classmethod
    def cannot_reactivate(cls, v: ItemStatus) -> ItemStatus:
        if v == ItemStatus.available:
            raise ValueError("Cannot manually set status back to 'available'")
        return v


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    retailer_id: str
    title: str
    category: str
    quantity: int
    price: float
    condition: str
    expiry_date: datetime
    description: Optional[str]
    location: Optional[str]
    status: str
    embedded: bool
    created_at: datetime
    updated_at: datetime


# ── Bulk upload schemas ────────────────────────────────────────────────────────

class RowError(BaseModel):
    """Details of a single row that failed validation during bulk upload."""
    row: int             # 1-indexed data row number (header not counted)
    raw_data: dict       # normalized cell values as parsed from the file
    errors: list[str]    # human-readable validation error messages


class BulkUploadResponse(BaseModel):
    """Summary returned after processing a CSV or Excel bulk upload."""
    filename: str
    total_rows: int           # data rows parsed (empty rows excluded)
    successful: int           # rows stored to DB (ChromaDB embed may be pending)
    failed: int               # rows that failed validation
    uploaded_item_ids: list[str]  # IDs of successfully created InventoryItems
    errors: list[RowError]    # one entry per failed row
