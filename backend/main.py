"""FastAPI application entry point for iphipi."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.utils.redis_client import redis_client
from backend.utils.chroma_client import chroma_client
from backend.models.schemas import HealthResponse
from backend.api import resume, interview, feedback, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    try:
        await redis_client.connect()
        print("Redis connected successfully")
    except Exception as e:
        print(f"Warning: Redis connection failed: {e}")
    try:
        chroma_client.connect()
        print("ChromaDB connected successfully")
    except Exception as e:
        print(f"Warning: ChromaDB connection failed: {e}")

    yield

    # Shutdown
    try:
        await redis_client.disconnect()
    except Exception:
        pass


app = FastAPI(
    title="iphipi - AI Mock Interview Platform",
    description="AI-powered mock interview platform with adaptive questioning and multi-dimensional scoring",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(interview.router, prefix="/api", tags=["Interview"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )
