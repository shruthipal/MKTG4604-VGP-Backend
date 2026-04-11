#!/usr/bin/env python3
"""
VGP Platform — Boston Demo Data Seeder
═══════════════════════════════════════
Populates Auth, Inventory, and Buyer services with realistic Greater Boston data.

Prerequisites
─────────────
  pip install httpx
  # From vgp-platform/ — start all three services:
  uvicorn auth.main:app --port 8000 &
  uvicorn inventory.main:app --port 8001 &
  uvicorn buyer.main:app --port 8002 &

Usage
─────
  cd vgp-platform
  python scripts/seed.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed.  Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

# ── Service base URLs ─────────────────────────────────────────────────────────
AUTH = "http://localhost:8000"
INV  = "http://localhost:8001"
BYR  = "http://localhost:8002"

PASSWORD    = "Test1234!"
TIMEOUT     = 30.0
CONCURRENCY = 4          # semaphore cap — keeps SQLite happy under concurrent writes

# ── Helpers ───────────────────────────────────────────────────────────────────

def _exp(days: int) -> str:
    """UTC ISO datetime string N days from now."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _ok(msg: str)   -> None: print(f"    ✓  {msg}")
def _skip(msg: str) -> None: print(f"    ~  {msg}  (already exists — skipped)")
def _warn(msg: str) -> None: print(f"    ⚠  {msg}")
def _err(msg: str)  -> None: print(f"    ✗  {msg}", file=sys.stderr)

# ── Static demo data ──────────────────────────────────────────────────────────

RETAILERS: list[dict] = [
    {"email": "dunkin@demo.com",       "name": "Dunkin"},
    {"email": "wholefoods@demo.com",   "name": "Whole Foods"},
    {"email": "stopshop@demo.com",     "name": "Stop & Shop"},
    {"email": "marketbasket@demo.com", "name": "Market Basket"},
    {"email": "hm@demo.com",           "name": "H&M"},
    {"email": "newbalance@demo.com",   "name": "New Balance"},
    {"email": "tjx@demo.com",          "name": "TJX Companies"},
    {"email": "tatte@demo.com",        "name": "Tatte Bakery"},
    {"email": "mikespastry@demo.com",  "name": "Mike's Pastry"},
    {"email": "bostonbeer@demo.com",   "name": "Boston Beer Company"},
    {"email": "polar@demo.com",        "name": "Polar Beverages"},
    {"email": "cvs@demo.com",          "name": "CVS Health"},
    {"email": "staples@demo.com",      "name": "Staples"},
    {"email": "bose@demo.com",         "name": "Bose"},
]

