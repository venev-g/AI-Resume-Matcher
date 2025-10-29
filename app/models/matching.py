from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.skill import SkillComparison, SkillGap

class MatchResult(BaseModel):
    resume_id: str
    jd_id: str
    match_percentage: float
    skill_comparison: SkillComparison
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    technical_match: float
    non_technical_match: float
    recommendation: str
    processed_at: datetime

class MatchingRequest(BaseModel):
    job_description_id: str
    resume_ids: Optional[List[str]] = None  # If None, match all resumes

class MatchingResponse(BaseModel):
    jd_id: str
    total_resumes_processed: int
    high_matches: List[MatchResult]  # >= 80%
    close_matches: List[MatchResult]  # 65-79%
    low_matches: List[MatchResult]  # < 65%
    processing_time: float

class SuggestionRequest(BaseModel):
    resume_id: str
    jd_id: str

class SuggestionResponse(BaseModel):
    resume_id: str
    jd_id: str
    current_match_percentage: float
    skill_gaps: SkillGap
    improvement_suggestions: List[str]
    potential_match_increase: float
    priority_skills: List[str]
