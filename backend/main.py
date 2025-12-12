"""FastAPI application entry point for LogSentinel AI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from config import get_settings
import logging

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LogSentinel AI",
    description="Multi-Agent SOC Analyst for Critical Infrastructure",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting LogSentinel AI...")
    create_db_and_tables()
    logger.info("Database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "LogSentinel AI"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LogSentinel AI",
        "version": "1.0.0",
        "description": "Multi-Agent SOC Analyst for Critical Infrastructure"
    }


# Import routers
from routers import upload, search, anomalies, logs, copilot

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(anomalies.router, prefix="/api", tags=["anomalies"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["copilot"])
