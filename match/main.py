import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import cache as result_cache
from .database import Base, engine
from .routes import router
from .vector import warmup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_CACHE_EVICTION_INTERVAL = 300  # evict expired cache entries every 5 minutes


async def _cache_eviction_loop() -> None:
    while True:
        await asyncio.sleep(_CACHE_EVICTION_INTERVAL)
        evicted = result_cache.evict_expired()
        if evicted:
            logger.debug("Cache eviction: removed %d expired entries.", evicted)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create match-pipeline DB tables (match_results, retailer_alerts)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Warm ChromaDB / sentence-transformer (shared model cache)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warmup)

    # 3. Start background cache eviction
    eviction_task = asyncio.create_task(_cache_eviction_loop())
    logger.info("Match service ready on port 8003.")

    yield

    eviction_task.cancel()
    try:
        await eviction_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="VGP Match Service",
    version="1.0.0",
    description=(
        "Core agentic reasoning module: segment check → vector similarity search → "
        "rank/filter → LLM personalisation → retailer alert. "
        "Enforces R-01 (nonprofit priority), R-02 (buyer data isolation), "
        "R-03 (≤2 s with cache fallback), R-04 (segment rejection de-prioritization), "
        "R-06 (retailer JWT blocked from buyer pipeline)."
    ),
    lifespan=lifespan,
)


# ── Pydantic ValidationError → HTTP 400 ───────────────────────────────────────
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "match",
        "cache_entries": result_cache.size(),
    }
