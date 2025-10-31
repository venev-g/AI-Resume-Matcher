import sys
import asyncio
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.llm_service import llm_service

async def test_llm():
    try:
        # Test Gemini
        if llm_service.is_available("gemini"):
            result = await llm_service.test_connection("gemini")
            print(f"Gemini: {result['status']}")
        
        # Test OpenRouter
        if llm_service.is_available("openrouter"):
            result = await llm_service.test_connection("openrouter")
            print(f"OpenRouter: {result['status']}")
            
    except Exception as e:
        print(f"LLM test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())