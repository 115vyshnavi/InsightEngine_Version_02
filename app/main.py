"""InsightEngine FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logging import logger
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.query import router as query_router
from app.api.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting InsightEngine Financial RAG Service...")
    settings.ensure_directories()
    logger.info(f"Vector Database mode: {settings.VECTOR_DB}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down InsightEngine Financial RAG Service.")


app = FastAPI(
    title="InsightEngine - Financial Report Analysis System",
    description="Production-grade AI-powered financial report analysis with multi-vector table preservation, hybrid retrieval, FlashRank reranking, and deterministic arithmetic.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "dist"
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(jobs_router)


@app.get("/")
def root():
    """Provides a useful response when the backend base URL is opened directly."""
    frontend_index = FRONTEND_DIST / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "service": "InsightEngine Financial RAG",
        "status": "healthy",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
