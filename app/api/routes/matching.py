from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional

from app.models.matching import MatchingRequest, MatchingResponse, MatchResult
from app.services.graph_service import graph_service
from app.services.database_service import database_service
from app.core.config import settings

router = APIRouter()

@router.post("/single", response_model=MatchResult)
async def match_single_resume(
    resume_id: str,
    jd_id: str
):
    """Match a single resume against a job description"""
    
    try:
        # Get documents from database
        resume_doc = await database_service.get_document_by_id(resume_id)
        jd_doc = await database_service.get_document_by_id(jd_id)
        
        if not resume_doc:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not jd_doc:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Process match using LangGraph
        match_result = await graph_service.process_single_match(
            resume_id=resume_id,
            jd_id=jd_id,
            resume_content=resume_doc["raw_content"],
            jd_content=jd_doc["raw_content"]
        )
        
        return match_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing match: {str(e)}")

@router.post("/batch", response_model=MatchingResponse)
async def match_batch_resumes(
    request: MatchingRequest,
    background_tasks: BackgroundTasks
):
    """Match multiple resumes against a job description"""
    
    try:
        # Get job description
        jd_doc = await database_service.get_document_by_id(request.job_description_id)
        
        if not jd_doc:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Process batch matching
        matching_result = await graph_service.process_batch_matching(
            jd_id=request.job_description_id,
            jd_content=jd_doc["raw_content"],
            resume_ids=request.resume_ids
        )
        
        return matching_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch match: {str(e)}")

@router.get("/results/{jd_id}", response_model=List[MatchResult])
async def get_matching_results(
    jd_id: str,
    min_score: Optional[float] = None,
    max_results: int = 100
):
    """Get stored matching results for a job description"""
    
    try:
        # Get match results from database
        matches = await database_service.get_match_results_by_jd(jd_id)
        
        # Filter by minimum score if provided
        if min_score is not None:
            matches = [m for m in matches if m.get("match_percentage", 0) >= min_score]
        
        # Sort by match percentage (descending)
        matches.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
        
        # Limit results
        matches = matches[:max_results]
        
        # Convert to MatchResult objects
        results = []
        for match in matches:
            # This would need proper conversion from dict to MatchResult
            # For now, returning the dict
            results.append(match)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")

@router.get("/summary/{jd_id}")
async def get_matching_summary(jd_id: str):
    """Get summary statistics for matching results"""
    
    try:
        matches = await database_service.get_match_results_by_jd(jd_id)
        
        if not matches:
            raise HTTPException(status_code=404, detail="No matching results found")
        
        # Calculate statistics
        total_matches = len(matches)
        high_matches = len([m for m in matches if m.get("match_percentage", 0) >= 80])
        close_matches = len([m for m in matches if 65 <= m.get("match_percentage", 0) < 80])
        low_matches = len([m for m in matches if m.get("match_percentage", 0) < 65])
        
        avg_score = sum(m.get("match_percentage", 0) for m in matches) / total_matches
        max_score = max(m.get("match_percentage", 0) for m in matches)
        min_score = min(m.get("match_percentage", 0) for m in matches)
        
        return {
            "jd_id": jd_id,
            "total_matches": total_matches,
            "high_matches": high_matches,
            "close_matches": close_matches,
            "low_matches": low_matches,
            "average_score": round(avg_score, 2),
            "max_score": max_score,
            "min_score": min_score,
            "score_distribution": {
                "90-100%": len([m for m in matches if m.get("match_percentage", 0) >= 90]),
                "80-89%": len([m for m in matches if 80 <= m.get("match_percentage", 0) < 90]),
                "70-79%": len([m for m in matches if 70 <= m.get("match_percentage", 0) < 80]),
                "60-69%": len([m for m in matches if 60 <= m.get("match_percentage", 0) < 70]),
                "Below 60%": len([m for m in matches if m.get("match_percentage", 0) < 60])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
