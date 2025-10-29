from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from enum import Enum

class SkillClass(str, Enum):
    TECHNICAL = "Technical"
    NON_TECHNICAL = "Non-Technical"

class Skill(BaseModel):
    skill: str
    years_of_experience: Union[float, str]
    justification: str
    skill_class: Optional[SkillClass] = None

class SkillSet(BaseModel):
    skills: List[Skill]
    total_skills: int
    technical_skills: int
    non_technical_skills: int

class SkillGap(BaseModel):
    missing_skills: List[str]
    skill_gaps: List[Dict[str, Any]]
    recommendations: List[str]
    priority_skills: List[str]

class SkillComparison(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    match_percentage: float
    technical_match: float
    non_technical_match: float
    detailed_analysis: Dict[str, Any]
