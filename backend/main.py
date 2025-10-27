"""FastAPI server for AI Resume Matcher system."""

import logging
import os
import shutil
import tempfile
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import MatchResponse
from graph_executor import GraphExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global executor instance
graph_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global graph_executor
    
    logger.info("Starting AI Resume Matcher API")
    
    # Initialize graph executor
    try:
        graph_executor = GraphExecutor()
        logger.info("Successfully initialized GraphExecutor")
    except Exception as e:
        logger.error(f"Failed to initialize GraphExecutor: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Resume Matcher API")


# Create FastAPI application
app = FastAPI(
    title="Enterprise AI Resume Matcher",
    description="Multi-agent AI system for matching resumes to job descriptions",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "ai-resume-matcher",
        "version": "1.0.0"
    }


@app.post("/api/match", response_model=MatchResponse)
async def match_resumes(
    jd_text: str = Form(..., description="Job description text"),
    files: List[UploadFile] = File(..., description="Resume PDF files")
):
    """
    Match resumes to job description.
    
    This endpoint processes a job description and multiple resume PDFs,
    orchestrating the five-agent workflow to evaluate matches and provide
    recommendations.
    
    Args:
        jd_text: Job description text
        files: List of resume PDF files
        
    Returns:
        MatchResponse with detailed match results
        
    Raises:
        HTTPException: If validation fails or processing errors occur
    """
    temp_files = []
    
    try:
        # Validate inputs
        if not jd_text or not jd_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Job description text cannot be empty"
            )
        
        if not files:
            raise HTTPException(
                status_code=400,
                detail="At least one resume file is required"
            )
        
        if len(files) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 resume files allowed per request"
            )
        
        logger.info(f"Received match request with {len(files)} resume files")
        
        # Save uploaded files to temporary directory
        temp_dir = tempfile.mkdtemp()
        
        for idx, file in enumerate(files):
            # Validate file type
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only PDF files are supported. Invalid file: {file.filename}"
                )
            
            # Validate file size (max 10MB)
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large (max 10MB): {file.filename}"
                )
            
            # Save to temp file
            temp_file_path = os.path.join(temp_dir, f"resume_{idx + 1}.pdf")
            with open(temp_file_path, "wb") as f:
                f.write(content)
            
            temp_files.append(temp_file_path)
            logger.info(f"Saved temp file: {temp_file_path}")
        
        # Execute workflow
        logger.info("Starting workflow execution")
        result = await graph_executor.execute(
            jd_text=jd_text,
            resume_files=temp_files
        )
        
        logger.info(f"Workflow completed: {result.get('total_resumes', 0)} resumes processed")
        
        return MatchResponse(**result)
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error processing match request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
        
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")
        
        # Cleanup temp directory
        if temp_files:
            temp_dir = os.path.dirname(temp_files[0])
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to delete temp directory {temp_dir}: {e}")


@app.get("/api/statistics")
async def get_statistics():
    """
    Get system statistics.
    
    Returns aggregate statistics from all match evaluations stored in MongoDB.
    
    Returns:
        Dictionary containing statistics
    """
    try:
        from services.mongodb_service import MongoDBService
        
        mongodb = MongoDBService()
        await mongodb.connect()
        
        stats = await mongodb.get_statistics()
        
        await mongodb.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@app.get("/api/history")
async def get_match_history(limit: int = 10, skip: int = 0):
    """
    Get match history.
    
    Retrieves historical match results from MongoDB.
    
    Args:
        limit: Maximum number of records to return (default: 10)
        skip: Number of records to skip for pagination (default: 0)
        
    Returns:
        List of historical match results
    """
    try:
        from services.mongodb_service import MongoDBService
        
        if limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Maximum limit is 100 records"
            )
        
        mongodb = MongoDBService()
        await mongodb.connect()
        
        history = await mongodb.get_match_history(limit=limit, skip=skip)
        
        await mongodb.close()
        
        return {
            "results": history,
            "count": len(history),
            "limit": limit,
            "skip": skip
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
