# VGP Platform — Build Trace Log

## Module 1: Auth — 2026-04-11

### Files Created
- `auth/__init__.py`
- `auth/database.py`
- `auth/models.py`
- `auth/schemas.py`
- `auth/jwt_utils.py`
- `auth/routes.py`
- `auth/main.py`
- `auth/requirements.txt`
- `.env.example`

### Endpoints
| Method | Path         | Auth Required | Description                          |
|--------|--------------|---------------|--------------------------------------|
| POST   | /auth/signup | No            | Register buyer or retailer, get JWT  |
| POST   | /auth/login  | No            | Authenticate, get JWT                |
| GET    | /auth/me     | Yes (any role)| Return current user from JWT         |
| GET    | /health      | No            | Service liveness check               |

### JWT Payload
```json
{ "sub": "<user_id>", "email": "<email>", "role": "buyer|retailer", "iat": <unix>, "exp": <unix+24h> }
```

### Rules Enforced
| Rule | How Enforced |
|------|-------------|
| R-06 | `require_buyer_role` dependency in `jwt_utils.py` — raises HTTP 403 if JWT role != "buyer". Applied to all match/buyer-pipeline routes in subsequent modules. Retailer cannot bypass this at the application layer. |

### Validation
- HTTP 400: Pydantic raises automatically for missing/invalid fields (email format, password < 8 chars)
- HTTP 401: Wrong credentials on login; expired or invalid JWT on protected routes
- HTTP 403: R-06 role block
- HTTP 409: Duplicate email on signup

### Decisions & Notes
- Passwords hashed with bcrypt (salted, 12 rounds default)
- Token expiry: 24 hours
- SQLite used for development; swap `DATABASE_URL` to `postgresql+asyncpg://...` for production
- `require_buyer_role` and `require_retailer_role` exported from `jwt_utils.py` — downstream modules import these as FastAPI `Depends()` guards

### Status
**COMPLETE — approved 2026-04-11**

---

## Module 2: Inventory Upload Pipeline — 2026-04-11

### Files Created
- `inventory/__init__.py`
- `inventory/database.py`
- `inventory/models.py`
- `inventory/schemas.py`
- `inventory/embeddings.py`
- `inventory/cleanup.py`
- `inventory/routes.py`
- `inventory/main.py`
- `inventory/requirements.txt`
- `.env.example` — added `CHROMA_PATH`

### Endpoints
| Method | Path                        | Auth             | Description                                       |
|--------|-----------------------------|------------------|---------------------------------------------------|
| POST   | /inventory/upload           | Retailer JWT     | Validate, store to SQLite, embed to ChromaDB      |
| GET    | /inventory/                 | Retailer JWT     | List calling retailer's items                     |
| GET    | /inventory/{item_id}        | Retailer JWT     | Fetch single item (must be owned by caller)       |
| PATCH  | /inventory/{item_id}/status | Retailer JWT     | Mark sold/expired; immediate R-05 de-index        |
| GET    | /health                     | None             | Liveness check                                    |

### Required Inventory Fields (HTTP 400 if missing or invalid)
| Field        | Type     | Constraint                        |
|--------------|----------|-----------------------------------|
| title        | str      | Non-blank                         |
| category     | str      | Non-blank                         |
| quantity     | int      | > 0                               |
| price        | float    | >= 0                              |
| condition    | enum     | new / like_new / good / fair / poor |
| expiry_date  | datetime | Must be in the future             |

### Rules Enforced
| Rule | How Enforced |
|------|-------------|
| R-03 | `embeddings.upsert_item()` runs in a thread-pool executor with `asyncio.wait_for(..., timeout=1.5)`. On timeout: item is saved to DB (`embedded=False`), 201 still returned. Will be indexed on next cleanup pass. Cache fallback for query side deferred to Match module. |
| R-05 | Two-path strategy: (1) **Hourly background loop** (`cleanup.run_cleanup_loop`) queries DB for `status IN ('sold','expired') OR expiry_date <= now()` with `embedded=True`, deletes from ChromaDB. (2) **Immediate path** in `PATCH /{id}/status` — de-indexes synchronously when retailer marks an item sold/expired. Worst-case lag: ~1 hour. |
| R-06 | All routes protected by `require_retailer_role` (imported from `auth.jwt_utils`). Buyers receive HTTP 403. |

### Validation Errors → HTTP 400
- FastAPI's built-in 422 for Pydantic errors is overridden by a global `exception_handler(ValidationError)` that returns HTTP 400 with the full error list.

### ChromaDB Details
- Engine: `chromadb.PersistentClient` (local disk, no API key)
- Embedding model: `all-MiniLM-L6-v2` (via `sentence-transformers`, auto-downloaded on first run)
- Distance metric: cosine similarity (`hnsw:space: cosine`)
- Collection name: `inventory`
- Metadata stored per item: `retailer_id`, `category`, `condition`, `price`, `quantity`, `status`
- Model warm-up runs in lifespan on startup (prevents cold-start latency on first upload)

