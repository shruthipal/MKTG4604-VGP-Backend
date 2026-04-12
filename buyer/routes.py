"""
Buyer routes — ALL endpoints require a valid buyer JWT (require_buyer_role).

R-02 enforcement at this layer:
  1. require_buyer_role blocks retailers at the dependency level (HTTP 403).
  2. Every response uses BuyerProfileResponse — a buyer-only schema.
  3. No route in this file may return BuyerMatchSummary; that schema is reserved
     for the match pipeline when it builds retailer-facing payloads.
  4. Behavioral history (BehaviorLog) is never returned outside this module.

POST  /buyer/onboarding         — create profile (409 if already exists)
GET   /buyer/profile            — fetch own profile
PUT   /buyer/profile            — update own profile (partial)
POST  /buyer/behavior           — log a behavior event
GET   /buyer/behavior           — fetch own behavior history (buyer-only)
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_utils import require_buyer_role
from .database import get_db
from .models import BehaviorLog, BuyerProfile
from .schemas import (
    BehaviorLogRequest,
    BehaviorLogResponse,
    BuyerProfileResponse,
    ProfileUpdateRequest,
    OnboardingRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buyer", tags=["buyer"])


# ── Onboarding ─────────────────────────────────────────────────────────────────

@router.post(
    "/onboarding",
    response_model=BuyerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create buyer profile — segment, preferences, and budget (buyer only)",
)
async def onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    """
    Creates a buyer profile and embeds it to ChromaDB.
    HTTP 409 if a profile already exists for this account.
    HTTP 400 for any missing or invalid required field.
    R-02: response schema (BuyerProfileResponse) is buyer-only.
    """
    existing = await db.execute(
        select(BuyerProfile).where(BuyerProfile.user_id == current_user["sub"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile already exists for this account. Use PUT /buyer/profile to update it.",
        )

    profile = BuyerProfile(
        user_id=current_user["sub"],
        segment=body.segment.value,
        preferences=body.preferences,
        budget_min=body.budget_min,
        budget_max=body.budget_max,
        location=body.location,
        notes=body.notes,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    logger.info(
        "Buyer profile created: user=%s segment=%s embedded=%s",
        current_user["sub"],
        profile.segment,
        profile.embedded,
    )
    return BuyerProfileResponse.model_validate(profile)


# ── Profile read ───────────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=BuyerProfileResponse,
    summary="Fetch own buyer profile (buyer only)",
)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    profile = await _get_profile_or_404(current_user["sub"], db)
    return BuyerProfileResponse.model_validate(profile)


# ── Profile update ─────────────────────────────────────────────────────────────

@router.put(
    "/profile",
    response_model=BuyerProfileResponse,
    summary="Update own buyer profile — all fields optional (buyer only)",
)
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    """
    Partial update — only provided fields are changed.
    Re-embeds the profile to ChromaDB if any field is modified.
    """
    profile = await _get_profile_or_404(current_user["sub"], db)

    updated = False
    if body.segment is not None:
        profile.segment = body.segment.value
        updated = True
    if body.preferences is not None:
        profile.preferences = body.preferences
        updated = True
    if body.budget_min is not None:
        profile.budget_min = body.budget_min
        updated = True
    if body.budget_max is not None:
        profile.budget_max = body.budget_max
        updated = True
    if body.location is not None:
        profile.location = body.location
        updated = True
    if body.notes is not None:
        profile.notes = body.notes
        updated = True

    if not updated:
        return BuyerProfileResponse.model_validate(profile)

    profile.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(profile)

    return BuyerProfileResponse.model_validate(profile)


# ── Behavior logging ───────────────────────────────────────────────────────────

@router.post(
    "/behavior",
    response_model=BehaviorLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a buyer behavior event — viewed, clicked, purchased, or rejected (buyer only)",
)
async def log_behavior(
    body: BehaviorLogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    """
    R-02: Behavior history is buyer-private and platform-internal.
    This endpoint is protected by require_buyer_role. The match pipeline
    reads behavior_logs directly from the DB for re-ranking; it is never
    surfaced to retailers.
    """
    log = BehaviorLog(
        user_id=current_user["sub"],
        action=body.action.value,
        item_id=body.item_id,
        item_category=body.item_category,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return BehaviorLogResponse.model_validate(log)


@router.get(
    "/behavior",
    response_model=list[BehaviorLogResponse],
    summary="Fetch own behavior history (buyer only)",
)
async def get_behavior(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    """R-02: History accessible only to the buyer themselves."""
    result = await db.execute(
        select(BehaviorLog)
        .where(BehaviorLog.user_id == current_user["sub"])
        .order_by(BehaviorLog.created_at.desc())
    )
    return [BehaviorLogResponse.model_validate(log) for log in result.scalars().all()]


# ── Private helper ─────────────────────────────────────────────────────────────

async def _get_profile_or_404(user_id: str, db: AsyncSession) -> BuyerProfile:
    result = await db.execute(
        select(BuyerProfile).where(BuyerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found. Complete onboarding at POST /buyer/onboarding first.",
        )
    return profile
