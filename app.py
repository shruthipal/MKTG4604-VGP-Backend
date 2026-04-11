"""
VGP Platform — combined entry point.

Mounts all four service routers on a single port so a single ngrok tunnel
(or Vercel environment variable) covers the entire backend.

Start:
    cd vgp-platform
    uvicorn app:app --port 8000 --reload

Docs: http://localhost:8000/docs
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# ── Database tables ───────────────────────────────────────────────────────────
from auth.database import Base as AuthBase, engine as auth_engine
from buyer.database import Base as BuyerBase, engine as buyer_engine
from inventory.database import Base as InvBase, engine as inv_engine
from match.database import Base as MatchBase, engine as match_engine

# ── Routers ───────────────────────────────────────────────────────────────────
from auth.routes import router as auth_router
from buyer.routes import router as buyer_router
from inventory.routes import router as inv_router
from match.routes import router as match_router

# ── Background tasks / warmup ─────────────────────────────────────────────────
from buyer.embeddings import warmup as buyer_warmup
from inventory.cleanup import run_cleanup_loop
from inventory.embeddings import warmup as inv_warmup
from match import cache as result_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_CACHE_EVICTION_INTERVAL = 300  # seconds


async def _cache_eviction_loop() -> None:
    while True:
        await asyncio.sleep(_CACHE_EVICTION_INTERVAL)
        evicted = result_cache.evict_expired()
        if evicted:
            logger.debug("Cache eviction: removed %d expired entries.", evicted)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all DB tables
    for engine, base in [
        (auth_engine, AuthBase),
        (inv_engine, InvBase),
        (buyer_engine, BuyerBase),
        (match_engine, MatchBase),
    ]:
        async with engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)

    # 2. Warm up ChromaDB + sentence-transformer (shared on-disk cache)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, inv_warmup)   # inventory collection + model
    await loop.run_in_executor(None, buyer_warmup)  # buyer_profiles collection

    # 3. Start background tasks
    cleanup_task = asyncio.create_task(run_cleanup_loop())
    eviction_task = asyncio.create_task(_cache_eviction_loop())

    logger.info("VGP platform ready — all services on port 8000.")
    yield

    cleanup_task.cancel()
    eviction_task.cancel()
    for task in (cleanup_task, eviction_task):
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="VGP Platform — Surplus Connect",
    version="1.0.0",
    description=(
        "Surplus Connect inventory matching and recommendation platform. "
        "Combined entry point for auth, inventory, buyer, and match services."
    ),
    lifespan=lifespan,
)

# ── CORS: allow all origins so Vercel frontend + local dev both work ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Pydantic ValidationError → HTTP 400 ───────────────────────────────
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(inv_router)
app.include_router(buyer_router)
app.include_router(match_router)


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "services": ["auth", "inventory", "buyer", "match"],
        "cache_entries": result_cache.size(),
    }
