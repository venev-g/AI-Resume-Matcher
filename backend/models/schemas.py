"""Pydantic models for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class JDData(BaseModel):
    """Job Description structured data model."""
    
    job_title: str = Field(..., description="Job title extracted from JD")
    required_skills: List[str] = Field(default_factory=list, description="List of required skills")
    experience_years: float = Field(0.0, description="Required years of experience")
    qualifications: List[str] = Field(default_factory=list, description="Educational and professional qualifications")
    responsibilities: List[str] = Field(default_factory=list, description="Key job responsibilities")


class ResumeData(BaseModel):
    """Resume structured data model."""
    
    candidate_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = Field(None, description="Contact email address")
    skills: List[str] = Field(default_factory=list, description="List of candidate skills")
    experience_years: float = Field(0.0, description="Total years of experience")
    work_history: List[str] = Field(default_factory=list, description="Work experience entries")
    education: List[str] = Field(default_factory=list, description="Educational background")


class SkillGap(BaseModel):
    """Skill gap recommendation model."""
    
    missing_skill: str = Field(..., description="The missing skill name")
    importance: str = Field(..., description="Importance level: high, medium, or low")
    reason: str = Field(..., description="Why this skill is important for the role")
    learning_path: str = Field(..., description="Suggested learning resources or approach")
    estimated_time: str = Field(..., description="Estimated time to acquire the skill")


class MatchResult(BaseModel):
    """Individual resume match result."""
    
    resume_id: str = Field(..., description="Unique identifier for the resume")
    candidate_name: Optional[str] = Field(None, description="Candidate's name")
    match_score: float = Field(..., description="Overall match score (0-100)")
    skill_match_score: float = Field(..., description="Skill match score (0-100)")
    experience_match_score: float = Field(..., description="Experience match score (0-100)")
    role_match_score: float = Field(..., description="Role similarity score (0-100)")
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match JD requirements")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills not found in resume")
    skill_gaps: List[SkillGap] = Field(default_factory=list, description="Skill improvement recommendations")
    recommendation: str = Field(..., description="Overall hiring recommendation")


class MatchRequest(BaseModel):
    """Request model for match endpoint."""
    
    jd_text: str = Field(..., description="Job description text")
    resume_files: List[str] = Field(..., description="List of resume file paths")


class MatchResponse(BaseModel):
    """Response model for match endpoint."""
    
    matches: List[MatchResult] = Field(..., description="List of match results")
    total_resumes: int = Field(..., description="Total number of resumes processed")
    high_matches: int = Field(0, description="Number of matches >= 80%")
    potential_matches: int = Field(0, description="Number of matches between 65-79%")
