"""
Main FastAPI application initialization and configuration.

CrossInsure AI - AI-Powered Insurance Fraud Detection System
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import init_db, close_db
from app.api.routes import auth, claims, admin
from app.schemas import ErrorResponse

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description="AI-Powered Insurance Fraud Detection System",
    version=settings.api_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware configuration
# Adjust these settings based on your deployment environment
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",  # Live Server default port
    "http://127.0.0.1:5500",
    "null",  # For file:// protocol
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """
    Handle RuntimeError (e.g., database unavailable).
    """
    error_msg = str(exc)
    if "Database is not available" in error_msg:
        logger.warning(f"Database unavailable for request: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=jsonable_encoder(ErrorResponse(
                error_code="SERVICE_UNAVAILABLE",
                message="Service is initializing. Please try again in a moment.",
                timestamp=datetime.now(timezone.utc),
            )),
        )
    # Re-raise other RuntimeErrors
    raise exc


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Logs the error and returns a standardized error response.
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            timestamp=datetime.now(timezone.utc),
        )),
    )


# Lifespan events
@app.on_event("startup")
async def startup_event():
    """
    Initialize the application on startup.
    
    - Set up logging
    - Initialize database
    """
    logger.info(
        f"Starting {settings.api_title} (v{settings.api_version}) "
        f"in {settings.environment} environment"
    )
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {str(e)}")
        logger.info("Application will continue without local database - using Supabase for data storage")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on shutdown.
    
    - Close database connections
    """
    logger.info("Shutting down application")
    
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    
    Returns basic health status information.
    """
    from app.core.database import database_available
    
    return {
        "status": "healthy",
        "service": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "database_available": database_available,
        "gemini_configured": settings.gemini_api_key is not None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# API Routes (must be registered BEFORE static files mount)
app.include_router(auth.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


@app.get("/", tags=["Root"])
async def root():
    """Serve the insurer dashboard as the root page."""
    index_path = os.path.join(frontend_dir, "insurer.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"service": settings.api_title, "version": settings.api_version}


# Mount static files AFTER all routes are defined
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_dir}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
