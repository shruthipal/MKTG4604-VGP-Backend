"""
Match pipeline routes.

POST /match/recommendations  — buyer JWT; returns top-5 ranked, LLM-personalised cards
  Pipeline:
    1. Load buyer profile from DB
    2. Build query text + check in-memory cache (5-min TTL)
    3. Keyword search — SQLite LIKE on title, category, description
    4. Load full inventory details (available items only)
    5. Load same-segment rejection counts per retailer
    6. Composite scoring + sort (similarity, price fit, quantity, rejection penalty)
    7. Nonprofit reorder — free/discounted items always surfaced first
    8. LLM personalisation — parallel Ollama llama3 calls with segment-aware prompts
    9. Persist MatchResult rows + retailer alerts
   10. Cache results + return MatchResponse

GET  /match/alerts            — retailer JWT; dashboard alerts (no buyer data)
PATCH /match/alerts/{id}/read — retailer JWT; mark alert as read
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_utils import get_current_user, require_buyer_role, require_retailer_role
from . import cache as result_cache
from .database import get_db
from .llm import generate_recommendation
from .models import MatchResult, RetailerAlert
from .ranker import RankedItem, rank_and_filter
from .schemas import (
    BuyerInterestCard, BuyerSearchResponse,
    MatchResponse, RecommendationCard, RetailerAlertResponse,
)
from .vector import query_inventory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["match"])

_TOP_N = 40
_CHROMADB_FETCH_N = 100  # fetch more than needed so ranker has room to filter


# ── POST /match/recommendations ───────────────────────────────────────────────

@router.post(
    "/recommendations",
    response_model=MatchResponse,
    summary=(
        "Run the full match pipeline for the authenticated buyer. "
        "Returns top-5 ranked, LLM-personalised recommendation cards. "
        "[R-06: retailer JWTs blocked]"
    ),
)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),  # R-06 enforced here
):
    t0 = time.monotonic()
    user_id: str = current_user["sub"]

    # Step 1: Load buyer profile
    buyer = await _load_buyer_profile(user_id, db)
    segment: str = buyer["segment"]

    # Step 2: Build query text + check cache
    query_text = _build_query_text(buyer)
    cached_cards = result_cache.get(user_id, query_text)

    if cached_cards is not None:
        logger.info("[R-03] Cache hit for user %s — returning %d cards.", user_id, len(cached_cards))
        return MatchResponse(
            recommendations=cached_cards,
            buyer_segment=segment,
            total_found=len(cached_cards),
            generated_at=datetime.now(timezone.utc),
            served_from_cache=True,
        )

    # Step 3: Semantic vector search (ChromaDB)
    import re as _re
    notes_match = _re.search(r'Notes:\s*(.+)', query_text, _re.IGNORECASE)
    prefs_match = _re.search(r'Category preferences:\s*(.+)', query_text, _re.IGNORECASE)
    notes_text = notes_match.group(1).strip() if notes_match else ""
    prefs_text = prefs_match.group(1).strip() if prefs_match else ""
    semantic_query = f"{notes_text} {prefs_text}".strip() or query_text
    logger.info("[match] semantic vector search: %r", semantic_query[:120])

    vector_result = await query_inventory(semantic_query, n_results=_CHROMADB_FETCH_N)
    ids: list[str] = vector_result["ids"][0] if vector_result.get("ids") and vector_result["ids"] else []
    distances: list[float] = vector_result["distances"][0] if vector_result.get("distances") and vector_result["distances"] else []

    # Step 3b: SQLite keyword fallback if ChromaDB is empty or not yet indexed
    if not ids:
        logger.warning("[match] ChromaDB returned no results — falling back to keyword search")
        keyword = semantic_query.lower()
        raw_words = [w.strip("'\".,!?()-") for w in keyword.split() if len(w.strip("'\".,!?()-")) > 2]
        if not raw_words:
            raw_words = [keyword]
        where_conditions = " OR ".join(
            f"(LOWER(title) LIKE :w{i} OR LOWER(category) LIKE :w{i} OR LOWER(description) LIKE :w{i})"
            for i in range(len(raw_words))
        )
        title_conditions    = " OR ".join(f"LOWER(title)    LIKE :w{i}" for i in range(len(raw_words)))
        category_conditions = " OR ".join(f"LOWER(category) LIKE :w{i}" for i in range(len(raw_words)))
        params = {f"w{i}": f"%{w}%" for i, w in enumerate(raw_words)}
        fb_result = await db.execute(
            text(
                f"SELECT DISTINCT *, "
                f"  CASE "
                f"    WHEN ({title_conditions})    THEN 0.85 "
                f"    WHEN ({category_conditions}) THEN 0.70 "
                f"    ELSE 0.50 "
                f"  END AS relevance_score "
                f"FROM inventory_items "
                f"WHERE status = 'available' "
                f"AND ({where_conditions}) "
                f"LIMIT 100"
            ),
            params,
        )
        fb_rows = fb_result.fetchall()
        ids = [row.id for row in fb_rows]
        distances = [1.0 - float(row.relevance_score) for row in fb_rows]

    if not ids:
        return MatchResponse(
            recommendations=[],
            buyer_segment=segment,
            total_found=0,
            generated_at=datetime.now(timezone.utc),
            served_from_cache=False,
        )

    # ── (synonym dict kept only for buyers/search endpoint below) ─────────────
    _SYNONYMS: dict[str, list[str]] = {
        # ── Clothing (general) ────────────────────────────────────────────────
        "clothes":      ["clothing", "apparel"],
        "clothing":     ["clothing", "apparel"],
        "apparel":      ["apparel", "clothing"],
        "outfit":       ["clothing", "apparel", "outfit"],
        "outfits":      ["clothing", "apparel"],
        "uniform":      ["uniform", "workwear", "apparel"],
        "uniforms":     ["uniform", "workwear", "apparel"],
        "casual":       ["casual", "clothing", "apparel"],
        "streetwear":   ["streetwear", "athletic", "casual", "clothing"],
        "fashion":      ["fashion", "clothing", "apparel"],
        # ── Tops ──────────────────────────────────────────────────────────────
        "shirt":        ["shirt"],
        "shirts":       ["shirt"],
        "tee":          ["tee", "shirt", "graphic"],
        "tshirt":       ["shirt", "tee"],
        "tshirts":      ["shirt", "tee"],
        "polo":         ["polo", "shirt"],
        "polos":        ["polo", "shirt"],
        "flannel":      ["flannel", "shirt"],
        "blouse":       ["blouse", "shirt", "top"],
        "blouses":      ["blouse", "shirt", "top"],
        "top":          ["top", "shirt", "blouse"],
        "tops":         ["top", "shirt", "blouse"],
        "tank":         ["tank", "shirt", "athletic"],
        # ── Bottoms ───────────────────────────────────────────────────────────
        "pants":        ["pants", "jeans", "chino", "trouser"],
        "jeans":        ["jeans", "denim"],
        "denim":        ["denim", "jeans"],
        "chinos":       ["chino", "pants", "trouser"],
        "chino":        ["chino", "pants", "trouser"],
        "trousers":     ["trouser", "pants", "chino"],
        "shorts":       ["shorts", "athletic", "casual"],
        "leggings":     ["legging", "athletic", "workout"],
        "legging":      ["legging", "athletic", "workout"],
        "joggers":      ["jogger", "sweat", "athletic", "pants"],
        # ── Outerwear ─────────────────────────────────────────────────────────
        "jacket":       ["jacket", "outerwear"],
        "jackets":      ["jacket", "outerwear"],
        "coat":         ["coat", "jacket", "outerwear"],
        "coats":        ["coat", "jacket", "outerwear"],
        "puffer":       ["puffer", "down", "jacket", "outerwear"],
        "parka":        ["parka", "jacket", "outerwear", "winter"],
        "fleece":       ["fleece", "jacket", "hoodie", "pullover"],
        "vest":         ["vest", "outerwear", "jacket"],
        "vests":        ["vest", "outerwear"],
        "windbreaker":  ["windbreaker", "jacket", "rain", "outerwear"],
        "raincoat":     ["rain", "jacket", "outerwear"],
        "winter coat":  ["winter", "jacket", "outerwear", "parka"],
        # ── Sweaters & Hoodies ────────────────────────────────────────────────
        "hoodie":       ["hoodie", "fleece", "sweat"],
        "hoodies":      ["hoodie", "fleece", "sweat"],
        "sweatshirt":   ["sweat", "hoodie", "fleece", "crew"],
        "sweatshirts":  ["sweat", "hoodie", "fleece"],
        "sweater":      ["sweater", "knitwear", "pullover"],
        "sweaters":     ["sweater", "knitwear", "pullover"],
        "pullover":     ["pullover", "sweater", "fleece", "hoodie"],
        "sweats":       ["sweat", "fleece", "hoodie", "jogger"],
        "crewneck":     ["crew", "sweat", "hoodie", "sweater"],
        # ── Athletic / Activewear ─────────────────────────────────────────────
        "athletic":     ["athletic", "workout", "training", "sport"],
        "workout":      ["workout", "athletic", "training", "fitness"],
        "activewear":   ["athletic", "activewear", "workout", "training"],
        "gym":          ["gym", "workout", "athletic", "training", "fitness"],
        "running":      ["running", "athletic", "training", "footwear"],
        "yoga":         ["yoga", "athletic", "legging", "activewear"],
        "sports":       ["sport", "athletic", "training", "fitness"],
        "sport":        ["sport", "athletic", "training"],
        "compression":  ["compression", "athletic", "training"],
        "training":     ["training", "athletic", "workout", "sport"],
        "fitness":      ["fitness", "athletic", "workout", "training"],
        # ── Footwear ──────────────────────────────────────────────────────────
        "shoes":        ["shoes", "footwear", "boot", "sneaker"],
        "shoe":         ["shoes", "footwear", "boot", "sneaker"],
        "boots":        ["boot", "footwear"],
        "boot":         ["boot", "footwear"],
        "sneakers":     ["sneaker", "footwear", "athletic"],
        "sneaker":      ["sneaker", "footwear", "athletic"],
        "footwear":     ["footwear", "shoes", "boot", "sneaker"],
        "heels":        ["heel", "footwear", "women"],
        "sandals":      ["sandal", "footwear"],
        "workboots":    ["work", "boot", "footwear", "carhartt"],
        "hiking boots": ["hiking", "boot", "footwear", "outdoor"],
        # ── Underwear & Basics ────────────────────────────────────────────────
        "underwear":    ["underwear", "basics", "essential"],
        "socks":        ["socks", "underwear", "basics"],
        "thermal":      ["thermal", "underwear", "basics", "heattech"],
        "undershirt":   ["undershirt", "shirt", "thermal", "basics"],
        # ── Professional / Formal ─────────────────────────────────────────────
        "dress":        ["dress", "formal", "business", "professional"],
        "suit":         ["suit", "blazer", "formal", "dress"],
        "blazer":       ["blazer", "suit", "formal", "jacket"],
        "blazers":      ["blazer", "suit", "formal"],
        "formal":       ["formal", "dress", "blazer", "suit"],
        "business":     ["business", "dress", "formal", "professional"],
        "professional": ["professional", "dress", "formal", "business"],
        "workwear":     ["workwear", "work", "carhartt", "professional"],
        # ── Outdoor / Adventure ───────────────────────────────────────────────
        "outdoor":      ["outdoor", "hiking", "camping"],
        "hiking":       ["hiking", "outdoor", "trail", "boot"],
        "camping":      ["camping", "outdoor", "gear"],
        "gear":         ["gear", "outdoor", "athletic", "equipment"],
        # ── Gender ────────────────────────────────────────────────────────────
        "men":          ["men", "men's", "male"],
        "mens":         ["men", "men's", "male"],
        "women":        ["women", "women's", "female"],
        "womens":       ["women", "women's", "female"],
        "unisex":       ["unisex", "men", "women"],
        # ── Accessories ───────────────────────────────────────────────────────
        "accessories":  ["accessories", "accessory", "jewelry", "handbag"],
        "jewelry":      ["jewelry", "necklace", "earring", "accessories"],
        "handbag":      ["handbag", "bag", "accessories"],
        "sunglasses":   ["sunglasses", "accessories"],
        # ── Makeup & Cosmetics ────────────────────────────────────────────────
        "makeup":       ["makeup", "cosmetic", "beauty"],
        "cosmetics":    ["cosmetic", "makeup", "beauty"],
        "beauty":       ["beauty", "makeup", "cosmetic", "skincare"],
        "foundation":   ["foundation", "makeup", "cosmetic"],
        "concealer":    ["concealer", "foundation", "makeup"],
        "lipstick":     ["lipstick", "lip", "makeup"],
        "lip":          ["lip", "lipstick", "gloss", "makeup"],
        "gloss":        ["gloss", "lip", "makeup"],
        "mascara":      ["mascara", "eye", "makeup"],
        "eyeliner":     ["eyeliner", "eye", "liner", "makeup"],
        "eyeshadow":    ["eyeshadow", "eye", "palette", "makeup"],
        "palette":      ["palette", "eyeshadow", "makeup"],
        "palettes":     ["palette", "eyeshadow", "makeup"],
        "blush":        ["blush", "cheek", "makeup"],
        "bronzer":      ["bronzer", "blush", "cheek", "makeup"],
        "highlighter":  ["highlighter", "glow", "makeup"],
        "primer":       ["primer", "makeup", "skincare"],
        "setting spray":["setting", "spray", "makeup"],
        "brow":         ["brow", "eyebrow", "makeup"],
        "nail":         ["nail", "polish", "beauty"],
        "nails":        ["nail", "polish", "beauty"],
        # ── Skincare ─────────────────────────────────────────────────────────
        "skincare":     ["skincare", "skin", "moisturizer", "serum"],
        "moisturizer":  ["moisturizer", "lotion", "skincare"],
        "lotion":       ["lotion", "moisturizer", "skincare"],
        "serum":        ["serum", "vitamin", "skincare"],
        "cleanser":     ["cleanser", "face", "wash", "skincare"],
        "face wash":    ["face", "cleanser", "wash", "skincare"],
        "sunscreen":    ["sunscreen", "spf", "skincare"],
        "toner":        ["toner", "skincare"],
        "facial":       ["facial", "face", "skincare"],
        # ── Men's Grooming ────────────────────────────────────────────────────
        "grooming":     ["grooming", "shaving", "razor", "deodorant"],
        "razor":        ["razor", "shaving", "grooming"],
        "razors":       ["razor", "shaving", "grooming"],
        "shaving":      ["shaving", "razor", "grooming"],
        "shave":        ["shave", "razor", "shaving", "grooming"],
        "deodorant":    ["deodorant", "antiperspirant", "grooming"],
        "body wash":    ["body", "wash", "shower", "grooming"],
        "shower gel":   ["shower", "gel", "body", "wash", "grooming"],
        "shampoo":      ["shampoo", "hair", "grooming"],
        "conditioner":  ["conditioner", "hair", "grooming"],
        "hair":         ["hair", "shampoo", "conditioner", "styling"],
        "pomade":       ["pomade", "styling", "hair", "grooming"],
        "gel":          ["gel", "styling", "hair", "grooming"],
        "hygiene":      ["hygiene", "grooming", "personal", "deodorant"],
        "personal care":["personal", "grooming", "hygiene"],
        # ── Food (general) ────────────────────────────────────────────────────
        "food":         ["food", "beverage", "produce", "baked", "prepared"],
        "meal":         ["meal", "prepared", "food"],
        "meals":        ["meal", "prepared", "food"],
        "lunch":        ["lunch", "prepared", "sandwich", "food"],
        "dinner":       ["dinner", "prepared", "food"],
        "breakfast":    ["breakfast", "baked", "pastry", "coffee", "bagel"],
        "snack":        ["snack", "packaged", "food"],
        "snacks":       ["snack", "packaged", "food"],
        "catering":     ["catering", "prepared", "food"],
        "restaurant":   ["restaurant", "prepared", "food"],
        # ── Baked Goods ───────────────────────────────────────────────────────
        "pastry":       ["pastry", "baked", "bakery"],
        "pastries":     ["pastry", "baked", "bakery"],
        "bakery":       ["bakery", "baked", "bread", "pastry"],
        "baked":        ["baked", "bakery", "bread", "pastry"],
        "bread":        ["bread", "baked", "loaf", "bakery"],
        "loaf":         ["loaf", "bread", "baked"],
        "donut":        ["donut", "pastry", "baked"],
        "donuts":       ["donut", "pastry", "baked"],
        "doughnut":     ["donut", "pastry", "baked"],
        "muffin":       ["muffin", "pastry", "baked"],
        "muffins":      ["muffin", "pastry", "baked"],
        "croissant":    ["croissant", "pastry", "baked"],
        "croissants":   ["croissant", "pastry", "baked"],
        "bagel":        ["bagel", "baked", "bakery"],
        "bagels":       ["bagel", "baked", "bakery"],
        "cookie":       ["cookie", "baked", "pastry"],
        "cookies":      ["cookie", "baked", "pastry"],
        "cake":         ["cake", "baked", "dessert"],
        "dessert":      ["dessert", "baked", "cake", "pastry"],
        "desserts":     ["dessert", "baked", "cake"],
        # ── Produce & Fresh ───────────────────────────────────────────────────
        "produce":      ["produce", "vegetable", "fruit", "organic"],
        "vegetables":   ["vegetable", "produce", "organic"],
        "vegetable":    ["vegetable", "produce", "organic"],
        "veggies":      ["vegetable", "produce", "organic"],
        "veggie":       ["vegetable", "produce", "organic"],
        "fruits":       ["fruit", "produce", "organic"],
        "fruit":        ["fruit", "produce", "organic"],
        "organic":      ["organic", "produce", "natural"],
        "fresh":        ["fresh", "produce", "food"],
        "greens":       ["greens", "produce", "vegetable", "salad"],
        "salad":        ["salad", "prepared", "produce", "greens"],
        "salads":       ["salad", "prepared", "produce"],
        # ── Canned / Packaged ─────────────────────────────────────────────────
        "canned":       ["canned", "beans", "soup", "pantry"],
        "beans":        ["beans", "canned", "legume", "protein"],
        "soup":         ["soup", "canned", "prepared"],
        "soups":        ["soup", "canned", "prepared"],
        "pantry":       ["pantry", "canned", "packaged", "bulk"],
        "groceries":    ["groceries", "packaged", "canned", "food"],
        "grocery":      ["grocery", "packaged", "canned", "food"],
        "packaged":     ["packaged", "groceries", "canned"],
        "grains":       ["grain", "bulk", "rice", "quinoa"],
        "grain":        ["grain", "bulk", "rice", "oat"],
        "rice":         ["rice", "grain", "bulk"],
        "oats":         ["oat", "grain", "bulk", "breakfast"],
        "lentils":      ["lentil", "grain", "bulk", "beans"],
        "quinoa":       ["quinoa", "grain", "bulk"],
        # ── Prepared Foods ────────────────────────────────────────────────────
        "prepared":     ["prepared", "food", "meal"],
        "sandwich":     ["sandwich", "prepared", "wrap"],
        "sandwiches":   ["sandwich", "prepared", "wrap"],
        "wrap":         ["wrap", "sandwich", "prepared"],
        "wraps":        ["wrap", "sandwich", "prepared"],
        "bowl":         ["bowl", "prepared", "grain"],
        "bowls":        ["bowl", "prepared", "grain"],
        "burrito":      ["burrito", "prepared", "mexican"],
        "burritos":     ["burrito", "prepared"],
        "pizza":        ["pizza", "prepared", "food"],
        "chicken":      ["chicken", "prepared", "protein"],
        "protein":      ["protein", "chicken", "prepared"],
        "deli":         ["deli", "prepared", "sandwich"],
        "sushi":        ["sushi", "prepared", "food"],
        "pasta":        ["pasta", "prepared", "italian"],
        "sauce":        ["sauce", "pasta", "prepared"],
        "sauces":       ["sauce", "pasta", "prepared"],
        # ── Dairy ─────────────────────────────────────────────────────────────
        "dairy":        ["dairy", "cheese", "milk"],
        "cheese":       ["cheese", "dairy"],
        "milk":         ["milk", "dairy"],
        # ── Beverages ─────────────────────────────────────────────────────────
        "coffee":       ["coffee", "beverage"],
        "beverage":     ["beverage", "coffee", "drink"],
        "beverages":    ["beverage", "coffee", "drink"],
        "drink":        ["drink", "beverage", "coffee"],
        "drinks":       ["drink", "beverage", "coffee"],
        "tea":          ["tea", "beverage", "drink"],
        "juice":        ["juice", "beverage", "drink"],
        "cold brew":    ["cold", "brew", "coffee", "beverage"],
        "latte":        ["latte", "coffee", "beverage"],
        # ── Home Goods ────────────────────────────────────────────────────────
        "home":         ["home", "household", "goods", "kitchen"],
        "household":    ["household", "home", "goods"],
        "kitchen":      ["kitchen", "cookware", "bakeware", "tableware"],
        "cookware":     ["cookware", "pots", "pans", "kitchen"],
        "bedding":      ["bedding", "sheets", "towel", "linen"],
        "towels":       ["towel", "bath", "bedding"],
        "towel":        ["towel", "bath", "bedding"],
        "linens":       ["linen", "bedding", "towel"],
        "decor":        ["decor", "accessories", "home"],
        "furniture":    ["furniture", "home", "goods"],
        "dishes":       ["dishes", "tableware", "kitchen"],
        "tableware":    ["tableware", "dishes", "kitchen"],
        # ── Electronics / Office ──────────────────────────────────────────────
        "headphones":   ["headphone", "audio", "electronics"],
        "tech":         ["tech", "electronics", "gadget"],
        "electronics":  ["electronics", "tech", "gadget"],
        "office":       ["office", "supplies", "staples"],
        "supplies":     ["supplies", "office", "stationery"],
    }

    # Step 4: Load inventory details
    inventory = await _load_inventory_items(ids, db)

    # Step 5: Load rejection counts
    rejection_counts = await _load_rejection_counts(segment, db)

    # Steps 6 + 7: Rank, filter, nonprofit reorder
    ranked: list[RankedItem] = rank_and_filter(ids, distances, inventory, buyer, rejection_counts)
    top: list[RankedItem] = ranked[:_TOP_N]

    if not top:
        return MatchResponse(
            recommendations=[],
            buyer_segment=segment,
            total_found=0,
            generated_at=datetime.now(timezone.utc),
            served_from_cache=False,
        )

    # Step 8: Generate recommendations
    rec_texts: list[str] = await asyncio.gather(*[
        generate_recommendation(r.item_data, segment, r.composite_score)
        for r in top
    ])

    # Step 8b: Fetch retailer emails in one query so contact info is available
    retailer_ids = list({r.item_data.get("retailer_id", "") for r in top} - {""})
    retailer_email_map: dict[str, str] = {}
    if retailer_ids:
        placeholders = ", ".join(f":rid_{i}" for i in range(len(retailer_ids)))
        params = {f"rid_{i}": rid for i, rid in enumerate(retailer_ids)}
        email_rows = await db.execute(
            text(f"SELECT id, email FROM users WHERE id IN ({placeholders})"),
            params,
        )
        retailer_email_map = {row.id: row.email for row in email_rows.fetchall()}

    # Step 9a: Build cards
    cards: list[RecommendationCard] = [
        RecommendationCard(
            item_id=r.item_id,
            title=r.item_data.get("title", ""),
            category=r.item_data.get("category", ""),
            price=float(r.item_data.get("price", 0)),
            condition=r.item_data.get("condition", ""),
            quantity=int(r.item_data.get("quantity", 0)),
            retailer_id=r.item_data.get("retailer_id", ""),
            similarity_score=round(r.similarity_score, 4),
            composite_score=round(r.composite_score, 4),
            recommendation_text=rec_text,
            retailer_email=retailer_email_map.get(r.item_data.get("retailer_id", ""), ""),
            retailer_name="",
        )
        for r, rec_text in zip(top, rec_texts)
    ]

    # Step 9b: Persist results
    await _store_match_results(user_id, cards, db)
    await _create_retailer_alerts(cards, db)

    # Step 10: Cache + return
    result_cache.set_result(user_id, query_text, cards)

    elapsed = time.monotonic() - t0
    if elapsed > 2.0:
        logger.warning("[R-03] Match pipeline took %.2f s (exceeds 2 s target).", elapsed)
    else:
        logger.info("[R-03] Match pipeline completed in %.2f s.", elapsed)

    return MatchResponse(
        recommendations=cards,
        buyer_segment=segment,
        total_found=len(ranked),
        generated_at=datetime.now(timezone.utc),
        served_from_cache=False,
    )


# ── POST /match/buyers/search ─────────────────────────────────────────────────

@router.post(
    "/buyers/search",
    response_model=BuyerSearchResponse,
    summary="Find buyer orgs & nonprofits interested in a given surplus item type (business side)",
)
async def search_interested_buyers(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_buyer_role),
):
    """
    Searches buyer_profiles by notes + preferences using the same synonym expansion
    as the recommendation pipeline. Returns matching buyer orgs for the business side
    so retailers can see who actually wants their surplus.
    """
    import re as _re
    import json as _json

    query = str(body.get("query", "")).strip().lower()
    if not query:
        return BuyerSearchResponse(buyers=[], total_found=0, query=query)

    # Reuse the synonym expansion dict inline
    _SYNONYMS: dict[str, list[str]] = {
        "clothes": ["clothing", "apparel"], "clothing": ["clothing", "apparel"],
        "apparel": ["apparel", "clothing"], "outfit": ["clothing", "apparel"],
        "shirt": ["shirt"], "shirts": ["shirt"], "tee": ["tee", "shirt"],
        "polo": ["polo", "shirt"], "tops": ["top", "shirt", "blouse"],
        "pants": ["pants", "jeans", "chino", "trouser"], "jeans": ["jeans", "denim"],
        "denim": ["denim", "jeans"], "chinos": ["chino", "pants"],
        "shorts": ["shorts", "athletic", "casual"],
        "leggings": ["legging", "athletic", "workout"],
        "joggers": ["jogger", "sweat", "athletic"],
        "jacket": ["jacket", "outerwear"], "jackets": ["jacket", "outerwear"],
        "coat": ["coat", "jacket", "outerwear"], "puffer": ["puffer", "down", "jacket"],
        "fleece": ["fleece", "jacket", "hoodie"], "vest": ["vest", "outerwear"],
        "windbreaker": ["windbreaker", "jacket", "outerwear"],
        "hoodie": ["hoodie", "fleece", "sweat"], "hoodies": ["hoodie", "fleece", "sweat"],
        "sweatshirt": ["sweat", "hoodie", "fleece"],
        "sweater": ["sweater", "knitwear", "pullover"],
        "pullover": ["pullover", "sweater", "fleece"],
        "sweats": ["sweat", "fleece", "hoodie", "jogger"],
        "athletic": ["athletic", "workout", "training", "sport"],
        "workout": ["workout", "athletic", "training", "fitness"],
        "activewear": ["athletic", "activewear", "workout"],
        "gym": ["gym", "workout", "athletic", "training", "fitness"],
        "running": ["running", "athletic", "training", "footwear"],
        "yoga": ["yoga", "athletic", "legging"],
        "sports": ["sport", "athletic", "training", "fitness"],
        "training": ["training", "athletic", "workout", "sport"],
        "fitness": ["fitness", "athletic", "workout"],
        "shoes": ["shoes", "footwear", "boot", "sneaker"],
        "boots": ["boot", "footwear"], "sneakers": ["sneaker", "footwear", "athletic"],
        "footwear": ["footwear", "shoes", "boot", "sneaker"],
        "workboots": ["work", "boot", "footwear"],
        "underwear": ["underwear", "basics", "essential"],
        "socks": ["socks", "underwear", "basics"],
        "thermal": ["thermal", "underwear", "basics"],
        "dress": ["dress", "formal", "business", "professional"],
        "suit": ["suit", "blazer", "formal", "dress"],
        "blazer": ["blazer", "suit", "formal", "jacket"],
        "formal": ["formal", "dress", "blazer", "suit"],
        "business": ["business", "dress", "formal", "professional"],
        "professional": ["professional", "dress", "formal", "business"],
        "workwear": ["workwear", "work", "professional"],
        "outdoor": ["outdoor", "hiking", "camping"],
        "hiking": ["hiking", "outdoor", "trail", "boot"],
        "gear": ["gear", "outdoor", "athletic", "equipment"],
        "men": ["men", "men's", "male", "grooming"],
        "mens": ["men", "men's", "male"],
        "women": ["women", "women's", "female"],
        "womens": ["women", "women's", "female"],
        "accessories": ["accessories", "accessory", "jewelry"],
        "makeup": ["makeup", "cosmetic", "beauty"],
        "cosmetics": ["cosmetic", "makeup", "beauty"],
        "beauty": ["beauty", "makeup", "cosmetic", "skincare"],
        "skincare": ["skincare", "skin", "moisturizer", "serum"],
        "grooming": ["grooming", "shaving", "razor", "deodorant"],
        "razor": ["razor", "shaving", "grooming"],
        "deodorant": ["deodorant", "antiperspirant", "grooming"],
        "shampoo": ["shampoo", "hair", "grooming"],
        "hair": ["hair", "shampoo", "conditioner", "styling"],
        "hygiene": ["hygiene", "grooming", "personal", "deodorant"],
        "food": ["food", "beverage", "produce", "baked", "prepared"],
        "meal": ["meal", "prepared", "food"], "meals": ["meal", "prepared", "food"],
        "breakfast": ["breakfast", "baked", "pastry", "coffee", "bagel"],
        "snack": ["snack", "packaged", "food"], "snacks": ["snack", "packaged", "food"],
        "pastry": ["pastry", "baked", "bakery"], "pastries": ["pastry", "baked", "bakery"],
        "bakery": ["bakery", "baked", "bread", "pastry"],
        "bread": ["bread", "baked", "loaf", "bakery"],
        "donut": ["donut", "pastry", "baked"], "donuts": ["donut", "pastry", "baked"],
        "bagel": ["bagel", "baked", "bakery"], "bagels": ["bagel", "baked", "bakery"],
        "cookie": ["cookie", "baked", "pastry"], "cookies": ["cookie", "baked", "pastry"],
        "dessert": ["dessert", "baked", "cake", "pastry"],
        "produce": ["produce", "vegetable", "fruit", "organic"],
        "vegetables": ["vegetable", "produce", "organic"],
        "veggies": ["vegetable", "produce", "organic"],
        "fruits": ["fruit", "produce", "organic"],
        "organic": ["organic", "produce", "natural"],
        "fresh": ["fresh", "produce", "food"],
        "greens": ["greens", "produce", "vegetable", "salad"],
        "salad": ["salad", "prepared", "produce"],
        "canned": ["canned", "beans", "soup", "pantry"],
        "beans": ["beans", "canned", "legume"],
        "soup": ["soup", "canned", "prepared"],
        "pantry": ["pantry", "canned", "packaged", "bulk"],
        "groceries": ["groceries", "packaged", "canned", "food"],
        "grocery": ["grocery", "packaged", "canned", "food"],
        "grains": ["grain", "bulk", "rice", "quinoa"],
        "sandwich": ["sandwich", "prepared", "wrap"],
        "wrap": ["wrap", "sandwich", "prepared"],
        "bowl": ["bowl", "prepared", "grain"],
        "burrito": ["burrito", "prepared"],
        "pasta": ["pasta", "prepared"],
        "dairy": ["dairy", "cheese", "milk"],
        "cheese": ["cheese", "dairy"],
        "coffee": ["coffee", "beverage"],
        "beverage": ["beverage", "coffee", "drink"],
        "beverages": ["beverage", "coffee", "drink"],
        "drink": ["drink", "beverage", "coffee"],
        "tea": ["tea", "beverage", "drink"],
        "home": ["home", "household", "goods", "kitchen"],
        "kitchen": ["kitchen", "cookware", "tableware"],
        "bedding": ["bedding", "sheets", "towel", "linen"],
        "towels": ["towel", "bath", "bedding"],
        "office": ["office", "supplies"],
        "electronics": ["electronics", "tech"],
    }

    raw_words = [w.strip("'\".,!?()-") for w in query.split() if len(w.strip("'\".,!?()-")) > 2]
    if not raw_words:
        raw_words = [query]
    expanded: list[str] = []
    seen_exp: set[str] = set()
    for w in raw_words:
        for term in _SYNONYMS.get(w, [w]):
            if term not in seen_exp:
                seen_exp.add(term)
                expanded.append(term)

    # Search buyer_profiles — match on notes OR preferences (stored as JSON text)
    conditions = " OR ".join(
        f"(LOWER(bp.notes) LIKE :w{i} OR LOWER(bp.preferences) LIKE :w{i})"
        for i in range(len(expanded))
    )
    params = {f"w{i}": f"%{t}%" for i, t in enumerate(expanded)}

    result = await db.execute(
        text(f"""
            SELECT bp.org_name, bp.segment, bp.location, bp.notes, bp.preferences,
                   bp.user_id, u.email AS contact_email
            FROM   buyer_profiles bp
            LEFT JOIN users u ON u.id = bp.user_id
            WHERE  bp.org_name != ''
              AND  ({conditions})
            ORDER  BY bp.segment ASC
            LIMIT  40
        """),
        params,
    )
    rows = result.fetchall()

    cards: list[BuyerInterestCard] = []
    seen_orgs: set[str] = set()
    for row in rows:
        if row.org_name in seen_orgs:
            continue
        seen_orgs.add(row.org_name)

        # Parse preferences (stored as JSON list or comma string)
        prefs: list[str] = []
        if row.preferences:
            try:
                prefs = _json.loads(row.preferences) if isinstance(row.preferences, str) else list(row.preferences)
            except Exception:
                prefs = [p.strip() for p in str(row.preferences).split(",")]

        # Truncate notes to a readable wants summary
        notes_text = (row.notes or "").strip()
        wants = notes_text[:160].rsplit(" ", 1)[0] + "…" if len(notes_text) > 160 else notes_text

        # Score based on how many expanded terms hit preferences
        prefs_lower = " ".join(prefs).lower()
        hits = sum(1 for t in expanded if t in prefs_lower)
        strength = "Strong" if hits >= 2 else "Good" if hits >= 1 else "Moderate"

        cards.append(BuyerInterestCard(
            org_name=row.org_name,
            segment=row.segment,
            location=row.location,
            wants=wants,
            preferences=prefs[:6],  # cap display to 6
            match_strength=strength,
            contact_email=row.contact_email or "",
            user_id=str(row.user_id) if row.user_id else "",
        ))

    # Sort: Strong first, then Good, then Moderate
    order = {"Strong": 0, "Good": 1, "Moderate": 2}
    cards.sort(key=lambda c: order[c.match_strength])

    return BuyerSearchResponse(buyers=cards, total_found=len(cards), query=query)


# ── GET /match/alerts ─────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=list[RetailerAlertResponse],
    summary=(
        "Return match alerts for the authenticated retailer's dashboard. "
        "[R-02: no buyer segment, preferences, or history returned]"
    ),
)
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    """
    R-02: RetailerAlertResponse contains item info + match_score_label only.
    buyer_user_id (stored in match_results) is never included here.
    """
    retailer_id: str = current_user["sub"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    result = await db.execute(
        text("""
            SELECT id, retailer_id, item_id, item_title,
                   match_score_label, match_count, is_read, created_at
            FROM   retailer_alerts
            WHERE  retailer_id = :rid
              AND  created_at  >= :cutoff
            ORDER  BY created_at DESC
        """),
        {"rid": retailer_id, "cutoff": cutoff},
    )
    rows = result.fetchall()
    return [
        RetailerAlertResponse(
            id=row.id,
            item_id=row.item_id,
            item_title=row.item_title,
            match_score_label=row.match_score_label,
            match_count=row.match_count,
            is_read=bool(row.is_read),
            created_at=row.created_at,
        )
        for row in rows
    ]


# ── PATCH /match/alerts/{alert_id}/read ──────────────────────────────────────

@router.patch(
    "/alerts/{alert_id}/read",
    response_model=RetailerAlertResponse,
    summary="Mark a retailer dashboard alert as read",
)
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_retailer_role),
):
    result = await db.execute(
        text("""
            SELECT id, retailer_id, item_id, item_title,
                   match_score_label, match_count, is_read, created_at
            FROM   retailer_alerts
            WHERE  id = :aid AND retailer_id = :rid
        """),
        {"aid": alert_id, "rid": current_user["sub"]},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    await db.execute(
        text("UPDATE retailer_alerts SET is_read = 1 WHERE id = :aid"),
        {"aid": alert_id},
    )
    await db.commit()

    return RetailerAlertResponse(
        id=row.id,
        item_id=row.item_id,
        item_title=row.item_title,
        match_score_label=row.match_score_label,
        match_count=row.match_count,
        is_read=True,
        created_at=row.created_at,
    )


# ── POST /match/interest ──────────────────────────────────────────────────────

@router.post("/interest", summary="Express interest in a match")
async def express_interest(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import uuid as _uuid
    interest_id = str(_uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("""INSERT INTO interests
            (id, from_user_id, from_email, from_org_name, from_role,
             target_type, target_id, target_title, target_owner_id, message, is_read, created_at)
            VALUES (:id, :from_user_id, :from_email, :from_org_name, :from_role,
             :target_type, :target_id, :target_title, :target_owner_id, :message, 0, :created_at)"""),
        {
            "id": interest_id,
            "from_user_id": current_user["sub"],
            "from_email": current_user["email"],
            "from_org_name": body.get("from_org_name", ""),
            "from_role": current_user["role"],
            "target_type": body.get("target_type", "item"),
            "target_id": body.get("target_id", ""),
            "target_title": body.get("target_title", ""),
            "target_owner_id": body.get("target_owner_id", ""),
            "message": body.get("message", ""),
            "created_at": now,
        }
    )
    await db.commit()
    return {"id": interest_id, "status": "sent"}


# ── GET /match/inbox ───────────────────────────────────────────────────────────

@router.get("/inbox", summary="Get interest inbox")
async def get_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["sub"]
    result = await db.execute(
        text("""SELECT * FROM interests
            WHERE target_owner_id = :uid OR from_user_id = :uid
            ORDER BY created_at DESC LIMIT 50"""),
        {"uid": user_id}
    )
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


# ── PATCH /match/inbox/{interest_id}/read ─────────────────────────────────────

@router.patch("/inbox/{interest_id}/read", summary="Mark interest as read")
async def mark_interest_read(
    interest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await db.execute(
        text("UPDATE interests SET is_read = 1 WHERE id = :iid AND target_owner_id = :uid"),
        {"iid": interest_id, "uid": current_user["sub"]}
    )
    await db.commit()
    return {"status": "ok"}


# ── Private helpers ────────────────────────────────────────────────────────────

async def _load_buyer_profile(user_id: str, db: AsyncSession) -> dict:
    """Returns the buyer profile dict, or raises 404 if no profile exists."""
    result = await db.execute(
        text("SELECT * FROM buyer_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer profile not found. Complete onboarding at POST /buyer/onboarding first.",
        )
    profile = dict(row._mapping)
    # Deserialize preferences JSON if stored as string (SQLite TEXT fallback)
    prefs = profile.get("preferences")
    if isinstance(prefs, str):
        try:
            profile["preferences"] = json.loads(prefs)
        except (json.JSONDecodeError, TypeError):
            profile["preferences"] = []
    return profile


def _build_query_text(buyer: dict) -> str:
    """Build a structured text string from the buyer profile for keyword extraction."""
    prefs = buyer.get("preferences") or []
    if isinstance(prefs, str):
        prefs = json.loads(prefs)
    prefs_str = ", ".join(prefs) if prefs else ""

    parts = [
        f"Segment: {buyer.get('segment', '')}",
        f"Category preferences: {prefs_str}",
        f"Budget: ${float(buyer.get('budget_min', 0)):.2f} "
        f"to ${float(buyer.get('budget_max', 0)):.2f}",
    ]
    if buyer.get("notes"):
        parts.append(f"Notes: {buyer['notes']}")
    return "\n".join(parts)


async def _load_inventory_items(
    item_ids: list[str],
    db: AsyncSession,
) -> dict[str, dict]:
    """Fetch available inventory rows by ID. Returns {item_id: row_dict}."""
    if not item_ids:
        return {}
    placeholders = ", ".join(f":id{i}" for i in range(len(item_ids)))
    params = {f"id{i}": iid for i, iid in enumerate(item_ids)}
    result = await db.execute(
        text(
            f"SELECT * FROM inventory_items "
            f"WHERE id IN ({placeholders}) AND status = 'available'"
        ),
        params,
    )
    return {row.id: dict(row._mapping) for row in result.fetchall()}


async def _load_rejection_counts(
    segment: str,
    db: AsyncSession,
) -> dict[str, int]:
    """Returns {retailer_id: rejection_count} for the given segment."""
    try:
        result = await db.execute(
            text("""
                SELECT   i.retailer_id, COUNT(*) AS cnt
                FROM     behavior_logs  bl
                JOIN     inventory_items i  ON bl.item_id  = i.id
                JOIN     buyer_profiles bp  ON bl.user_id  = bp.user_id
                WHERE    bl.action    = 'rejected'
                  AND    bp.segment   = :segment
                GROUP BY i.retailer_id
            """),
            {"segment": segment},
        )
        return {row.retailer_id: row.cnt for row in result.fetchall()}
    except Exception:
        # Tables may not exist yet in a fresh environment — degrade gracefully
        logger.debug("[R-04] Could not load rejection counts — defaulting to empty.")
        return {}


async def _store_match_results(
    user_id: str,
    cards: list[RecommendationCard],
    db: AsyncSession,
) -> None:
    """Persist one MatchResult row per recommendation card (analytics + CTR tracking)."""
    for card in cards:
        db.add(MatchResult(
            buyer_user_id=user_id,
            item_id=card.item_id,
            similarity_score=card.similarity_score,
            composite_score=card.composite_score,
            recommendation_text=card.recommendation_text,
        ))
    await db.commit()


async def _create_retailer_alerts(
    cards: list[RecommendationCard],
    db: AsyncSession,
) -> None:
    """
    Create one RetailerAlert per matched item.

    Deduplication: if an alert for the same item_id was created within the
    last hour, increment its match_count instead of inserting a new row.

    R-02: alert rows store item info + match_score_label only — no buyer data.
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    for card in cards:
        score_label = (
            "Strong" if card.composite_score >= 0.75
            else "Good" if card.composite_score >= 0.50
            else "Moderate"
        )
        # Check for recent duplicate
        existing = await db.execute(
            text("""
                SELECT id, match_count FROM retailer_alerts
                WHERE  item_id     = :iid
                  AND  retailer_id = :rid
                  AND  created_at  >= :cutoff
                ORDER  BY created_at DESC
                LIMIT  1
            """),
            {"iid": card.item_id, "rid": card.retailer_id, "cutoff": one_hour_ago},
        )
        row = existing.fetchone()

        if row:
            await db.execute(
                text("UPDATE retailer_alerts SET match_count = :cnt WHERE id = :aid"),
                {"cnt": row.match_count + 1, "aid": row.id},
            )
        else:
            db.add(RetailerAlert(
                retailer_id=card.retailer_id,
                item_id=card.item_id,
                item_title=card.title,
                match_score_label=score_label,
            ))

    await db.commit()
