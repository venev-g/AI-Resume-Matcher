---
applyTo: "backend/**/*.py"
---

# Backend Python Development Instructions

## Project Context
Building the backend for enterprise AI Resume Matcher using FastAPI, LangGraph, and multi-agent architecture.

## Key Requirements

### FastAPI Development
- Use **async def** for all route handlers
- Apply **dependency injection** for database connections
- Implement **background tasks** for long-running operations
- Use **HTTPException** for error responses with proper status codes
- Add **response_model** to all POST/GET endpoints for validation

### LangGraph Agent Implementation
- All agents inherit from base patterns defined in the blueprint
- Use **StateGraph** for workflow orchestration
- Implement **checkpointing** for resumable workflows
- Add **timeout handling** for LLM API calls (30s default)
- Use **ainvoke** for async graph execution

### LLM Integration
- **Gemini**: Use google-genai SDK, handle rate limits (60 RPM)
- **OpenRouter**: Use OpenAI SDK with custom base_url
- Implement **exponential backoff** for retries
- Parse JSON responses from LLMs with error handling
- Truncate long texts before embedding (10K chars max)

### Database Operations
- **Pinecone**: Initialize index on app startup, check existence first
- **MongoDB**: Use async motor for non-blocking I/O
- Implement **upsert** operations for resume updates
- Add **TTL indexes** for temporary data (optional)
- Use **aggregation pipelines** for complex queries

### Error Handling
```python
# Standard error handling pattern
try:
    result = await llm_client.generate(prompt)
    return parse_response(result)
except RateLimitError:
    await asyncio.sleep(60)
    return await retry_with_backoff()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Processing error")
```

### Environment Variables
Required vars in .env:
- GEMINI_API_KEY
- OPENROUTER_API_KEY
- PINECONE_API_KEY
- MONGODB_URI

Load with python-dotenv at app startup.

### Logging
Use structured logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log important operations
logger.info(f"Processing resume: {resume_id}")
logger.error(f"Failed to parse PDF: {error}", exc_info=True)
```

### Code Quality
- Run **black** for formatting
- Use **ruff** for linting
- Add **mypy** type checking
- Follow **Google docstring** format