### Decisions & Notes
- Both modules share the same `DATABASE_URL` (single SQLite file in dev)
- `embedded` flag on `InventoryItem` tracks ChromaDB index state — prevents double-delete and enables re-index recovery
- `require_retailer_role` imported directly from `auth.jwt_utils`; run all services from `vgp-platform/` so the package is on the Python path
- `description` and `location` are optional but included in embedding text when present, improving match quality

### Status
**COMPLETE — approved 2026-04-11**

---

## Module 3: Buyer Onboarding Pipeline — 2026-04-11

### Files Created
- `buyer/__init__.py`
- `buyer/database.py`
- `buyer/models.py`
- `buyer/schemas.py`
- `buyer/embeddings.py`
- `buyer/routes.py`
- `buyer/main.py`
- `buyer/requirements.txt`

### Endpoints
| Method | Path                | Auth        | Description                                          |
|--------|---------------------|-------------|------------------------------------------------------|
| POST   | /buyer/onboarding   | Buyer JWT   | Create profile; 409 if exists; embeds to ChromaDB    |
| GET    | /buyer/profile      | Buyer JWT   | Fetch own full profile                               |
| PUT    | /buyer/profile      | Buyer JWT   | Partial update; re-embeds to ChromaDB on any change  |
| POST   | /buyer/behavior     | Buyer JWT   | Log viewed / clicked / purchased / rejected event    |
| GET    | /buyer/behavior     | Buyer JWT   | Fetch own behavior history                           |
| GET    | /health             | None        | Liveness check                                       |

### DB Tables
| Table           | Purpose                                                    |
|-----------------|------------------------------------------------------------|
| buyer_profiles  | Segment, preferences (JSON), budget_min/max, location, notes |
| behavior_logs   | user_id, action, item_id, item_category — match pipeline reads this for re-ranking |

### Buyer Segment Options
`reseller` | `nonprofit` | `smb` | `consumer`

### Required Fields (HTTP 400 if missing or invalid)
| Field        | Constraint                                    |
|--------------|-----------------------------------------------|
| segment      | Must be one of the four valid segment values  |
| preferences  | Non-empty list, ≤ 20 items, no blank strings  |
| budget_min   | >= 0                                          |
| budget_max   | > budget_min                                  |

### Rules Enforced
| Rule | How Enforced |
|------|-------------|
| R-02 | **Three layers**: (1) All routes gated by `require_buyer_role` — retailers receive HTTP 403 and cannot reach any buyer data. (2) `BuyerProfileResponse` schema (full data) is only ever returned on buyer-authenticated routes. (3) `BuyerMatchSummary` schema is defined here as the ONLY buyer-related object permitted in retailer-facing contexts — it contains `buyer_id` (opaque ID), `match_score`, and `match_label` only. Segment, preferences, budget, history, and PII are structurally absent from this schema. |
| R-03 | `upsert_buyer()` and `query_buyers()` both use `asyncio.wait_for(..., timeout=1.5)`. Timeout on upsert → `embedded=False`, graceful 201 return. Timeout on query → empty result returned. |

### ChromaDB Details
- Collection: `buyer_profiles` (separate from `inventory` collection)
- Same `CHROMA_PATH`, same model (`all-MiniLM-L6-v2`), same cosine distance
- Metadata stored: `user_id`, `segment`, `budget_min`, `budget_max`
- `query_buyers()` is exported for **match pipeline internal use only** — caller is responsible for R-02 compliance

### R-02 Schema Boundary (critical)
```
BuyerProfileResponse   →  buyer-authenticated routes ONLY
BuyerMatchSummary      →  the ONLY type crossing the buyer→retailer boundary
BehaviorLogResponse    →  buyer-authenticated routes ONLY, never forwarded
```

### Decisions & Notes
- `preferences` stored as JSON array in SQLite; included in embedding text as comma-separated string
- Profile update re-embeds to ChromaDB on any field change — ensures vector stays current
- `embedded` flag prevents double-delete and enables recovery if ChromaDB times out
- Run on port 8002: `uvicorn buyer.main:app --reload --port 8002`

### Status
**COMPLETE — approved 2026-04-11**

---

## Module 4: Match Pipeline — 2026-04-11

### Files Created
- `match/__init__.py`
- `match/database.py`
- `match/models.py`
- `match/schemas.py`
- `match/cache.py`
- `match/vector.py`
- `match/ranker.py`
- `match/llm.py`
- `match/routes.py`
- `match/main.py`
- `match/requirements.txt`

### Endpoints
| Method | Path                          | Auth          | Description                                                     |
|--------|-------------------------------|---------------|-----------------------------------------------------------------|
| POST   | /match/recommendations        | Buyer JWT     | Full pipeline → top-5 LLM-personalised recommendation cards    |
| GET    | /match/alerts                 | Retailer JWT  | Retailer dashboard — last 7 days of match alerts (R-02 safe)   |
| PATCH  | /match/alerts/{id}/read       | Retailer JWT  | Mark an alert as read                                           |
| GET    | /health                       | None          | Liveness + cache size                                           |

