"""
Inventory routes — all endpoints require a valid retailer JWT (R-06 / role guard).

POST  /inventory/upload        — validate + store + embed a new item
POST  /inventory/upload/bulk   — CSV or Excel batch upload; returns per-row summary
GET   /inventory/              — list the calling retailer's own items
GET   /inventory/{item_id}     — fetch a single item (retailer must own it)
PATCH /inventory/{item_id}/status — mark sold/expired; triggers immediate R-05 de-index
"""
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_utils import require_retailer_role
from .bulk import parse_file
from .database import get_db
from .embeddings import delete_items, upsert_item
from .models import InventoryItem
from .schemas import (
    BulkUploadResponse,
    InventoryResponse,
    InventoryUploadRequest,
    RowError,
    StatusUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new inventory item (retailer only)",
)
async def upload_inventory(
    body: InventoryUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    item = InventoryItem(
        retailer_id=current_user["sub"],
        title=body.title,
        category=body.category,
        quantity=body.quantity,
        price=body.price,
        condition=body.condition.value,
        expiry_date=body.expiry_date,
        description=body.description,
        location=body.location,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Attempt ChromaDB embed (1.5 s timeout — R-03)
    item_data = {
        "retailer_id": item.retailer_id,
        "title": item.title,
        "category": item.category,
        "condition": item.condition,
        "price": item.price,
        "quantity": item.quantity,
        "description": item.description,
        "location": item.location,
        "status": item.status,
    }
    embedded = await upsert_item(item.id, item_data)

    if embedded:
        item.embedded = True
        item.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(item)

    return InventoryResponse.model_validate(item)


# ── Bulk upload ────────────────────────────────────────────────────────────────

@router.post(
    "/upload/bulk",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch upload inventory from a CSV or Excel file (retailer only)",
)
async def bulk_upload_inventory(
    file: UploadFile = File(..., description="A .csv or .xlsx file. Headers must include: title, category, quantity (or qty), price, condition, expiry_date."),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    """
    Accepts CSV (.csv) or Excel (.xlsx/.xls). Rows are validated independently —
    a failure on one row does not block others. Returns BulkUploadResponse with
    counts and per-row error detail.
    """
    # 1. Parse file
    filename = file.filename or "upload"
    content = await file.read()

    try:
        rows = parse_file(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains no data rows.",
        )

    # 2. Validate rows
    valid: list[tuple[int, dict, InventoryUploadRequest]] = []  # (row_num, raw, parsed)
    row_errors: list[RowError] = []

    for row_num, raw in rows:
        try:
            parsed = InventoryUploadRequest.model_validate(raw)
            valid.append((row_num, raw, parsed))
        except ValidationError as exc:
            messages = [
                f"{' → '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
                if e.get("loc")
                else e["msg"]
                for e in exc.errors()
            ]
            row_errors.append(RowError(row=row_num, raw_data=raw, errors=messages))

    # 3. Insert to DB
    inserted: list[InventoryItem] = []

    for _row_num, _raw, parsed in valid:
        item = InventoryItem(
            retailer_id=current_user["sub"],
            title=parsed.title,
            category=parsed.category,
            quantity=parsed.quantity,
            price=parsed.price,
            condition=parsed.condition.value,
            expiry_date=parsed.expiry_date,
            description=parsed.description,
            location=parsed.location,
        )
        db.add(item)
        inserted.append(item)

    if inserted:
        await db.commit()
        for item in inserted:
            await db.refresh(item)

    # 4. Embed to ChromaDB
    async def _embed_one(item: InventoryItem) -> bool:
        item_data = {
            "retailer_id": item.retailer_id,
            "title": item.title,
            "category": item.category,
            "condition": item.condition,
            "price": item.price,
            "quantity": item.quantity,
            "description": item.description,
            "location": item.location,
            "status": item.status,
        }
        return await upsert_item(item.id, item_data)

    if inserted:
        embed_results: list[bool] = await asyncio.gather(*[_embed_one(i) for i in inserted])

        now = datetime.now(timezone.utc)
        any_embedded = False
        for item, did_embed in zip(inserted, embed_results):
            if did_embed:
                item.embedded = True
                item.updated_at = now
                any_embedded = True

        if any_embedded:
            await db.commit()

        embedded_count = sum(embed_results)
        if embedded_count < len(inserted):
            logger.warning(
                "[R-03] Bulk upload: %d/%d items embedded immediately; "
                "%d will be indexed on next cleanup pass.",
                embedded_count,
                len(inserted),
                len(inserted) - embedded_count,
            )

    logger.info(
        "Bulk upload by retailer %s — file: %s, rows: %d, ok: %d, failed: %d",
        current_user["sub"],
        filename,
        len(rows),
        len(inserted),
        len(row_errors),
    )

    return BulkUploadResponse(
        filename=filename,
        total_rows=len(rows),
        successful=len(inserted),
        failed=len(row_errors),
        uploaded_item_ids=[item.id for item in inserted],
        errors=row_errors,
    )


# ── List ───────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[InventoryResponse],
    summary="List all inventory items belonging to the calling retailer",
)
async def list_my_inventory(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.retailer_id == current_user["sub"])
    )
    return [InventoryResponse.model_validate(i) for i in result.scalars().all()]


# ── Detail ─────────────────────────────────────────────────────────────────────

@router.get(
    "/{item_id}",
    response_model=InventoryResponse,
    summary="Fetch a single inventory item (must be owned by calling retailer)",
)
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    item = await _get_owned_item(item_id, current_user["sub"], db)
    return InventoryResponse.model_validate(item)


# ── Status update (triggers R-05 on sold/expired) ─────────────────────────────

@router.patch(
    "/{item_id}/status",
    response_model=InventoryResponse,
    summary="Mark an item as sold or expired — immediately de-indexes from ChromaDB (R-05)",
)
async def update_item_status(
    item_id: str,
    body: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    """Immediately de-indexes from ChromaDB when status changes to sold/expired."""
    item = await _get_owned_item(item_id, current_user["sub"], db)

    item.status = body.status.value
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()

    if item.embedded:
        await delete_items([item.id])
        item.embedded = False
        item.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            "De-indexed item %s (status: %s, retailer: %s).",
            item_id,
            body.status.value,
            current_user["sub"],
        )

    await db.refresh(item)
    return InventoryResponse.model_validate(item)


# ── Private helpers ────────────────────────────────────────────────────────────

async def _get_owned_item(
    item_id: str, retailer_id: str, db: AsyncSession
) -> InventoryItem:
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.retailer_id == retailer_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
