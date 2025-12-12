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
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://hackathon-logsentinel-frontend.onrender.com",  # Your frontend domain
        "https://logsentinel-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and directories on startup."""
    import os
    logger.info("Starting LogSentinel AI...")
    
    # Create required directories (non-blocking)
    try:
        os.makedirs("./data/uploads", exist_ok=True)
        os.makedirs("./data/faiss_index", exist_ok=True)
        logger.info("Data directories created successfully")
    except Exception as e:
        logger.warning(f"Failed to create data directories (will use fallback): {e}")
    
    # Initialize database
    try:
        create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise the exception to prevent startup failure
        logger.error("Continuing startup without database - some features may not work")


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


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
