from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from dotenv import load_dotenv

from app.api.routes import upload, matching, suggestions
from app.core.config import settings
from app.core.database import startup_database_event, shutdown_database_event, database_manager
from app.utils.exceptions import CustomException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Handles startup and shutdown events
    """
    # Startup
    try:
        logger.info("Starting application...")
        await startup_database_event()
        logger.info("Application startup completed")
        yield
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
    finally:
        # Shutdown
        try:
            logger.info("Shutting down application...")
            await shutdown_database_event()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Application shutdown failed: {str(e)}")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Resume-JD Matching System",
    description="AI-powered system for matching resumes to job descriptions with skill gap analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )

# Health check endpoints
@app.get("/")
async def root():
    return {"message": "Resume-JD Matching System API", "status": "running"}

@app.get("/health")
async def health_check():
    """Comprehensive health check including database"""
    try:
        # Check database health
        db_health = await database_manager.health_check()
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "version": "1.0.0",
            "database": db_health,
            "services": {
                "api": "healthy",
                "database": db_health["status"]
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e),
                "database": {"status": "error"},
                "services": {
                    "api": "healthy",
                    "database": "error"
                }
            }
        )

# For testing LLM services
@app.get("/test-llm")
async def test_llm_providers():
    """Test all configured LLM providers"""
    from app.services.llm_service import test_all_providers
    
    try:
        results = await test_all_providers()
        return {
            "status": "completed",
            "providers_tested": len(results),
            "results": results
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

# Include routers
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["matching"])
app.include_router(suggestions.router, prefix="/api/v1/suggestions", tags=["suggestions"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
