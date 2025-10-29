from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.api.routes import upload, matching, suggestions
from app.core.config import settings
from app.utils.exceptions import CustomException

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Resume-JD Matching System",
    description="AI-powered system for matching resumes to job descriptions with skill gap analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Resume-JD Matching System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

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