# Keyed by retailer email; each value is a list of item dicts for that retailer
INVENTORY: dict[str, list[dict]] = {
    "dunkin@demo.com": [
        {
            "title": "Surplus Assorted Pastries",
            "category": "Food & Beverage",
            "quantity": 500,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": (
                "Assorted surplus pastries from Dunkin locations across Greater Boston "
                "— donuts, muffins, and croissants. Packaged same-day."
            ),
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Dunkin Coffee Cups (Sealed Cases)",
            "category": "Food & Beverage",
            "quantity": 300,
            "price": 0.75,
            "condition": "new",
            "expiry_date": _exp(90),
            "description": (
                "Surplus sealed coffee cup cases from Dunkin supply chain overstock. "
                "New, unopened."
            ),
            "location": "Canton, MA",
        },
    ],
    "wholefoods@demo.com": [
        {
            "title": "Organic Produce Surplus",
            "category": "Produce",
            "quantity": 400,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(14),
            "description": (
                "Mixed organic produce surplus from Whole Foods Boston-area stores "
                "— seasonal vegetables and fruits, cosmetically imperfect but fully edible."
            ),
            "location": "Cambridge, MA",
        },
        {
            "title": "Surplus Canned Goods",
            "category": "Canned Goods",
            "quantity": 200,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": (
                "Assorted surplus canned goods from Whole Foods Boston stores "
                "— beans, soups, vegetables. Label changes cleared for redistribution."
            ),
            "location": "Cambridge, MA",
        },
    ],
    "stopshop@demo.com": [
        {
            "title": "Packaged Groceries Surplus",
            "category": "Packaged Groceries",
            "quantity": 600,
            "price": 1.00,
            "condition": "good",
            "expiry_date": _exp(60),
            "description": (
                "Assorted packaged grocery surplus from Stop & Shop stores across "
                "Greater Boston — crackers, cereals, snack foods, pasta."
            ),
            "location": "Quincy, MA",
        },
        {
            "title": "Dairy Products Surplus",
            "category": "Dairy",
            "quantity": 300,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(10),
            "description": (
                "Surplus dairy products from Stop & Shop Boston stores "
                "— milk, yogurt, and cheese nearing sell-by date but fully safe."
            ),
            "location": "Quincy, MA",
        },
    ],
    "marketbasket@demo.com": [
        {
            "title": "Bulk Dry Goods Surplus",
            "category": "Bulk Dry Goods",
            "quantity": 800,
            "price": 0.80,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": (
                "Bulk dry goods surplus from Market Basket regional distribution "
                "— rice, flour, pasta, and grains. Ideal for food banks and bulk buyers."
            ),
            "location": "Tewksbury, MA",
        },
        {
            "title": "Household Essentials Surplus",
            "category": "Household Essentials",
            "quantity": 400,
            "price": 1.20,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": (
                "Surplus household essentials from Market Basket — cleaning supplies, "
                "paper goods, and laundry products from overstock clearance."
            ),
            "location": "Tewksbury, MA",
        },
    ],
    "hm@demo.com": [
        {
            "title": "Excess Apparel — Mixed Sizes",
            "category": "Apparel",
            "quantity": 500,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Excess new apparel from H&M seasonal inventory clearance "
                "— mixed sizes and styles, original tags still attached. "
                "Includes tops, bottoms, and outerwear."
            ),
            "location": "Boston, MA",
        },
    ],
    "newbalance@demo.com": [
        {
            "title": "Surplus New Balance Athletic Shoes",
            "category": "Athletic Footwear",
            "quantity": 200,
            "price": 25.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Surplus New Balance athletic shoes from Boston HQ "
                "— various styles and sizes from discontinued lines. "
                "Factory new, original boxes."
            ),
            "location": "Brighton, MA",
        },
        {
            "title": "Surplus New Balance Athletic Apparel",
            "category": "Athletic Apparel",
            "quantity": 300,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Excess New Balance athletic apparel from Brighton campus "
                "— running shirts, shorts, and leggings. New with tags."
            ),
            "location": "Brighton, MA",
        },
    ],
    "tjx@demo.com": [
        {
            "title": "Mixed Clothing Surplus",
            "category": "Apparel",
            "quantity": 400,
            "price": 8.00,
            "condition": "like_new",
            "expiry_date": _exp(365),
            "description": (
                "Mixed clothing surplus from TJX companies — assorted styles and sizes "
                "from TJ Maxx and Marshalls inventory transitions. Like-new condition."
            ),
            "location": "Framingham, MA",
        },
        {
            "title": "Home Goods Surplus",
            "category": "Home Goods",
            "quantity": 300,
            "price": 6.00,
            "condition": "like_new",
            "expiry_date": _exp(365),
            "description": (
                "Home goods surplus from TJX — kitchenware, décor, and bedding "
                "from TJ Maxx and HomeGoods inventory overstock."
            ),
            "location": "Framingham, MA",
        },
    ],
    "tatte@demo.com": [
        {
            "title": "Surplus Tatte Pastries",
            "category": "Food & Beverage",
            "quantity": 100,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": (
                "Daily surplus pastries from Tatte Bakery Boston locations "
                "— kouign-amann, croissants, and galettes des rois. Baked fresh."
            ),
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Artisan Sourdough Bread",
            "category": "Food & Beverage",
            "quantity": 50,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": (
                "Surplus artisan sourdough and specialty breads from Tatte Bakery "
                "— baked fresh daily, surplus after close."
            ),
            "location": "Boston, MA",
        },
    ],
    "mikespastry@demo.com": [
        {
            "title": "Surplus Cannoli — Assorted Flavors",
            "category": "Food & Beverage",
            "quantity": 150,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": (
                "Surplus cannoli from Mike's Pastry North End location "
                "— traditional, chocolate, and pistachio flavors."
            ),
            "location": "Boston, MA (North End)",
        },
        {
            "title": "Surplus Italian Cookies",
            "category": "Food & Beverage",
            "quantity": 100,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": (
                "Assorted surplus Italian cookies from Mike's Pastry "
                "— pignoli, rainbow, and anisette varieties."
            ),
            "location": "Boston, MA (North End)",
        },
    ],
    "bostonbeer@demo.com": [
        {
            "title": "Samuel Adams Beer Cases — Seasonal Surplus",
            "category": "Beverages",
            "quantity": 500,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(90),
            "description": (
                "Surplus Samuel Adams beer cases from Boston Beer Company "
                "— seasonal variety packs and flagship brews cleared for redistribution."
            ),
            "location": "Jamaica Plain, MA",
        },
    ],
    "polar@demo.com": [
        {
            "title": "Polar Sparkling Water — Surplus Cases",
            "category": "Beverages",
            "quantity": 600,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": (
                "Surplus Polar Beverages sparkling water cases from Worcester production "
                "— assorted flavors including lime, cranberry-lime, and raspberry."
            ),
            "location": "Worcester, MA",
        },
    ],
    "cvs@demo.com": [
        {
            "title": "Surplus Health & Wellness Products",
            "category": "Health & Wellness",
            "quantity": 300,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": (
                "Surplus health and wellness products from CVS Boston-area stores "
                "— first aid, personal care, and OTC items. Sealed and unexpired."
            ),
            "location": "Woonsocket, RI (distributed from Boston)",
        },
        {
            "title": "Surplus Vitamins & Dietary Supplements",
            "category": "Vitamins & Supplements",
            "quantity": 200,
            "price": 8.00,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": (
                "Surplus vitamins and dietary supplements from CVS inventory "
                "— sealed, unexpired, assorted national brands."
            ),
            "location": "Boston, MA",
        },
    ],
    "staples@demo.com": [
        {
            "title": "Surplus Office Supplies",
            "category": "Office Supplies",
            "quantity": 400,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Surplus office supplies from Staples Boston-area stores "
                "— pens, paper, folders, binders, and sticky notes. New in packaging."
            ),
            "location": "Framingham, MA",
        },
        {
            "title": "Surplus Electronics & Accessories",
            "category": "Electronics",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Surplus electronics from Staples overstock "
                "— USB drives, cables, keyboards, and webcams. New in box."
            ),
            "location": "Framingham, MA",
        },
    ],
    "bose@demo.com": [
        {
            "title": "Surplus Bose Headphones",
            "category": "Electronics",
            "quantity": 100,
            "price": 40.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": (
                "Surplus Bose headphones from Framingham HQ "
                "— new units from product line transitions. Original packaging."
            ),
            "location": "Framingham, MA",
        },
    ],
}

