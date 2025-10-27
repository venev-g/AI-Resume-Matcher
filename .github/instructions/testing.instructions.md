---
applyTo: "{backend/tests/**/*.py,frontend/**/*.test.{tsx,ts}}"
---

# Testing Instructions

## Backend Testing (pytest)

### Setup
```python
# conftest.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_gemini_client():
    client = Mock()
    client.generate = AsyncMock(return_value="mocked response")
    return client

@pytest.fixture
def sample_jd_data():
    return {
        "job_title": "Senior Python Developer",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience_years": 5
    }
```

### Agent Testing
```python
import pytest
from agents.jd_extractor import JDExtractorAgent

@pytest.mark.asyncio
async def test_jd_extraction(mock_gemini_client, sample_jd_data):
    agent = JDExtractorAgent()
    agent.client = mock_gemini_client
    
    result = await agent.extract("Sample JD text")
    
    assert "job_title" in result
    assert isinstance(result["required_skills"], list)
    mock_gemini_client.generate.assert_called_once()
```

### Service Testing
```python
@pytest.mark.asyncio
async def test_pinecone_upsert(monkeypatch):
    # Mock Pinecone client
    mock_index = Mock()
    
    service = PineconeService()
    service.index = mock_index
    
    await service.upsert_resume("test-id", [0.1] * 768, {"name": "Test"})
    
    mock_index.upsert.assert_called_once()
```

### API Testing
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_match_endpoint(tmp_path):
    # Create test PDF
    pdf_file = tmp_path / "resume.pdf"
    pdf_file.write_bytes(b"PDF content")
    
    with open(pdf_file, "rb") as f:
        response = client.post(
            "/api/match",
            data={"jd_text": "Test JD"},
            files={"resumes": f}
        )
    
    assert response.status_code == 200
```

## Frontend Testing (Jest + React Testing Library)

### Component Testing
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import UploadSection from '@/components/UploadSection';

describe('UploadSection', () => {
  it('renders upload form', () => {
    const mockSubmit = jest.fn();
    render(<UploadSection onSubmit={mockSubmit} loading={false} />);
    
    expect(screen.getByText(/Job Description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Match Resumes/i })).toBeInTheDocument();
  });
  
  it('handles file upload', () => {
    const mockSubmit = jest.fn();
    render(<UploadSection onSubmit={mockSubmit} loading={false} />);
    
    const file = new File(['resume'], 'resume.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/Upload Resumes/i);
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByText(/1 file\\(s\\) selected/i)).toBeInTheDocument();
  });
});
```

### API Mocking
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.post('http://localhost:8000/api/match', (req, res, ctx) => {
    return res(ctx.json({
      matches: [],
      total_resumes: 0,
      high_matches: 0,
      potential_matches: 0
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Coverage Requirements
- Aim for **80%+ coverage** overall
- **100% coverage** for critical paths (scoring algorithm)
- **All error scenarios** should have tests
- Mock **external services** (don't hit real APIs in tests)

## Running Tests
```bash
# Backend
cd backend
pytest --cov=. --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```