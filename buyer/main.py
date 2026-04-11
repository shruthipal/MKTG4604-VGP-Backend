import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .database import Base, engine
from .embeddings import warmup
from .routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create DB tables (buyer_profiles, behavior_logs)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Warm ChromaDB model (reuses on-disk cache from inventory service)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warmup)

    logger.info("Buyer service ready.")
    yield


app = FastAPI(
    title="VGP Buyer Service",
    version="1.0.0",
    description=(
        "Buyer onboarding, profile storage, and vector embedding pipeline. "
        "Enforces R-02 (buyer data never exposed to retailers)."
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
    return {"status": "ok", "service": "buyer"}