# Buyer records: includes auth fields + profile fields
BUYERS: list[dict] = [
    # ── Nonprofits ─────────────────────────────────────────────────────────
    {
        "email": "gbfb@demo.com",
        "name": "Greater Boston Food Bank",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Produce", "Canned Goods", "Packaged Groceries",
                "Bulk Dry Goods", "Dairy", "Food & Beverage",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Largest hunger-relief organization in New England. Distributes food "
                "to 190 partner agencies across Eastern Massachusetts. "
                "All food categories accepted."
            ),
        },
    },
    {
        "email": "spoonfuls@demo.com",
        "name": "Spoonfuls",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Food & Beverage", "Produce", "Canned Goods",
                "Packaged Groceries", "Dairy",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Somerville, MA",
            "notes": (
                "Rescues surplus food from grocery stores, institutions, and caterers "
                "to redirect to hunger-relief agencies across Greater Boston."
            ),
        },
    },
    {
        "email": "foodforfree@demo.com",
        "name": "Food For Free",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Produce", "Canned Goods", "Dairy",
                "Packaged Groceries", "Bulk Dry Goods",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Cambridge, MA",
            "notes": (
                "Provides free food to low-income individuals and families "
                "in Cambridge and Greater Boston. Focus on nutritious staples."
            ),
        },
    },
    {
        "email": "rosies@demo.com",
        "name": "Rosie's Place",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Apparel", "Household Essentials", "Health & Wellness",
                "Home Goods", "Clothing",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Sanctuary for poor and homeless women in Boston. "
                "Needs clothing, hygiene products, and household items for residents."
            ),
        },
    },
    {
        "email": "stfrancis@demo.com",
        "name": "St. Francis House",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Apparel", "Food & Beverage", "Health & Wellness",
                "Household Essentials", "Clothing",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Provides meals, shelter, and supportive services to adults "
                "experiencing homelessness in downtown Boston."
            ),
        },
    },
    {
        "email": "abcd@demo.com",
        "name": "ABCD Food Access",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Produce", "Packaged Groceries", "Canned Goods",
                "Dairy", "Food & Beverage", "Bulk Dry Goods",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Action for Boston Community Development — provides emergency food "
                "assistance and nutrition support to low-income Boston residents."
            ),
        },
    },
    {
        "email": "goodwill@demo.com",
        "name": "Goodwill Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Apparel", "Home Goods", "Athletic Apparel",
                "Athletic Footwear", "Household Essentials",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Collects and resells donated goods to fund job training and "
                "employment programs in Greater Boston. Strong interest in apparel "
                "and home goods."
            ),
        },
    },
    {
        "email": "stvincent@demo.com",
        "name": "St. Vincent de Paul",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": [
                "Apparel", "Home Goods", "Household Essentials",
                "Food & Beverage", "Clothing",
            ],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": (
                "Provides material assistance — food, clothing, and household goods "
                "— to families in need across Massachusetts."
            ),
        },
    },
    # ── Resellers ──────────────────────────────────────────────────────────
    {
        "email": "tgtg@demo.com",
        "name": "Too Good To Go",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": [
                "Food & Beverage", "Produce", "Packaged Groceries",
                "Canned Goods", "Dairy", "Bulk Dry Goods",
            ],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": (
                "App-based surplus food rescue platform. Looking for near-expiry "
                "and surplus food lots to redistribute via consumer surprise bags."
            ),
        },
    },
    {
        "email": "flashfood@demo.com",
        "name": "Flashfood",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": [
                "Packaged Groceries", "Canned Goods", "Produce",
                "Dairy", "Food & Beverage",
            ],
            "budget_min": 1000.0,
            "budget_max": 8000.0,
            "location": "Boston, MA",
            "notes": (
                "Grocery savings app connecting shoppers with near-expiry items "
                "at deep discounts. Primarily interested in packaged grocery items."
            ),
        },
    },
    {
        "email": "foodrescue@demo.com",
        "name": "Food Rescue US",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": [
                "Food & Beverage", "Produce", "Canned Goods",
                "Packaged Groceries", "Dairy", "Bulk Dry Goods",
            ],
            "budget_min": 0.0,
            "budget_max": 2000.0,
            "location": "Boston, MA",
            "notes": (
                "Technology-enabled food rescue connecting donors with nonprofits. "
                "Primarily sourcing all food categories for immediate redistribution."
            ),
        },
    },
    {
        "email": "boomerangs@demo.com",
        "name": "Boomerangs",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": [
                "Apparel", "Home Goods", "Athletic Apparel",
                "Athletic Footwear", "Household Essentials",
            ],
            "budget_min": 200.0,
            "budget_max": 3000.0,
            "location": "Boston, MA",
            "notes": (
                "Upscale thrift stores benefiting AIDS Action Committee of Massachusetts. "
                "Specializes in clothing and home goods for resale."
            ),
        },
    },
    # ── SMB ────────────────────────────────────────────────────────────────
    {
        "email": "bostonsmb@demo.com",
        "name": "Boston Local SMB",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": [
                "Office Supplies", "Electronics", "Bulk Dry Goods",
                "Household Essentials", "Beverages",
            ],
            "budget_min": 500.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": (
                "Local Boston small business seeking office supplies, electronics, "
                "and operational goods at below-retail prices."
            ),
        },
    },
]

