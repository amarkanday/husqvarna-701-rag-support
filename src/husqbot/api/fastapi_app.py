"""
FastAPI application for Husqvarna 701 RAG Support System.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routes import query, health, admin, metrics
from .middleware.logging import LoggingMiddleware
from .middleware.auth import AuthMiddleware
from .dependencies import get_rag_system
from ..core.rag_system import HusqvarnaRAGSystem
from ..utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Husqvarna 701 RAG Support System...")
    
    # Initialize RAG system
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
    
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    rag_system = HusqvarnaRAGSystem(project_id, location)
    app.state.rag_system = rag_system
    
    logger.info("RAG system initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Husqvarna 701 RAG Support System...")


# Create FastAPI app
app = FastAPI(
    title="Husqvarna 701 RAG Support System",
    description="AI-powered technical support system for Husqvarna 701 Enduro motorcycles",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Include routers
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Husqvarna 701 RAG Support System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        rag_system = get_rag_system()
        stats = await rag_system.get_system_stats()
        
        return {
            "status": "healthy",
            "system_stats": stats,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    uvicorn.run(
        "src.husqbot.api.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 