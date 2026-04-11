"""
R-02 schema boundary
─────────────────────────────────────────────────────────────────────────────
BuyerProfileResponse  — full profile; ONLY returned on buyer-authenticated routes.
BuyerMatchSummary     — the ONLY buyer-related object permitted in retailer-facing
                        contexts. Contains no segment, no preferences, no history,
                        no PII. Match pipeline must use this type exclusively when
                        building retailer responses.
─────────────────────────────────────────────────────────────────────────────
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
    """
    Full buyer profile — BUYER-ONLY. Must never be returned on a retailer route.
    R-02: enforce with require_buyer_role on every route that returns this type.
    """
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
    """
    R-02 compliant summary — the ONLY buyer-related object that may be included
    in retailer-facing API responses or dashboard payloads.

    Structural guarantee: this schema has NO segment, NO preferences, NO budget,
    NO behavioral history, NO email, NO location. Adding any of those fields here
    is a R-02 violation.

    buyer_id is an opaque internal platform ID — not the user's email or name.
    """
    buyer_id: str          # opaque platform ID only — no PII
    match_score: float     # 0.0 – 1.0 cosine similarity
    match_label: str       # "Strong" | "Good" | "Moderate"

    @staticmethod
    def label_from_score(score: float) -> str:
        if score >= 0.75:
            return "Strong"
        if score >= 0.50:
            return "Good"
        return "Moderate"
