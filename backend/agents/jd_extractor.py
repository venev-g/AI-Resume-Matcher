"""Job Description Extractor Agent using Gemini 2.5 Flash."""

import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, Optional
from google import genai

logger = logging.getLogger(__name__)


class JDExtractorAgent:
    """Agent for extracting structured data from job descriptions."""

    def __init__(self):
        """Initialize Gemini client for JD extraction."""
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3

    def _initialize_client(self):
        """Setup Gemini client with API key from environment."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        client = genai.Client(api_key=self.api_key)
        return client

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

    async def _call_llm_with_retry(self, prompt: str) -> Optional[str]:
        """
        Call LLM with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response text or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
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
        
        return None

    async def extract_jd_data(self, jd_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from job description text.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Dictionary containing extracted job data with defaults on failure
            
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
        
        try:
            self.logger.info("Extracting JD data with retry logic")
            
            # Call LLM with retry logic
            response_text = await self._call_llm_with_retry(prompt)
            
            if not response_text:
                self.logger.error("Failed to get response from LLM after all retries")
                return self._get_default_jd_structure()
            
            # Strip markdown formatting
            clean_text = self._strip_markdown_json(response_text)
            
            # Parse JSON response
            jd_data = json.loads(clean_text)
            
            # Validate and sanitize data
            jd_data = self._validate_and_sanitize_jd_data(jd_data)
            
            self.logger.info(f"Successfully extracted JD data: {jd_data['job_title']}")
            return jd_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.error(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
            return self._get_default_jd_structure()
            
        except Exception as e:
            self.logger.error(f"Error extracting JD data: {e}")
            return self._get_default_jd_structure()

    def _validate_and_sanitize_jd_data(self, jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize extracted JD data.
        
        Args:
            jd_data: Raw extracted data
            
        Returns:
            Validated and sanitized data
        """
        required_fields = [
            "job_title", "required_skills", "experience_years",
            "qualifications", "responsibilities"
        ]
        
        # Check all required fields exist
        if not all(field in jd_data for field in required_fields):
            self.logger.warning(f"Missing required fields in response: {jd_data.keys()}")
            return self._get_default_jd_structure()
        
        # Ensure lists are actually lists
        for list_field in ["required_skills", "qualifications", "responsibilities"]:
            if not isinstance(jd_data[list_field], list):
                jd_data[list_field] = []
        
        # Ensure experience_years is a float
        try:
            jd_data["experience_years"] = float(jd_data["experience_years"])
        except (ValueError, TypeError):
            jd_data["experience_years"] = 0.0
        
        return jd_data

    def _get_default_jd_structure(self) -> Dict[str, Any]:
        """
        Return default JD structure for malformed job descriptions.
        
        Returns:
            Default job description structure
        """
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
