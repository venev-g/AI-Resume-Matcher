import asyncio
import os
import time
import aiohttp
import json
from typing import Optional, Dict, Any, List
from google import genai
from dotenv import load_dotenv
import logging

from app.core.config import settings
from app.utils.exceptions import LLMServiceError

logger = logging.getLogger(__name__)
load_dotenv()


class LLMService:
    """
    Advanced LLM service supporting multiple providers with async operations
    Supports Gemini 2.5 Flash and OpenRouter (GPT-OSS 20B) models
    """

    def __init__(self):
        self.gemini_client = None
        self.openrouter_session = None
        self.default_provider = settings.DEFAULT_LLM_PROVIDER

        # Model configurations
        self.gemini_model = "gemini-2.5-flash"  # Latest stable version
        self.openrouter_model = "openai/gpt-oss-20b:free"  # GPT-OSS 20B model

        # Initialize clients
        self._initialize_gemini()
        self._initialize_openrouter_session()

    def _initialize_gemini(self):
        """Initialize Gemini client with the new Google GenAI SDK"""
        try:
            if settings.GEMINI_API_KEY:
                # Configure the new Google GenAI SDK
                # genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Gemini client initialized successfully")
            else:
                logger.warning("Gemini API key not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None

    def _initialize_openrouter_session(self):
        """Initialize OpenRouter HTTP session for async requests"""
        try:
            if settings.OPENROUTER_API_KEY:
                # OpenRouter session will be created per request to avoid connection issues
                logger.info("OpenRouter configuration ready")
            else:
                logger.warning("OpenRouter API key not provided")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter session: {e}")

    async def call_llm(
        self,
        prompt: str,
        provider: Optional[str] = None,
        max_retries: int = 3,
        delay: int = 2,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs,
    ) -> str:
        """
        Call LLM with retry logic and fallback providers

        Args:
            prompt: The input prompt
            provider: LLM provider ('gemini' or 'openrouter')
            max_retries: Maximum retry attempts
            delay: Initial delay between retries
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            **kwargs: Additional model-specific parameters

        Returns:
            str: Generated response text
        """
        provider = provider or self.default_provider

        if provider == "gemini" and self.gemini_client:
            return await self._call_gemini(
                prompt, max_retries, delay, temperature, max_tokens, **kwargs
            )
        elif provider == "openrouter" and settings.OPENROUTER_API_KEY:
            return await self._call_openrouter(
                prompt, max_retries, delay, temperature, max_tokens, **kwargs
            )
        else:
            raise LLMServiceError(
                f"Provider {provider} not available or not configured"
            )

    async def _call_gemini(
        self,
        prompt: str,
        max_retries: int,
        delay: int,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Call Gemini API with the new Google GenAI SDK"""

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")

                # Use the new Google GenAI SDK
                from google.generativeai import types

                # Configure generation parameters
                config = types.GenerationConfigDict(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=kwargs.get("top_p", 0.9),
                    top_k=kwargs.get("top_k", 40),
                    stop_sequences=kwargs.get("stop_sequences", []),
                )

                # Generate content
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model, contents=prompt, config=config
                )

                # Extract text from response
                if response and hasattr(response, "text") and response.text:
                    logger.info("Gemini API call successful")
                    return response.text.strip()
                elif (
                    response and hasattr(response, "candidates") and response.candidates
                ):
                    # Handle different response structures
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content:
                        text_content = ""
                        # Safely iterate over parts - check if parts exists and is not None
                        if (
                            hasattr(candidate.content, "parts")
                            and candidate.content.parts
                        ):
                            for part in candidate.content.parts:
                                if part and hasattr(part, "text") and part.text:
                                    text_content += part.text
                        if text_content:
                            logger.info("Gemini API call successful")
                            return text_content.strip()

                raise LLMServiceError("Empty or invalid response from Gemini API")

            except Exception as e:
                logger.error(
                    f"Gemini API error on attempt {attempt + 1}: {type(e).__name__} - {e}"
                )

                if attempt == max_retries - 1:
                    raise LLMServiceError(
                        f"All Gemini API retry attempts failed: {str(e)}"
                    )

                # Exponential backoff
                await asyncio.sleep(delay)
                delay *= 2

    async def _call_openrouter(
        self,
        prompt: str,
        max_retries: int,
        delay: int,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> str:
        """Call OpenRouter API with GPT-OSS 20B model"""

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": kwargs.get("http_referer", "http://localhost:8000"),
            "X-Title": kwargs.get("x_title", "Resume-JD Matching System"),
        }

        payload = {
            "model": self.openrouter_model,
            "messages": [
                {
                    "role": "system",
                    "content": kwargs.get(
                        "system_message",
                        "You are a helpful AI assistant specialized in resume and job description analysis.",
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "stream": False,
        }

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Calling OpenRouter API (attempt {attempt + 1}/{max_retries})"
                )

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120),  # 2 minute timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if (
                                    "message" in choice
                                    and "content" in choice["message"]
                                ):
                                    content = choice["message"]["content"]
                                    if content and content.strip():
                                        logger.info("OpenRouter API call successful")
                                        return content.strip()

                            raise LLMServiceError(
                                "Empty or invalid response from OpenRouter API"
                            )

                        else:
                            error_text = await response.text()
                            logger.error(
                                f"OpenRouter API error {response.status}: {error_text}"
                            )

                            if response.status == 429:  # Rate limit
                                await asyncio.sleep(
                                    delay * 2
                                )  # Longer wait for rate limits
                                continue
                            elif response.status >= 500:  # Server error, retry
                                await asyncio.sleep(delay)
                                continue
                            else:  # Client error, don't retry
                                raise LLMServiceError(
                                    f"OpenRouter API error {response.status}: {error_text}"
                                )

            except asyncio.TimeoutError:
                logger.error(f"OpenRouter API timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise LLMServiceError("OpenRouter API timeout after all retries")
            except aiohttp.ClientError as e:
                logger.error(
                    f"OpenRouter API client error on attempt {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    raise LLMServiceError(f"OpenRouter API client error: {str(e)}")
            except Exception as e:
                logger.error(
                    f"OpenRouter API error on attempt {attempt + 1}: {type(e).__name__} - {e}"
                )
                if attempt == max_retries - 1:
                    raise LLMServiceError(
                        f"All OpenRouter API retry attempts failed: {str(e)}"
                    )

            # Exponential backoff
            await asyncio.sleep(delay)
            delay *= 2

    def is_available(self, provider: Optional[str] = None) -> bool:
        """Check if LLM service is available"""
        provider = provider or self.default_provider

        if provider == "gemini":
            return self.gemini_client is not None and bool(settings.GEMINI_API_KEY)
        elif provider == "openrouter":
            return bool(settings.OPENROUTER_API_KEY)

        return False

    async def get_available_models(
        self, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available models for a provider"""
        provider = provider or self.default_provider

        if provider == "gemini":
            return [
                {
                    "id": "gemini-2.5-flash",
                    "name": "Gemini 2.5 Flash",
                    "description": "Our best model in terms of price-performance, offering well-rounded capabilities",
                    "context_window": 1048576,  # 1M tokens
                    "max_output_tokens": 8192,
                },
                {
                    "id": "gemini-2.0-flash-exp",
                    "name": "Gemini 2.0 Flash (Experimental)",
                    "description": "Experimental version with latest features",
                    "context_window": 1048576,
                    "max_output_tokens": 8192,
                },
            ]
        elif provider == "openrouter":
            return [
                {
                    "id": "openai/gpt-oss-20b:free",
                    "name": "GPT-OSS 20B",
                    "description": "Open-source 20B parameter model by OpenAI",
                    "context_window": 128000,  # 128k tokens
                    "max_output_tokens": 4096,
                },
                {
                    "id": "openai/gpt-oss-120b",
                    "name": "GPT-OSS 120B",
                    "description": "Open-source 120B parameter model by OpenAI",
                    "context_window": 128000,
                    "max_output_tokens": 4096,
                },
            ]

        return []

    async def test_connection(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to LLM provider"""
        provider = provider or self.default_provider
        test_prompt = "Hello! Please respond with 'Connection test successful.'"

        try:
            start_time = time.time()
            response = await self.call_llm(
                prompt=test_prompt,
                provider=provider,
                max_retries=1,
                temperature=0.1,
                max_tokens=50,
            )
            end_time = time.time()

            return {
                "provider": provider,
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "response": response[:100] + "..." if len(response) > 100 else response,
            }

        except Exception as e:
            return {
                "provider": provider,
                "status": "error",
                "error": str(e),
                "response_time": None,
                "response": None,
            }

    async def batch_call(
        self,
        prompts: List[str],
        provider: Optional[str] = None,
        max_concurrent: int = 5,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Process multiple prompts concurrently"""
        provider = provider or self.default_provider

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_prompt(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    start_time = time.time()
                    response = await self.call_llm(
                        prompt=prompt, provider=provider, **kwargs
                    )
                    end_time = time.time()

                    return {
                        "index": index,
                        "status": "success",
                        "response": response,
                        "processing_time": round(end_time - start_time, 2),
                    }
                except Exception as e:
                    return {
                        "index": index,
                        "status": "error",
                        "error": str(e),
                        "processing_time": None,
                    }

        # Process all prompts concurrently
        tasks = [process_prompt(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)

        # Sort results by index to maintain order
        return sorted(results, key=lambda x: x["index"])

    async def stream_response(
        self, prompt: str, provider: Optional[str] = None, **kwargs
    ):
        """Stream response from LLM (generator function)"""
        # Note: Streaming is more complex to implement and depends on the specific use case
        # This is a placeholder for future streaming implementation
        provider = provider or self.default_provider

        if provider == "openrouter":
            # OpenRouter supports streaming
            kwargs["stream"] = True
            # Implementation would require handling SSE (Server-Sent Events)
            # For now, fall back to regular call
            response = await self.call_llm(prompt=prompt, provider=provider, **kwargs)
            yield response
        else:
            # For providers that don't support streaming, return full response
            response = await self.call_llm(prompt=prompt, provider=provider, **kwargs)
            yield response

    def get_model_info(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the current model configuration"""
        provider = provider or self.default_provider

        if provider == "gemini":
            return {
                "provider": "gemini",
                "model": self.gemini_model,
                "client_available": self.gemini_client is not None,
                "api_key_configured": bool(settings.GEMINI_API_KEY),
                "features": [
                    "Multimodal (text, images, video, audio)",
                    "Function calling",
                    "Large context window (1M tokens)",
                    "High-quality reasoning",
                ],
            }
        elif provider == "openrouter":
            return {
                "provider": "openrouter",
                "model": self.openrouter_model,
                "client_available": bool(settings.OPENROUTER_API_KEY),
                "api_key_configured": bool(settings.OPENROUTER_API_KEY),
                "features": [
                    "Open-source model",
                    "Cost-effective",
                    "Good reasoning capabilities",
                    "Apache 2.0 licensed",
                ],
            }

        return {"error": f"Provider {provider} not supported"}

    async def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 characters ≈ 1 token for English)"""
        return len(text) // 4

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.openrouter_session and not self.openrouter_session.closed:
                await self.openrouter_session.close()
            logger.info("LLM service cleanup completed")
        except Exception as e:
            logger.error(f"Error during LLM service cleanup: {e}")


# Global LLM service instance
llm_service = LLMService()


# Utility functions for easy access
async def call_gemini(prompt: str, **kwargs) -> str:
    """Quick access to Gemini API"""
    return await llm_service.call_llm(prompt=prompt, provider="gemini", **kwargs)


async def call_openrouter(prompt: str, **kwargs) -> str:
    """Quick access to OpenRouter API"""
    return await llm_service.call_llm(prompt=prompt, provider="openrouter", **kwargs)


async def test_all_providers() -> Dict[str, Any]:
    """Test all available providers"""
    results = {}

    if llm_service.is_available("gemini"):
        results["gemini"] = await llm_service.test_connection("gemini")

    if llm_service.is_available("openrouter"):
        results["openrouter"] = await llm_service.test_connection("openrouter")

    return results
