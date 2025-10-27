"""Skill Recommender Agent using Gemini 2.5 Flash."""

import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, List
from google import genai

logger = logging.getLogger(__name__)


class SkillRecommenderAgent:
    """Agent for generating skill gap recommendations."""

    def __init__(self):
        """Initialize Gemini client for skill recommendations."""
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)
        self.model_name = "gemini-2.5-flash"
        self.max_retries = 3
        self.max_recommendations = 5

    def _initialize_client(self):
        """Setup Gemini client with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        return genai.Client(api_key=api_key)

    def _strip_markdown_json(self, text: str) -> str:
        """
        Strip markdown code block formatting from JSON responses.
        
        Args:
            text: Raw response text that may contain markdown
            
        Returns:
            Clean JSON string
        """
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        return text

    async def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response text
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                if response and response.text:
                    return response.text
                else:
                    self.logger.warning(f"Empty response from Gemini on attempt {attempt + 1}")
                    
            except Exception as e:
                if "rate" in str(e).lower() or "quota" in str(e).lower():
                    # Exponential backoff for rate limit errors
                    await asyncio.sleep(2 ** attempt)
                    self.logger.warning(f"Rate limit hit, retry {attempt + 1}/{self.max_retries}")
                else:
                    if attempt == self.max_retries - 1:
                        self.logger.error(f"All retry attempts failed: {e}")
                        raise
                    self.logger.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
        
        raise Exception("All retry attempts exhausted")

    async def recommend_skills(
        self,
        missing_skills: List[str],
        jd_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        match_score: float
    ) -> List[Dict[str, Any]]:
        """
        Generate skill improvement recommendations.
        
        Only activates for match scores between 65-79%.
        
        Args:
            missing_skills: List of skills missing from resume
            jd_data: Job description data
            resume_data: Resume data
            match_score: Overall match score
            
        Returns:
            List of skill gap recommendations
        """
        # Only recommend for potential candidates (65-79%)
        if match_score < 65 or match_score >= 80:
            logger.info(f"Skipping recommendations for match score: {match_score}%")
            return []
        
        if not missing_skills:
            logger.info("No missing skills to recommend")
            return []
        
        prompt = f"""
You are an expert career advisor. A candidate is being considered for a position but has some skill gaps.

Job Title: {jd_data.get('job_title', 'Unknown')}
Required Skills: {', '.join(jd_data.get('required_skills', []))}
Candidate's Current Skills: {', '.join(resume_data.get('skills', []))}
Missing Skills: {', '.join(missing_skills)}
Current Match Score: {match_score}%

Provide actionable recommendations for the TOP {self.max_recommendations} most important missing skills that would help the candidate reach an 80%+ match.

For each skill, provide:
1. missing_skill: The skill name
2. importance: "high", "medium", or "low"
3. reason: Why this skill is important for the role (1-2 sentences)
4. learning_path: Specific resources or approach to learn this skill (courses, certifications, practice projects)
5. estimated_time: Realistic time estimate to acquire the skill (e.g., "2-3 months", "6-8 weeks")

Return ONLY a valid JSON array with these recommendations. Do not include markdown formatting or explanations.

Example format:
[
  {{
    "missing_skill": "Docker",
    "importance": "high",
    "reason": "Containerization is essential for modern DevOps practices and deployment workflows.",
    "learning_path": "Complete Docker Mastery course on Udemy, practice with hands-on projects deploying microservices, obtain Docker Certified Associate certification",
    "estimated_time": "2-3 months"
  }}
]
"""
        
        try:
            self.logger.info("Generating skill recommendations")
            
            # Call LLM with retry logic
            response_text = await self._call_llm_with_retry(prompt)
            
            # Strip markdown formatting
            clean_text = self._strip_markdown_json(response_text)
            
            # Parse JSON response
            recommendations = json.loads(clean_text)
            
            if not isinstance(recommendations, list):
                self.logger.warning("Response is not a list")
                return []
            
            # Validate and filter recommendations
            valid_recommendations = []
            
            for rec in recommendations[:self.max_recommendations]:
                required_fields = [
                    "missing_skill", "importance", "reason",
                    "learning_path", "estimated_time"
                ]
                
                if all(field in rec for field in required_fields):
                    # Validate importance level
                    if rec["importance"] not in ["high", "medium", "low"]:
                        rec["importance"] = "medium"
                    
                    valid_recommendations.append(rec)
            
            if valid_recommendations:
                self.logger.info(f"Generated {len(valid_recommendations)} skill recommendations")
                return valid_recommendations
            else:
                self.logger.warning("No valid recommendations generated")
                return []
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.error(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []

    async def recommend_batch(
        self,
        match_results: List[Dict[str, Any]],
        jd_data: Dict[str, Any],
        resume_data_dict: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for multiple match results.
        
        Args:
            match_results: List of match evaluation results
            jd_data: Job description data
            resume_data_dict: Dictionary mapping resume_id to resume_data
            
        Returns:
            Updated match results with skill_gaps field
        """
        updated_results = []
        
        for result in match_results:
            resume_id = result.get("resume_id")
            match_score = result.get("match_score", 0)
            missing_skills = result.get("missing_skills", [])
            
            # Get corresponding resume data
            resume_data = resume_data_dict.get(resume_id, {})
            
            # Generate recommendations if applicable
            if 65 <= match_score < 80 and missing_skills:
                logger.info(f"Generating recommendations for {result.get('candidate_name', 'Unknown')}")
                
                recommendations = await self.recommend_skills(
                    missing_skills,
                    jd_data,
                    resume_data,
                    match_score
                )
                
                result["skill_gaps"] = recommendations
            else:
                result["skill_gaps"] = []
            
            updated_results.append(result)
        
        return updated_results

    def format_recommendations_text(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Format recommendations as human-readable text.
        
        Args:
            recommendations: List of skill gap recommendations
            
        Returns:
            Formatted text string
        """
        if not recommendations:
            return "No specific skill recommendations at this time."
        
        text_parts = ["Recommended Skills to Improve:\n"]
        
        for idx, rec in enumerate(recommendations, 1):
            text_parts.append(f"\n{idx}. {rec['missing_skill']} (Importance: {rec['importance'].upper()})")
            text_parts.append(f"   Reason: {rec['reason']}")
            text_parts.append(f"   Learning Path: {rec['learning_path']}")
            text_parts.append(f"   Estimated Time: {rec['estimated_time']}")
        
        return "\n".join(text_parts)
