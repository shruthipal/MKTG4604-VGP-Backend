"""
Pydantic schemas for the buyer service.

BuyerProfileResponse — full profile returned to authenticated buyers only.
BuyerMatchSummary    — the only buyer-related object permitted in retailer responses.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ── Enums ──────────────────────────────────────────────────────────────────────

class BuyerSegment(str, Enum):
    reseller = "reseller"
    nonprofit = "nonprofit"
    smb = "smb"
    consumer = "consumer"


class BehaviorAction(str, Enum):
    viewed = "viewed"
    clicked = "clicked"
    purchased = "purchased"
    rejected = "rejected"


# ── Request schemas ────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    segment: BuyerSegment
    preferences: list[str]
    budget_min: float
    budget_max: float
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("preferences")
    @classmethod
    def preferences_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("preferences must contain at least one category")
        cleaned = [p.strip() for p in v if p.strip()]
        if not cleaned:
            raise ValueError("preferences must contain at least one non-blank category")
        if len(cleaned) > 20:
            raise ValueError("preferences cannot exceed 20 categories")
        return cleaned

    @field_validator("budget_min")
    @classmethod
    def budget_min_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("budget_min cannot be negative")
        return v

    @field_validator("budget_max")
    @classmethod
    def budget_max_gt_min(cls, v: float, info) -> float:
        budget_min = info.data.get("budget_min")
        # Allow 0 / 0 — means "free items only" (valid for nonprofit profiles)
        if budget_min is not None and budget_min == 0.0 and v == 0.0:
            return v
        if budget_min is not None and v <= budget_min:
            raise ValueError("budget_max must be greater than budget_min")
        return v


class ProfileUpdateRequest(BaseModel):
    """All fields optional — only provided fields are updated."""
    segment: Optional[BuyerSegment] = None
    preferences: Optional[list[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("preferences")
    @classmethod
    def preferences_valid(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        cleaned = [p.strip() for p in v if p.strip()]
        if not cleaned:
            raise ValueError("preferences must contain at least one non-blank category")
        if len(cleaned) > 20:
            raise ValueError("preferences cannot exceed 20 categories")
        return cleaned


class BehaviorLogRequest(BaseModel):
    action: BehaviorAction
    item_id: Optional[str] = None
    item_category: Optional[str] = None


# ── Response schemas ───────────────────────────────────────────────────────────

class BuyerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    segment: str
    preferences: list
    budget_min: float
    budget_max: float
    location: Optional[str]
    notes: Optional[str]
    embedded: bool
    created_at: datetime
    updated_at: datetime


class BehaviorLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    action: str
    item_id: Optional[str]
    item_category: Optional[str]
    created_at: datetime


class BuyerMatchSummary(BaseModel):
    """Opaque buyer summary for retailer-facing responses — no PII, no preferences."""
    buyer_id: str
    match_score: float
    match_label: str  # "Strong" | "Good" | "Moderate"

    @staticmethod
    def label_from_score(score: float) -> str:
        if score >= 0.75:
            return "Strong"
        if score >= 0.50:
            return "Good"
        return "Moderate"
