from fastapi import APIRouter, HTTPException
from typing import List

from app.models.matching import SuggestionRequest, SuggestionResponse
from app.services.graph_service import graph_service
from app.services.database_service import database_service
import json

router = APIRouter()

@router.post("/generate", response_model=SuggestionResponse)
async def generate_skill_suggestions(
    request: SuggestionRequest
):
    """Generate skill gap suggestions for a specific resume-JD pair"""
    
    try:
        # Check if match exists
        existing_match = await database_service.get_match_result(
            request.resume_id, 
            request.jd_id
        )
        
        if not existing_match:
            # Need to run matching first
            resume_doc = await database_service.get_document_by_id(request.resume_id)
            jd_doc = await database_service.get_document_by_id(request.jd_id)
            
            if not resume_doc or not jd_doc:
                raise HTTPException(status_code=404, detail="Resume or Job Description not found")
            
            # Run matching to get suggestions
            match_result = await graph_service.process_single_match(
                resume_id=request.resume_id,
                jd_id=request.jd_id,
                resume_content=resume_doc["raw_content"],
                jd_content=jd_doc["raw_content"]
            )
            
            current_match_percentage = match_result.match_percentage
            suggestions_data = match_result.skill_comparison.detailed_analysis.get("skill_gaps", {})
        else:
            current_match_percentage = existing_match.get("match_percentage", 0.0)
            suggestions_data = json.loads(existing_match.get("suggestions_json", "{}"))
        
        # Parse suggestions data
        if isinstance(suggestions_data, str):
            try:
                suggestions_data = json.loads(suggestions_data)
            except json.JSONDecodeError:
                suggestions_data = {}
        
        # Extract skill gaps
        from app.models.skill import SkillGap
        skill_gaps = SkillGap(
            missing_skills=suggestions_data.get("missing_skills", []),
            skill_gaps=suggestions_data.get("critical_skill_gaps", []),
            recommendations=suggestions_data.get("specific_recommendations", {}).get("immediate_actions", []),
            priority_skills=suggestions_data.get("priority_skills", [])
        )
        
        # Extract improvement suggestions
        improvement_suggestions = []
        roadmap = suggestions_data.get("improvement_roadmap", {})
        for phase_key, phase_data in roadmap.items():
            if isinstance(phase_data, dict) and "key_activities" in phase_data:
                improvement_suggestions.extend(phase_data["key_activities"])
        
        # Extract priority skills
        priority_skills = []
        critical_gaps = suggestions_data.get("critical_skill_gaps", [])
        for gap in critical_gaps:
            if isinstance(gap, dict) and "skill" in gap:
                priority_skills.append(gap["skill"])
        
        # Calculate potential improvement
        projected_outcomes = suggestions_data.get("projected_outcomes", {})
        potential_improvement = projected_outcomes.get("6_month_match_percentage", 80.0) - current_match_percentage
        
        response = SuggestionResponse(
            resume_id=request.resume_id,
            jd_id=request.jd_id,
            current_match_percentage=current_match_percentage,
            skill_gaps=skill_gaps,
            improvement_suggestions=improvement_suggestions,
            potential_match_increase=max(0, potential_improvement),
            priority_skills=priority_skills
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")

@router.get("/close-matches/{jd_id}")
async def get_close_matches_suggestions(
    jd_id: str,
    min_score: float = 65.0,
    max_score: float = 79.9
):
    """Get skill suggestions for all close matches (65-79% range)"""
    
    try:
        # Get all matches for this JD
        matches = await database_service.get_match_results_by_jd(jd_id)
        
        # Filter close matches
        close_matches = [
            m for m in matches 
            if min_score <= m.get("match_percentage", 0) <= max_score
        ]
        
        if not close_matches:
            return {
                "jd_id": jd_id,
                "message": "No close matches found in the specified range",
                "suggestions": []
            }
        
        # Generate suggestions for each close match
        suggestions = []
        for match in close_matches:
            try:
                suggestion_request = SuggestionRequest(
                    resume_id=match.get("resume_id"),
                    jd_id=jd_id
                )
                
                suggestion = await generate_skill_suggestions(suggestion_request)
                suggestions.append(suggestion)
                
            except Exception as e:
                # Log error but continue with other matches
                print(f"Error generating suggestion for resume {match.get('resume_id')}: {e}")
                continue
        
        return {
            "jd_id": jd_id,
            "total_close_matches": len(close_matches),
            "successful_suggestions": len(suggestions),
            "score_range": f"{min_score}% - {max_score}%",
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating batch suggestions: {str(e)}")

@router.get("/improvement-roadmap/{resume_id}/{jd_id}")
async def get_improvement_roadmap(
    resume_id: str,
    jd_id: str
):
    """Get detailed improvement roadmap for a specific resume-JD pair"""
    
    try:
        # Get existing match data
        match_data = await database_service.get_match_result(resume_id, jd_id)
        
        if not match_data:
            raise HTTPException(status_code=404, detail="Match result not found. Run matching first.")
        
        # Extract roadmap from suggestions
        suggestions_json = match_data.get("suggestions_json", "{}")
        if isinstance(suggestions_json, str):
            try:
                suggestions_data = json.loads(suggestions_json)
            except json.JSONDecodeError:
                suggestions_data = {}
        else:
            suggestions_data = suggestions_json
        
        roadmap = suggestions_data.get("improvement_roadmap", {})
        
        if not roadmap:
            raise HTTPException(status_code=404, detail="No improvement roadmap available")
        
        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "current_match_percentage": match_data.get("match_percentage", 0.0),
            "target_match_percentage": 80.0,
            "improvement_roadmap": roadmap,
            "projected_outcomes": suggestions_data.get("projected_outcomes", {}),
            "success_metrics": suggestions_data.get("success_metrics", {}),
            "learning_resources": suggestions_data.get("specific_recommendations", {}).get("learning_resources", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving roadmap: {str(e)}")
