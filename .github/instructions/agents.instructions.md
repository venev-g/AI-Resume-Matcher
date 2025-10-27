---
applyTo: "backend/agents/**/*.py"
---

# AI Agent Development Instructions

## Agent Architecture
Each agent is a specialized component in the LangGraph workflow with specific responsibilities.

## Standard Agent Pattern

```python
from typing import Dict, Any
import logging

class AgentName:
    \"\"\"Brief description of agent purpose.\"\"\"
    
    def __init__(self):
        # Initialize LLM client
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_client(self):
        # Setup with API key from env
        pass
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Main processing method.
        
        Args:
            input_data: Input dictionary with required fields
            
        Returns:
            Processed data dictionary
            
        Raises:
            AgentProcessingError: If processing fails
        \"\"\"
        try:
            # Processing logic
            result = await self._call_llm(input_data)
            return self._parse_result(result)
        except Exception as e:
            self.logger.error(f"Agent processing failed: {e}")
            raise
```

## Agent-Specific Guidelines

### JD Extractor Agent
- Extract: job_title, required_skills, experience_years, qualifications
- Use **Gemini 2.5 Flash** for fast extraction
- Return **valid JSON** only (strip markdown formatting)
- Handle **malformed JDs** gracefully with defaults

### Resume Analyzer Agent
- Use **Unstructured** library with "hi_res" strategy for PDFs
- Chunk text into **semantic sections** (experience, education, skills)
- Use **OpenRouter GPT-4 Turbo** for structuring
- Extract: candidate_name, email, skills, work_history, education
- Limit text to **4000 chars** for LLM context

### Embedding Agent
- Use **Gemini text-embedding-004** model
- Create **contextualized embeddings** (combine multiple fields)
- Truncate input to **10,000 characters**
- Return **numpy array** for consistency
- Cache embeddings for duplicate content

### Match Evaluator Agent
- Implement **weighted scoring formula**:
  - 40% skill match (intersection / required skills)
  - 30% experience match (min(resume_exp / jd_exp, 1.0))
  - 30% role similarity (cosine similarity of embeddings)
- Use **scikit-learn cosine_similarity** for embeddings
- Return scores **0-100** range (rounded to 2 decimals)
- Include matched_skills and missing_skills lists

### Skill Recommender Agent
- Activate only for **65-79% match scores**
- Use **Gemini 2.5 Flash** for recommendations
- Return structured JSON with:
  - skill_name
  - importance (high/medium/low)
  - reason (one sentence)
  - learning_path (course/certification/project)
  - estimated_time
- Limit to **top 5 recommendations**

## LLM Prompt Engineering
- Use **clear, specific instructions** in prompts
- Provide **examples** when format is critical
- Request **JSON output** explicitly
- Include **fallback instructions** for errors
- Keep prompts **under 2000 tokens** when possible

## Error Handling
```python
# Retry logic for LLM calls
async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await self.client.generate(prompt)
            return response
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            self.logger.warning(f"Retry {attempt + 1}/{max_retries}")
```

## Testing Agents
- Mock **LLM responses** in unit tests
- Test **error scenarios** (API failures, invalid input)
- Verify **output structure** matches expected schema
- Test with **real sample data** in integration tests