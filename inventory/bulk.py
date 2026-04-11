"""
File parsing utilities for the bulk upload endpoint.

Supported formats : .csv, .xlsx, .xls
Encoding          : UTF-8 / UTF-8-BOM for CSV; openpyxl for Excel
Row numbering     : 1-indexed, header row excluded, so row 1 = first data row

Header normalization
────────────────────
Headers are stripped, lowercased, and matched against a set of known aliases so
that common variations ("Qty", "qty", "QTY", "expiry", "Expiration Date", etc.)
are accepted without requiring an exact match.

Canonical field names after normalization:
  title, category, quantity, price, condition, expiry_date,
  description, location   (last two are optional)

Date pre-parsing
────────────────
Pydantic expects ISO 8601 for datetime fields. CSV values are often plain dates
("2025-12-31", "12/31/2025"). _parse_date_str() tries common formats and emits a
UTC-aware ISO string so Pydantic validation succeeds. On failure, the raw string
is passed through — Pydantic's error message will surface the problem clearly.

Excel cells that already contain datetime objects are converted directly.
Completely empty rows (all values None / blank) are silently skipped.
"""
import csv
import io
import logging
from datetime import datetime, timezone

import openpyxl

logger = logging.getLogger(__name__)

# ── Header aliases ─────────────────────────────────────────────────────────────

_ALIASES: dict[str, str] = {
    "qty": "quantity",
    "expiry": "expiry_date",
    "expiration": "expiry_date",
    "expiration_date": "expiry_date",
    "exp_date": "expiry_date",
    "expire_date": "expiry_date",
    "expires": "expiry_date",
    "desc": "description",
    "loc": "location",
    "name": "title",
    "item_name": "title",
    "item_title": "title",
    "cat": "category",
    "cond": "condition",
    "unit_price": "price",
    "cost": "price",
    "amount": "quantity",
    "stock": "quantity",
    "units": "quantity",
}

# ── Date format candidates ─────────────────────────────────────────────────────

_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d-%b-%Y",  # e.g. 31-Dec-2025
    "%B %d, %Y",  # e.g. December 31, 2025
]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _normalize_key(k: str) -> str:
    """Lowercase, strip, replace spaces/dashes with underscores, then alias-map."""
    k = k.strip().lower().replace(" ", "_").replace("-", "_")
    return _ALIASES.get(k, k)


def _parse_date_str(value: str) -> str:
    """
    Try common date formats and return a UTC-aware ISO 8601 string.
    Returns the original string unchanged if nothing matches — Pydantic will
    raise a descriptive validation error downstream.
    """
    value = value.strip()
    # Already has timezone info — pass through
    if "+" in value or value.endswith("Z"):
        return value
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return value  # pass through for Pydantic to reject with a clear message


def _coerce_cell(key: str, value) -> object:
    """
    Normalize a single cell value:
      - Strip whitespace from strings; convert empty strings to None
      - Pre-parse date strings for the expiry_date field
      - Convert Excel datetime objects to UTC ISO strings
    """
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if key == "expiry_date":
            return _parse_date_str(value)
    elif isinstance(value, datetime):
        if key == "expiry_date":
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat()
    elif value is None:
        return None
    return value


def _normalize_row(raw: dict) -> dict:
    """Apply key normalization and cell coercion to one row dict."""
    return {
        _normalize_key(k): _coerce_cell(_normalize_key(k), v)
        for k, v in raw.items()
        if k is not None  # openpyxl can produce None header keys
    }


def _is_empty_row(row: dict) -> bool:
    """True if every value in the row is None or blank — skip these silently."""
    return all(v is None or v == "" for v in row.values())


# ── Public parsers ─────────────────────────────────────────────────────────────

def parse_csv(content: bytes) -> list[tuple[int, dict]]:
    """
    Parse CSV bytes into a list of (row_number, normalized_dict).
    Row numbers are 1-indexed, header excluded.
    Handles UTF-8-BOM exported from Excel.
    """
    text = content.decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))
    rows: list[tuple[int, dict]] = []
    for i, raw in enumerate(reader, start=1):
        normalized = _normalize_row(dict(raw))
        if not _is_empty_row(normalized):
            rows.append((i, normalized))
    return rows


def parse_excel(content: bytes) -> list[tuple[int, dict]]:
    """
    Parse Excel (.xlsx / .xls) bytes into a list of (row_number, normalized_dict).
    Uses the active worksheet; reads headers from the first row.
    Row numbers are 1-indexed, header excluded.
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    row_iter = ws.iter_rows(values_only=True)

    # First row = headers
    try:
        raw_headers = next(row_iter)
    except StopIteration:
        return []  # empty sheet

    headers = [str(h).strip() if h is not None else f"_col{j}" for j, h in enumerate(raw_headers)]

    rows: list[tuple[int, dict]] = []
    for i, cells in enumerate(row_iter, start=1):
        raw = {headers[j]: cell for j, cell in enumerate(cells) if j < len(headers)}
        normalized = _normalize_row(raw)
        if not _is_empty_row(normalized):
            rows.append((i, normalized))
    return rows


def parse_file(filename: str, content: bytes) -> list[tuple[int, dict]]:
    """
    Dispatch to the correct parser based on file extension.
    Raises ValueError for unsupported file types.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "csv":
        return parse_csv(content)
    if ext in ("xlsx", "xls"):
        return parse_excel(content)
    raise ValueError(
        f"Unsupported file type '.{ext}'. "
        "Upload a .csv or .xlsx file."
    )
