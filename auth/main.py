from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import engine, Base
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="VGP Auth Service",
    version="1.0.0",
    description="Login/signup, JWT issuance, and role-based access control for the VGP platform.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth"}
