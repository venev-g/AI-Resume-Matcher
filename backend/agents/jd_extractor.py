"""Job Description Extractor Agent using Gemini 2.5 Flash."""

import json
import logging
import os
import re
from typing import Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class JDExtractorAgent:
    """Agent for extracting structured data from job descriptions."""

    def __init__(self):
        """Initialize Gemini client for JD extraction."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.max_retries = 3

    def _strip_markdown_json(self, text: str) -> str:
        """
        Strip markdown code block formatting from JSON responses.
        
        Args:
            text: Raw response text that may contain markdown
            
        Returns:
            Clean JSON string
        """
        # Remove markdown code blocks
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        return text

    async def extract_jd_data(self, jd_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from job description text.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Dictionary containing extracted job data or None on failure
            
        Raises:
            ValueError: If jd_text is empty
        """
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description text cannot be empty")
        
        prompt = f"""
You are an expert job description analyzer. Extract the following information from the job description and return it as a valid JSON object.

Job Description:
{jd_text}

Extract:
1. job_title: The job title/position name
2. required_skills: List of technical and soft skills required
3. experience_years: Minimum years of experience required (as a number, e.g., 3.0, 5.0)
4. qualifications: Educational and professional qualifications required
5. responsibilities: Key job responsibilities and duties

Return ONLY a valid JSON object with these exact keys. Do not include any markdown formatting or explanations.

Example format:
{{
  "job_title": "Senior Software Engineer",
  "required_skills": ["Python", "FastAPI", "MongoDB", "Docker"],
  "experience_years": 5.0,
  "qualifications": ["Bachelor's degree in Computer Science", "Strong problem-solving skills"],
  "responsibilities": ["Design and develop backend systems", "Collaborate with cross-functional teams"]
}}
"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Extracting JD data (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.model.generate_content(prompt)
                
                if not response or not response.text:
                    logger.warning(f"Empty response from Gemini on attempt {attempt + 1}")
                    continue
                
                # Strip markdown formatting
                clean_text = self._strip_markdown_json(response.text)
                
                # Parse JSON response
                jd_data = json.loads(clean_text)
                
                # Validate required fields
                required_fields = [
                    "job_title", "required_skills", "experience_years",
                    "qualifications", "responsibilities"
                ]
                
                if not all(field in jd_data for field in required_fields):
                    logger.warning(f"Missing required fields in response: {jd_data.keys()}")
                    continue
                
                # Ensure lists are actually lists
                for list_field in ["required_skills", "qualifications", "responsibilities"]:
                    if not isinstance(jd_data[list_field], list):
                        jd_data[list_field] = []
                
                # Ensure experience_years is a float
                try:
                    jd_data["experience_years"] = float(jd_data["experience_years"])
                except (ValueError, TypeError):
                    jd_data["experience_years"] = 0.0
                
                logger.info(f"Successfully extracted JD data: {jd_data['job_title']}")
                return jd_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on attempt {attempt + 1}: {e}")
                logger.error(f"Response text: {response.text if response else 'No response'}")
                
            except Exception as e:
                logger.error(f"Error extracting JD data on attempt {attempt + 1}: {e}")
        
        # Return default structure if all attempts fail
        logger.error("All attempts to extract JD data failed, returning default structure")
        return {
            "job_title": "Unknown Position",
            "required_skills": [],
            "experience_years": 0.0,
            "qualifications": [],
            "responsibilities": []
        }

    async def validate_jd_data(self, jd_data: Dict[str, Any]) -> bool:
        """
        Validate extracted JD data structure.
        
        Args:
            jd_data: Extracted job description data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = [
                "job_title", "required_skills", "experience_years",
                "qualifications", "responsibilities"
            ]
            
            # Check all required fields exist
            if not all(field in jd_data for field in required_fields):
                return False
            
            # Validate types
            if not isinstance(jd_data["job_title"], str):
                return False
            
            if not isinstance(jd_data["required_skills"], list):
                return False
            
            if not isinstance(jd_data["experience_years"], (int, float)):
                return False
            
            if not isinstance(jd_data["qualifications"], list):
                return False
            
            if not isinstance(jd_data["responsibilities"], list):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating JD data: {e}")
            return False
