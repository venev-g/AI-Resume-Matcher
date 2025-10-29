import asyncio
import os
import time
from typing import Optional, Dict, Any
from google import genai
from dotenv import load_dotenv
import logging

from app.core.config import settings
from app.utils.exceptions import LLMServiceError

logger = logging.getLogger(__name__)
load_dotenv()

class LLMService:
    def __init__(self):
        self.gemini_client = None
        self.openrouter_client = None
        self.default_provider = settings.DEFAULT_LLM_PROVIDER
        
        # Initialize Gemini client
        if settings.GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        
        # Initialize OpenRouter client (placeholder for future implementation)
        if settings.OPENROUTER_API_KEY:
            # TODO: Implement OpenRouter client
            pass
    
    async def call_llm(
        self, 
        prompt: str, 
        provider: Optional[str] = None,
        max_retries: int = 3,
        delay: int = 2
    ) -> str:
        """
        Call LLM with retry logic and fallback providers
        """
        provider = provider or self.default_provider
        
        if provider == "gemini" and self.gemini_client:
            return await self._call_gemini(prompt, max_retries, delay)
        elif provider == "openrouter" and self.openrouter_client:
            return await self._call_openrouter(prompt, max_retries, delay)
        else:
            raise LLMServiceError(f"Provider {provider} not available or not configured")
    
    async def _call_gemini(self, prompt: str, max_retries: int, delay: int) -> str:
        """Call Gemini API with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt
                )
                
                if response and response.text:
                    logger.info("Gemini API call successful")
                    return response.text
                else:
                    raise LLMServiceError("Empty response from Gemini API")
                    
            except Exception as e:
                logger.error(f"Gemini API error on attempt {attempt + 1}: {type(e).__name__} - {e}")
                if attempt == max_retries - 1:
                    raise LLMServiceError(f"All Gemini API retry attempts failed: {str(e)}")
                
                # Exponential backoff
                await asyncio.sleep(delay)
                delay *= 2
    
    async def _call_openrouter(self, prompt: str, max_retries: int, delay: int) -> str:
        """Call OpenRouter API with retry logic (placeholder)"""
        # TODO: Implement OpenRouter API calls
        raise LLMServiceError("OpenRouter integration not yet implemented")
    
    def is_available(self, provider: Optional[str] = None) -> bool:
        """Check if LLM service is available"""
        provider = provider or self.default_provider
        
        if provider == "gemini":
            return self.gemini_client is not None
        elif provider == "openrouter":
            return self.openrouter_client is not None
        
        return False

# Global LLM service instance
llm_service = LLMService()
