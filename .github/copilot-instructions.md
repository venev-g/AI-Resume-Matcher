# Enterprise AI Resume Matcher - GitHub Copilot Instructions

## Project Overview
This is an enterprise-grade AI resume matching system built with LangGraph orchestration, multiple AI agents, Next.js 15 frontend, and production databases (Pinecone + MongoDB).

**Tech Stack:**
- **Backend**: Python 3.10+, FastAPI 0.119.0, LangGraph 1.0.1, CrewAI
- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **AI/LLM**: Google Gemini 2.5 (google-genai SDK), OpenRouter (GPT-4 Turbo)
- **Databases**: Pinecone (vector search), MongoDB Atlas (metadata)
- **PDF Processing**: Unstructured library with OCR support

## System Architecture
The system uses 5 specialized AI agents orchestrated by LangGraph:
1. **JD Extractor Agent** - Extracts job requirements using Gemini
2. **Resume Analyzer Agent** - Parses PDFs with Unstructured + OpenRouter
3. **Embedding Agent** - Generates Gemini embeddings (768-dim)
4. **Match Evaluator Agent** - Weighted scoring (40% skills, 30% exp, 30% role)
5. **Skill Recommender Agent** - Suggests improvements for 65-79% matches

## Code Generation Guidelines

### Python Backend (FastAPI)
- Use **async/await** for all I/O operations
- Follow **PEP 8** style guidelines with type hints
- Use **Pydantic BaseModel** for all data models
- Implement comprehensive **error handling** with try-except blocks
- Add **docstrings** (Google style) to all classes and functions
- Use **environment variables** (.env) for API keys and configs
- Import structure: stdlib → third-party → local modules
- Use **f-strings** for string formatting

Example:
```python
async def process_resume(self, file_path: str) -> Dict[str, Any]:
    \"\"\"Process resume and extract structured data.
    
    Args:
        file_path: Path to PDF resume file
        
    Returns:
        Dictionary containing parsed resume data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PDFParsingError: If PDF parsing fails
    \"\"\"
    try:
        elements = partition_pdf(filename=file_path)
        # Processing logic
        return parsed_data
    except Exception as e:
        logger.error(f"Resume processing failed: {e}")
        raise
```

### TypeScript/React Frontend (Next.js 15)
- Use **'use client'** directive for client components
- Prefer **Server Components** by default (Next.js 15)
- Use **async/await** with Server Actions for data mutations
- Apply **Tailwind CSS** classes for styling (no inline styles)
- Use **TypeScript interfaces** for all props and state
- Implement **error boundaries** for component error handling
- Use **semantic HTML** elements
- Follow **React 19** best practices (no more forwardRef needed)

Example:
```typescript
'use client';

interface UploadSectionProps {
  onSubmit: (jdText: string, files: File[]) => Promise<void>;
  loading: boolean;
}

export default function UploadSection({ onSubmit, loading }: UploadSectionProps) {
  const [jdText, setJdText] = useState('');
  // Component logic
}
```

### LangGraph Workflow
- Define **GraphState** as TypedDict with all state fields
- Use **async functions** for all node methods
- Implement **state management** with proper typing
- Add **edge conditions** for conditional workflows
- Store results in **MongoDB** for persistence
- Handle **errors gracefully** within nodes

### Agent Implementation
- Each agent should be a **separate class** in agents/ directory
- Initialize LLM clients in **__init__** method
- Use **async methods** for all agent operations
- Implement **retry logic** for API calls (max 3 attempts)
- Add **logging** for debugging and monitoring
- Return **structured data** (dict/Pydantic models)

### Database Operations
- **Pinecone**: Use serverless spec, cosine metric for embeddings
- **MongoDB**: Use async motor client where possible
- Implement **connection pooling** for database clients
- Add **indexes** for frequently queried fields
- Handle **connection errors** with reconnection logic

### API Design
- Use **FastAPI dependency injection** for shared resources
- Implement **CORS middleware** with specific origins (not *)
- Add **request validation** with Pydantic models
- Return **structured responses** with proper HTTP status codes
- Implement **rate limiting** for production
- Add **API documentation** with docstrings

## File Organization

### Backend Structure
```
backend/
├── agents/              # AI agent implementations
├── services/            # Database and external services
├── models/              # Pydantic schemas
├── utils/               # Helper functions
├── graph_executor.py    # LangGraph orchestration
├── main.py              # FastAPI application
└── requirements.txt
```

### Frontend Structure
```
frontend/
├── app/                 # Next.js app router
├── components/          # Reusable React components
├── types/               # TypeScript type definitions
├── lib/                 # Utility functions
└── public/              # Static assets
```

## Testing Guidelines
- Write **unit tests** for all agent methods
- Use **pytest** with async support for backend
- Mock **external API calls** (Gemini, OpenRouter, Pinecone)
- Test **error handling** scenarios
- Aim for **80%+ code coverage**

## Security Best Practices
- Store **API keys** in .env files (never commit)
- Validate **user input** before processing
- Implement **file upload limits** (max 10MB per file)
- Use **HTTPS** for all external API calls
- Sanitize **file paths** to prevent directory traversal
- Implement **authentication** for production deployment

## Performance Optimization
- Use **batching** for multiple embeddings
- Implement **caching** for repeated JD extractions
- Use **connection pooling** for databases
- Optimize **PDF parsing** with appropriate strategies
- Implement **lazy loading** in frontend

## Naming Conventions
- **Files**: snake_case for Python, kebab-case for React
- **Classes**: PascalCase
- **Functions/Methods**: snake_case (Python), camelCase (TypeScript)
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: prefix with underscore (_method_name)

## Documentation
- Add **README.md** for setup instructions
- Document **API endpoints** with FastAPI auto-docs
- Include **architecture diagrams** where helpful
- Write **inline comments** for complex logic
- Maintain **CHANGELOG.md** for version history

## Dependencies
Always use **latest stable versions**:
- FastAPI 0.119.0+
- LangGraph 1.0.1+
- Next.js 15+
- React 19+
- Pinecone 5.0.1+

When suggesting new dependencies, verify compatibility and security.

## Error Messages
Provide **user-friendly error messages**:
- Avoid exposing internal implementation details
- Include **actionable suggestions** for resolution
- Log **detailed errors** server-side for debugging