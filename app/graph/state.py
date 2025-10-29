from typing import TypedDict, Dict, List, Any, Optional
from app.models.skill import Skill

class ResumeMatchingState(TypedDict):
    # Input documents
    resume_doc: str
    job_description_doc: str
    resume_id: str
    jd_id: str
    
    # Skill extraction and processing
    extracted_resume_skills_json: str
    validated_resume_skills_json: str
    classified_resume_skills_json: str
    
    extracted_jd_skills_json: str
    validated_jd_skills_json: str
    classified_jd_skills_json: str
    
    # Matching results
    skill_comparison_json: str
    match_percentage: float
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    
    # Skill gap analysis
    skill_gaps_json: str
    suggestions_json: str
    
    # Metadata
    processing_status: str
    error_message: Optional[str]
