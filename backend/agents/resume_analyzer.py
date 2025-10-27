"""Resume Analyzer Agent using Unstructured library and OpenRouter."""

import json
import logging
import os
import re
from typing import Dict, Any, Optional, List
from unstructured.partition.pdf import partition_pdf
from openai import OpenAI

logger = logging.getLogger(__name__)


class ResumeAnalyzerAgent:
    """Agent for parsing and analyzing resume PDFs."""

    def __init__(self):
        """Initialize PDF parser and OpenRouter client."""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key
        )
        
        self.model = "openai/gpt-4-turbo"
        self.max_retries = 3
        self.max_text_length = 4000

    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF using Unstructured library.
        
        Args:
            file_path: Path to the PDF resume file
            
        Returns:
            Extracted text or None on failure
        """
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            
            # Use hi_res strategy with OCR support
            elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                infer_table_structure=True
            )
            
            # Combine all text elements
            text = "\n".join([str(element) for element in elements])
            
            # Limit text length for LLM context
            if len(text) > self.max_text_length:
                logger.warning(f"Text exceeds max length, truncating from {len(text)} to {self.max_text_length}")
                text = text[:self.max_text_length]
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None

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

    async def analyze_resume(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse PDF resume and extract structured data.
        
        Args:
            file_path: Path to the PDF resume file
            
        Returns:
            Dictionary containing parsed resume data or None on failure
        """
        # Extract text from PDF
        resume_text = self._extract_text_from_pdf(file_path)
        
        if not resume_text:
            logger.error(f"Failed to extract text from resume: {file_path}")
            return None
        
        prompt = f"""
You are an expert resume parser. Extract the following information from the resume text and return it as a valid JSON object.

Resume Text:
{resume_text}

Extract:
1. candidate_name: Full name of the candidate
2. email: Email address (if present)
3. skills: List of all technical and professional skills mentioned
4. experience_years: Total years of professional experience (as a number, e.g., 3.0, 5.0)
5. work_history: List of work experience entries (company, role, duration)
6. education: List of educational qualifications

Return ONLY a valid JSON object with these exact keys. Do not include any markdown formatting or explanations.

Example format:
{{
  "candidate_name": "John Doe",
  "email": "john.doe@example.com",
  "skills": ["Python", "FastAPI", "MongoDB", "Docker"],
  "experience_years": 5.0,
  "work_history": ["Senior Developer at TechCorp (2020-2023)", "Developer at StartupXYZ (2018-2020)"],
  "education": ["B.S. Computer Science - MIT (2018)", "M.S. Software Engineering - Stanford (2020)"]
}}
"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Analyzing resume (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert resume parser. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                if not response.choices or not response.choices[0].message.content:
                    logger.warning(f"Empty response from OpenRouter on attempt {attempt + 1}")
                    continue
                
                content = response.choices[0].message.content
                
                # Strip markdown formatting
                clean_text = self._strip_markdown_json(content)
                
                # Parse JSON response
                resume_data = json.loads(clean_text)
                
                # Validate required fields
                required_fields = [
                    "candidate_name", "email", "skills",
                    "experience_years", "work_history", "education"
                ]
                
                if not all(field in resume_data for field in required_fields):
                    logger.warning(f"Missing required fields in response: {resume_data.keys()}")
                    continue
                
                # Ensure lists are actually lists
                for list_field in ["skills", "work_history", "education"]:
                    if not isinstance(resume_data[list_field], list):
                        resume_data[list_field] = []
                
                # Ensure experience_years is a float
                try:
                    resume_data["experience_years"] = float(resume_data["experience_years"])
                except (ValueError, TypeError):
                    resume_data["experience_years"] = 0.0
                
                logger.info(f"Successfully analyzed resume: {resume_data.get('candidate_name', 'Unknown')}")
                return resume_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on attempt {attempt + 1}: {e}")
                logger.error(f"Response content: {content if 'content' in locals() else 'No content'}")
                
            except Exception as e:
                logger.error(f"Error analyzing resume on attempt {attempt + 1}: {e}")
        
        # Return default structure if all attempts fail
        logger.error(f"All attempts to analyze resume failed: {file_path}")
        return {
            "candidate_name": None,
            "email": None,
            "skills": [],
            "experience_years": 0.0,
            "work_history": [],
            "education": []
        }

    async def analyze_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple resumes in batch.
        
        Args:
            file_paths: List of PDF resume file paths
            
        Returns:
            List of parsed resume data dictionaries
        """
        results = []
        
        for idx, file_path in enumerate(file_paths):
            logger.info(f"Processing resume {idx + 1}/{len(file_paths)}: {file_path}")
            
            resume_data = await self.analyze_resume(file_path)
            
            if resume_data:
                resume_data["resume_id"] = f"resume_{idx + 1}"
                resume_data["file_path"] = file_path
                results.append(resume_data)
            else:
                logger.warning(f"Skipping failed resume: {file_path}")
        
        logger.info(f"Successfully analyzed {len(results)}/{len(file_paths)} resumes")
        return results
