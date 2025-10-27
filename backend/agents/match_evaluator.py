"""Match Evaluator Agent for scoring resume-JD matches."""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class MatchEvaluatorAgent:
    """Agent for evaluating resume-job description matches using weighted scoring."""

    def __init__(self):
        """Initialize match evaluator with scoring weights."""
        self.skill_weight = 0.40
        self.experience_weight = 0.30
        self.role_weight = 0.30

    def _calculate_skill_match(
        self,
        resume_skills: List[str],
        required_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skill match score.
        
        Args:
            resume_skills: List of skills from resume
            required_skills: List of required skills from JD
            
        Returns:
            Tuple of (score, matched_skills, missing_skills)
        """
        if not required_skills:
            return 100.0, [], []
        
        # Normalize skill names for comparison (lowercase, strip whitespace)
        resume_skills_normalized = {skill.lower().strip() for skill in resume_skills}
        required_skills_normalized = {skill.lower().strip() for skill in required_skills}
        
        # Find matched and missing skills
        matched = resume_skills_normalized.intersection(required_skills_normalized)
        missing = required_skills_normalized - resume_skills_normalized
        
        # Calculate match percentage
        match_score = (len(matched) / len(required_skills_normalized)) * 100
        
        # Get original case skills for display
        matched_skills = [
            skill for skill in required_skills
            if skill.lower().strip() in matched
        ]
        
        missing_skills = [
            skill for skill in required_skills
            if skill.lower().strip() in missing
        ]
        
        return round(match_score, 2), matched_skills, missing_skills

    def _calculate_experience_match(
        self,
        resume_experience: float,
        required_experience: float
    ) -> float:
        """
        Calculate experience match score.
        
        Args:
            resume_experience: Years of experience from resume
            required_experience: Required years from JD
            
        Returns:
            Experience match score (0-100)
        """
        if required_experience == 0:
            return 100.0
        
        # Cap at 100% if resume experience meets or exceeds requirement
        experience_ratio = min(resume_experience / required_experience, 1.0)
        
        return round(experience_ratio * 100, 2)

    def _calculate_role_similarity(
        self,
        resume_embedding: List[float],
        jd_embedding: List[float]
    ) -> float:
        """
        Calculate role similarity using cosine similarity of embeddings.
        
        Args:
            resume_embedding: Resume embedding vector
            jd_embedding: JD embedding vector
            
        Returns:
            Role similarity score (0-100)
        """
        try:
            # Convert to numpy arrays
            resume_vec = np.array(resume_embedding).reshape(1, -1)
            jd_vec = np.array(jd_embedding).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(resume_vec, jd_vec)[0][0]
            
            # Normalize to 0-100 scale (cosine similarity is -1 to 1, but typically 0 to 1)
            normalized_score = max(0, min(100, (similarity + 1) * 50))
            
            return round(normalized_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating role similarity: {e}")
            return 0.0

    async def evaluate_match(
        self,
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        resume_embedding: List[float],
        jd_embedding: List[float]
    ) -> Dict[str, Any]:
        """
        Evaluate match between resume and job description.
        
        Uses weighted scoring formula:
        - 40% Skill Match
        - 30% Experience Match
        - 30% Role Similarity
        
        Args:
            resume_data: Parsed resume data
            jd_data: Extracted JD data
            resume_embedding: Resume embedding vector
            jd_embedding: JD embedding vector
            
        Returns:
            Dictionary containing match scores and details
        """
        try:
            # Calculate individual scores
            skill_score, matched_skills, missing_skills = self._calculate_skill_match(
                resume_data.get("skills", []),
                jd_data.get("required_skills", [])
            )
            
            experience_score = self._calculate_experience_match(
                resume_data.get("experience_years", 0.0),
                jd_data.get("experience_years", 0.0)
            )
            
            role_score = self._calculate_role_similarity(
                resume_embedding,
                jd_embedding
            )
            
            # Calculate weighted overall score
            overall_score = (
                skill_score * self.skill_weight +
                experience_score * self.experience_weight +
                role_score * self.role_weight
            )
            
            overall_score = round(overall_score, 2)
            
            # Generate recommendation based on score
            if overall_score >= 80:
                recommendation = "Highly recommended - Strong match across all criteria"
            elif overall_score >= 65:
                recommendation = "Potential candidate - Good match with some skill gaps"
            else:
                recommendation = "Not recommended - Significant gaps in required qualifications"
            
            logger.info(
                f"Evaluated match for {resume_data.get('candidate_name', 'Unknown')}: "
                f"{overall_score}% (Skills: {skill_score}%, Exp: {experience_score}%, Role: {role_score}%)"
            )
            
            return {
                "resume_id": resume_data.get("resume_id", "unknown"),
                "candidate_name": resume_data.get("candidate_name"),
                "match_score": overall_score,
                "skill_match_score": skill_score,
                "experience_match_score": experience_score,
                "role_match_score": role_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error evaluating match: {e}")
            return {
                "resume_id": resume_data.get("resume_id", "unknown"),
                "candidate_name": resume_data.get("candidate_name"),
                "match_score": 0.0,
                "skill_match_score": 0.0,
                "experience_match_score": 0.0,
                "role_match_score": 0.0,
                "matched_skills": [],
                "missing_skills": jd_data.get("required_skills", []),
                "recommendation": "Evaluation failed"
            }

    async def evaluate_batch(
        self,
        resume_embeddings_list: List[Dict[str, Any]],
        jd_data: Dict[str, Any],
        jd_embedding: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple resumes against a job description.
        
        Args:
            resume_embeddings_list: List of dicts with resume_data and embedding
            jd_data: Extracted JD data
            jd_embedding: JD embedding vector
            
        Returns:
            List of match evaluation results sorted by score
        """
        results = []
        
        for idx, resume_item in enumerate(resume_embeddings_list):
            logger.info(f"Evaluating match {idx + 1}/{len(resume_embeddings_list)}")
            
            result = await self.evaluate_match(
                resume_item["resume_data"],
                jd_data,
                resume_item["embedding"],
                jd_embedding
            )
            
            results.append(result)
        
        # Sort by match score (highest first)
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"Completed evaluation of {len(results)} resumes")
        return results