# ── HTTP helpers ──────────────────────────────────────────────────────────────

async def _signup_or_login(
    client: httpx.AsyncClient,
    email: str,
    role: str,
) -> Optional[str]:
    """
    Try to sign up. If the account already exists (409), fall back to login.
    Returns the JWT access_token, or None on failure.
    """
    resp = await client.post(
        f"{AUTH}/auth/signup",
        json={"email": email, "password": PASSWORD, "role": role},
    )
    if resp.status_code == 201:
        return resp.json()["access_token"]
    if resp.status_code == 409:
        # Already registered — log in instead
        login = await client.post(
            f"{AUTH}/auth/login",
            json={"email": email, "password": PASSWORD},
        )
        if login.status_code == 200:
            return login.json()["access_token"]
        _err(f"Login failed for {email}: {login.text}")
        return None
    _err(f"Signup failed for {email}: {resp.status_code} {resp.text}")
    return None


async def _upload_item(
    client: httpx.AsyncClient,
    token: str,
    item: dict,
) -> bool:
    resp = await client.post(
        f"{INV}/inventory/upload",
        json=item,
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.status_code == 201


async def _create_profile(
    client: httpx.AsyncClient,
    token: str,
    profile: dict,
) -> bool:
    resp = await client.post(
        f"{BYR}/buyer/onboarding",
        json=profile,
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 201:
        return True
    if resp.status_code == 409:
        return True  # profile exists — that's fine
    return False


# ── Health check ──────────────────────────────────────────────────────────────

async def check_health(client: httpx.AsyncClient) -> bool:
    services = [
        ("Auth    ", f"{AUTH}/health"),
        ("Inventory", f"{INV}/health"),
        ("Buyer   ", f"{BYR}/health"),
    ]
    all_up = True
    for name, url in services:
        try:
            r = await client.get(url)
            status = "UP" if r.status_code == 200 else f"ERROR {r.status_code}"
        except httpx.ConnectError:
            status = "DOWN — is the service running?"
            all_up = False
        print(f"    {name}  {url}  →  {status}")
    return all_up


# ── Seeding steps ─────────────────────────────────────────────────────────────

async def seed_retailers(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> dict[str, str]:
    """Register all retailers. Returns {email: jwt_token}."""
    print("\n── Registering retailers ─────────────────────────────────────────")
    tokens: dict[str, str] = {}
    created = skipped = failed = 0

    async def _do(r: dict) -> None:
        nonlocal created, skipped, failed
        async with sem:
            # Check if already existed by peeking at the signup response
            signup_resp = await client.post(
                f"{AUTH}/auth/signup",
                json={"email": r["email"], "password": PASSWORD, "role": "retailer"},
            )
            if signup_resp.status_code == 201:
                tokens[r["email"]] = signup_resp.json()["access_token"]
                _ok(f"{r['name']}  ({r['email']})")
                created += 1
            elif signup_resp.status_code == 409:
                login_resp = await client.post(
                    f"{AUTH}/auth/login",
                    json={"email": r["email"], "password": PASSWORD},
                )
                if login_resp.status_code == 200:
                    tokens[r["email"]] = login_resp.json()["access_token"]
                    _skip(f"{r['name']}  ({r['email']})")
                    skipped += 1
                else:
                    _err(f"{r['name']}  — login failed: {login_resp.text}")
                    failed += 1
            else:
                _err(f"{r['name']}  — signup error: {signup_resp.status_code}")
                failed += 1

    await asyncio.gather(*[_do(r) for r in RETAILERS])
    print(f"\n    Retailers: {created} created, {skipped} skipped, {failed} failed")
    return tokens


async def seed_inventory(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    retailer_tokens: dict[str, str],
) -> int:
    """Upload inventory for each retailer. Returns total items created."""
    print("\n── Uploading inventory ───────────────────────────────────────────")
    total = 0

    for email, items in INVENTORY.items():
        token = retailer_tokens.get(email)
        if not token:
            _warn(f"No token for {email} — skipping inventory")
            continue

        ok_count = 0
        for item in items:
            async with sem:
                success = await _upload_item(client, token, item)
            if success:
                ok_count += 1
            else:
                _warn(f"Failed to upload '{item['title']}' for {email}")

        retailer_name = next(
            (r["name"] for r in RETAILERS if r["email"] == email), email
        )
        _ok(f"{retailer_name}: {ok_count}/{len(items)} items uploaded")
        total += ok_count

    print(f"\n    Inventory: {total} items total")
    return total


async def seed_buyers(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> dict[str, str]:
    """Register all buyer accounts. Returns {email: jwt_token}."""
    print("\n── Registering buyers ────────────────────────────────────────────")
    tokens: dict[str, str] = {}
    created = skipped = failed = 0

    async def _do(b: dict) -> None:
        nonlocal created, skipped, failed
        async with sem:
            signup_resp = await client.post(
                f"{AUTH}/auth/signup",
                json={"email": b["email"], "password": PASSWORD, "role": "buyer"},
            )
            if signup_resp.status_code == 201:
                tokens[b["email"]] = signup_resp.json()["access_token"]
                _ok(f"{b['name']}  ({b['email']})  [{b['segment']}]")
                created += 1
            elif signup_resp.status_code == 409:
                login_resp = await client.post(
                    f"{AUTH}/auth/login",
                    json={"email": b["email"], "password": PASSWORD},
                )
                if login_resp.status_code == 200:
                    tokens[b["email"]] = login_resp.json()["access_token"]
                    _skip(f"{b['name']}  ({b['email']})")
                    skipped += 1
                else:
                    _err(f"{b['name']}  — login failed: {login_resp.text}")
                    failed += 1
            else:
                _err(f"{b['name']}  — signup error: {signup_resp.status_code}")
                failed += 1

    await asyncio.gather(*[_do(b) for b in BUYERS])
    print(f"\n    Buyers: {created} created, {skipped} skipped, {failed} failed")
    return tokens


async def seed_profiles(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    buyer_tokens: dict[str, str],
) -> int:
    """Create buyer profiles. Returns count of profiles created."""
    print("\n── Creating buyer profiles ───────────────────────────────────────")
    created = skipped = failed = 0

    async def _do(b: dict) -> None:
        nonlocal created, skipped, failed
        token = buyer_tokens.get(b["email"])
        if not token:
            _warn(f"No token for {b['email']} — skipping profile")
            return
        async with sem:
            resp = await client.post(
                f"{BYR}/buyer/onboarding",
                json=b["profile"],
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 201:
            _ok(f"{b['name']}  [{b['segment']}]")
            created += 1
        elif resp.status_code == 409:
            _skip(f"{b['name']}")
            skipped += 1
        else:
            _err(f"{b['name']}  — profile error: {resp.status_code} {resp.text}")
            failed += 1

    await asyncio.gather(*[_do(b) for b in BUYERS])
    print(f"\n    Profiles: {created} created, {skipped} skipped, {failed} failed")
    return created


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("═" * 62)
    print("  VGP PLATFORM — Boston Demo Data Seeder")
    print("═" * 62)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        # ── Health check ───────────────────────────────────────────────────
        print("\n── Service health ────────────────────────────────────────────")
        healthy = await check_health(client)
        if not healthy:
            print(
                "\nERROR: One or more services are not reachable.\n"
                "Start all three services before running the seeder:\n\n"
                "  uvicorn auth.main:app --port 8000 &\n"
                "  uvicorn inventory.main:app --port 8001 &\n"
                "  uvicorn buyer.main:app --port 8002 &\n",
                file=sys.stderr,
            )
            sys.exit(1)

        sem = asyncio.Semaphore(CONCURRENCY)

        # ── Seed ───────────────────────────────────────────────────────────
        retailer_tokens = await seed_retailers(client, sem)
        item_count      = await seed_inventory(client, sem, retailer_tokens)
        buyer_tokens    = await seed_buyers(client, sem)
        profile_count   = await seed_profiles(client, sem, buyer_tokens)

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "═" * 62)
    print("  SEED COMPLETE")
    print("═" * 62)
    print(f"  Retailers  : {len(retailer_tokens)} accounts")
    print(f"  Inventory  : {item_count} items across {len(INVENTORY)} retailers")
    print(f"  Buyers     : {len(buyer_tokens)} accounts")
    print(f"  Profiles   : {profile_count} buyer profiles")
    print()
    print("  Password for all accounts : Test1234!")
    print(f"  Auth API    : {AUTH}/docs")
    print(f"  Inventory   : {INV}/docs")
    print(f"  Buyer       : {BYR}/docs")
    print("═" * 62)


if __name__ == "__main__":
    asyncio.run(main())
