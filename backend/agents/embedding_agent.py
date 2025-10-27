"""Embedding Agent using Gemini text-embedding-004 model."""

import logging
import os
from typing import List, Dict, Any, Optional
from google import genai

logger = logging.getLogger(__name__)


class EmbeddingAgent:
    """Agent for generating contextualized embeddings using Gemini."""

    def __init__(self):
        """Initialize Gemini embedding client."""
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)
        self.model_name = "models/text-embedding-004"
        self.dimension = 768
        self.max_text_length = 10000

    def _initialize_client(self):
        """Setup Gemini client with API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        return genai.Client(api_key=api_key)

    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for embedding by truncating if necessary.
        
        Args:
            text: Input text to prepare
            
        Returns:
            Prepared text within length limits
        """
        if len(text) > self.max_text_length:
            self.logger.warning(f"Text exceeds max length, truncating from {len(text)} to {self.max_text_length}")
            return text[:self.max_text_length]
        return text

    async def embed_jd(self, jd_data: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for job description.
        
        Combines multiple JD fields into rich context for better matching.
        
        Args:
            jd_data: Extracted job description data
            
        Returns:
            768-dimensional embedding vector or None on failure
        """
        try:
            # Combine relevant fields into context-rich text
            context_parts = [
                f"Job Title: {jd_data.get('job_title', '')}",
                f"Required Skills: {', '.join(jd_data.get('required_skills', []))}",
                f"Experience Required: {jd_data.get('experience_years', 0)} years",
                f"Qualifications: {', '.join(jd_data.get('qualifications', []))}",
                f"Responsibilities: {', '.join(jd_data.get('responsibilities', []))}"
            ]
            
            combined_text = "\n".join(context_parts)
            prepared_text = self._prepare_text(combined_text)
            
            self.logger.info(f"Generating JD embedding for: {jd_data.get('job_title', 'Unknown')}")
            
            # Generate embedding
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=prepared_text
            )
            
            embedding = result.embeddings[0].values
            
            if len(embedding) != self.dimension:
                self.logger.error(f"Unexpected embedding dimension: {len(embedding)}")
                return None
            
            self.logger.info(f"Successfully generated JD embedding (dim={len(embedding)})")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating JD embedding: {e}")
            return None

    async def embed_resume(self, resume_data: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for resume.
        
        Combines multiple resume fields into rich context for better matching.
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            768-dimensional embedding vector or None on failure
        """
        try:
            # Combine relevant fields into context-rich text
            context_parts = [
                f"Candidate: {resume_data.get('candidate_name', 'Unknown')}",
                f"Skills: {', '.join(resume_data.get('skills', []))}",
                f"Experience: {resume_data.get('experience_years', 0)} years",
                f"Work History: {'; '.join(resume_data.get('work_history', []))}",
                f"Education: {'; '.join(resume_data.get('education', []))}"
            ]
            
            combined_text = "\n".join(context_parts)
            prepared_text = self._prepare_text(combined_text)
            
            self.logger.info(f"Generating resume embedding for: {resume_data.get('candidate_name', 'Unknown')}")
            
            # Generate embedding
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=prepared_text
            )
            
            embedding = result.embeddings[0].values
            
            if len(embedding) != self.dimension:
                self.logger.error(f"Unexpected embedding dimension: {len(embedding)}")
                return None
            
            self.logger.info(f"Successfully generated resume embedding (dim={len(embedding)})")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating resume embedding: {e}")
            return None

    async def embed_batch_resumes(
        self,
        resume_data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple resumes.
        
        Args:
            resume_data_list: List of parsed resume data dictionaries
            
        Returns:
            List of dictionaries with resume data and embeddings
        """
        results = []
        
        for idx, resume_data in enumerate(resume_data_list):
            self.logger.info(f"Embedding resume {idx + 1}/{len(resume_data_list)}")
            
            embedding = await self.embed_resume(resume_data)
            
            if embedding:
                results.append({
                    "resume_data": resume_data,
                    "embedding": embedding
                })
            else:
                self.logger.warning(f"Failed to generate embedding for resume: {resume_data.get('candidate_name', 'Unknown')}")
        
        self.logger.info(f"Successfully generated {len(results)}/{len(resume_data_list)} resume embeddings")
        return results

    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """
        Generate embedding for arbitrary text.
        
        Args:
            text: Text to embed
            task_type: Type of embedding task (retrieval_document or retrieval_query)
            
        Returns:
            768-dimensional embedding vector or None on failure
        """
        try:
            prepared_text = self._prepare_text(text)
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=prepared_text
            )
            
            embedding = result.embeddings[0].values
            
            if len(embedding) != self.dimension:
                self.logger.error(f"Unexpected embedding dimension: {len(embedding)}")
                return None
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating text embedding: {e}")
            return None