### DB Tables
| Table            | Purpose                                                                    |
|------------------|----------------------------------------------------------------------------|
| match_results    | One row per recommendation served — buyer_user_id stored for analytics KPIs (never forwarded to retailers) |
| retailer_alerts  | R-02 safe: item_id, item_title, match_score_label, match_count, is_read — zero buyer fields |

### Full Pipeline (POST /match/recommendations)
```
1. Segment check    load buyer profile from buyer_profiles via JWT sub
                    → raises 404 if no profile (prompts onboarding)
2. Cache check      SHA-256(user_id + query_text) key, 5-min TTL
                    → cache hit: return immediately, served_from_cache=True
3. Vector search    query_inventory(query_text, n=20) with 1.5s timeout (R-03)
                    → timeout: return empty + log warning
4. Inventory load   SELECT from inventory_items WHERE status='available'
                    → skips sold/expired items silently (R-05 interplay)
5. R-04 check       COUNT rejections per retailer for buyer's segment
                    via JOIN behavior_logs × inventory_items × buyer_profiles
6. Rank + filter    composite_score = similarity + price_fit + qty + R-04_penalty
                    sorted descending; clamp [0.0, 1.0]
7. R-01 reorder     if segment==nonprofit: free items first, then discounted
                    (price ≤ 25% of budget_max), then rest
8. LLM generation   asyncio.gather() → 5 parallel Ollama llama3 calls, 10s timeout each
                    R-01: nonprofit prompt structurally forbids profit/ROI/margin language
                    fallback: deterministic template if Ollama unavailable
9. Persist          MatchResult rows (analytics) + RetailerAlert per item (with hourly dedup)
10. Cache + return  result_cache.set_result(); return MatchResponse to buyer
```

### Scoring Formula (ranker.py)
```
composite = similarity                                (base, 0–1)
          + 0.10  if price == 0 (free)
          + 0.10  if budget_min ≤ price ≤ budget_max
          + 0.05  if price < budget_min
          − 0.20  if price > budget_max
          + 0.05  if quantity ≥ 10
          − 0.50  if quantity == 0
          − 0.30  if retailer has ≥ 3 same-segment rejections (R-04)
          → clamp(result, 0.0, 1.0)
```

### Rules Enforced
| Rule | How Enforced |
|------|-------------|
| R-01 | **Two-layer enforcement**: (1) Sort override in `ranker._nonprofit_reorder()` — free/discounted items always float to top of results for nonprofit segment. (2) LLM prompt in `llm.py` structurally prohibits words: profit, revenue, ROI, margin, markup, financial return for nonprofit segment. Template fallback also uses mission framing. |
| R-02 | **Three-layer enforcement**: (1) `require_buyer_role` on `/match/recommendations` — retailers blocked at dependency (R-06). (2) `require_retailer_role` on `/match/alerts` — buyers cannot see alert data. (3) `RetailerAlertResponse` schema structurally contains zero buyer fields — only item_title, match_score_label, match_count. `buyer_user_id` stored only in `match_results` (internal analytics table). |
| R-03 | ChromaDB query: `asyncio.wait_for(..., timeout=1.5)` in `vector.py`. Timeout → empty result, caller checks `cache.get()`. Total pipeline timing logged; warning emitted if > 2s. Cache serves subsequent identical requests in < 50 ms. LLM calls are the primary latency source for first-time queries; template fallback caps per-item LLM time at 10s. |
| R-04 | Rejection counts loaded via cross-table SQL JOIN (behavior_logs × inventory_items × buyer_profiles). Retailers with ≥ 3 same-segment rejections receive −0.30 composite score penalty on all their items for that segment. |
| R-06 | `require_buyer_role` on `POST /match/recommendations` — retailer JWT raises HTTP 403 before any pipeline logic runs. |

### LLM Details
- Endpoint: `http://localhost:11434/api/generate`
- Model: `llama3`
- Per-call timeout: 10 s (all 5 run in parallel via `asyncio.gather`)
- Temperature: 0.4, max tokens: 120
- Fallback: `_template_fallback()` — segment-aware, R-01 compliant

### R-02 Schema Boundary (match module)
```
RecommendationCard      → buyer-authenticated route ONLY
RetailerAlertResponse   → retailer-authenticated route ONLY; zero buyer fields
MatchResult (DB table)  → internal analytics; buyer_user_id never forwarded
```

### Cross-Module DB Access
All modules share the same SQLite file. Match uses raw `sqlalchemy.text()` queries
to read `buyer_profiles`, `behavior_logs`, and `inventory_items` — no circular imports.

### Decisions & Notes
- `query_text` mirrors buyer embedding format from `buyer/embeddings.py` so cosine similarity is meaningful across buyer→inventory matching
- Cache key = SHA-256(user_id + query_text) — invalidated automatically when profile is updated (query_text changes)
- Alert deduplication: if same item was alerted within last hour, `match_count` is incremented rather than a new row inserted
- Run on port 8003: `uvicorn match.main:app --reload --port 8003`

### Status
**COMPLETE — awaiting approval**
