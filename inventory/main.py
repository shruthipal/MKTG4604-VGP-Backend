import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .cleanup import run_cleanup_loop
from .database import Base, engine
from .embeddings import warmup
from .routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Warm up ChromaDB / sentence-transformer model so first upload is fast
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warmup)

    # 3. Start R-05 hourly cleanup loop
    cleanup_task = asyncio.create_task(run_cleanup_loop())
    logger.info("Inventory service ready.")

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="VGP Inventory Service",
    version="1.0.0",
    description=(
        "Retailer inventory upload, storage, and vector embedding pipeline. "
        "Enforces R-03 (≤2s responses) and R-05 (de-index sold/expired within 24h)."
    ),
    lifespan=lifespan,
)


# ── Global exception handler: convert Pydantic ValidationError → HTTP 400 ─────
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "inventory"}
