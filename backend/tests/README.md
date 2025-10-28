# Backend Testing Documentation

## Overview
Comprehensive test suite for the AI Resume Matcher backend covering all agents, services, orchestration, and API endpoints.

## Test Structure

```
backend/tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Shared fixtures and test configuration
├── test_jd_extractor.py          # JD Extraction Agent tests (10 tests)
├── test_resume_analyzer.py       # Resume Analysis Agent tests (11 tests)
├── test_embedding_agent.py       # Embedding Generation Agent tests (13 tests)
├── test_match_evaluator.py       # Match Evaluation Agent tests (15 tests)
├── test_skill_recommender.py     # Skill Recommendation Agent tests (13 tests)
├── test_pinecone_service.py      # Pinecone Vector DB tests (18 tests)
├── test_mongodb_service.py       # MongoDB Persistence tests (8 tests)
├── test_graph_executor.py        # LangGraph Orchestrator tests (15 tests)
├── test_api.py                   # FastAPI Endpoint tests (20 tests)
└── test_integration.py           # End-to-End Integration tests (12 tests)
```

**Total: 135+ test methods**

## Running Tests

### Run All Tests
```bash
cd backend
python run_tests.py
```

### Run Specific Test Suite
```bash
# Agent tests
python run_tests.py jd_extractor
python run_tests.py resume_analyzer
python run_tests.py embedding_agent
python run_tests.py match_evaluator
python run_tests.py skill_recommender

# Service tests
python run_tests.py pinecone_service
python run_tests.py mongodb_service

# Orchestration tests
python run_tests.py graph_executor

# API tests
python run_tests.py api

# Integration tests
python run_tests.py integration
```

### Run with pytest Directly
```bash
# All tests with coverage
pytest tests/ -v --cov=. --cov-report=html

# Specific file
pytest tests/test_match_evaluator.py -v

# Specific test method
pytest tests/test_match_evaluator.py::TestMatchEvaluator::test_weighted_scoring_formula -v

# Run with output (useful for debugging)
pytest tests/ -v -s

# Stop after first failure
pytest tests/ -x

# Show slowest tests
pytest tests/ --durations=10
```

## Test Coverage

### Agent Layer (62 tests)
- **JD Extractor (10 tests)**: Extraction success, retry logic, JSON parsing, validation, error handling
- **Resume Analyzer (11 tests)**: PDF parsing, batch processing, truncation, ID generation, file handling
- **Embedding Agent (13 tests)**: JD/resume/text embedding, truncation, batching, dimension validation, API errors
- **Match Evaluator (15 tests)**: Skill matching (perfect/partial/case-insensitive), experience matching, role similarity, weighted scoring
- **Skill Recommender (13 tests)**: Recommendations for 65-79% matches, skip logic, markdown handling, batch processing

### Service Layer (26 tests)
- **Pinecone Service (18 tests)**: Upsert (single/batch), query with filters, search by JD, metadata truncation, stats, error handling
- **MongoDB Service (8 tests)**: Connect, store results, get history with pagination, statistics, connection management

### Orchestration Layer (15 tests)
- **Graph Executor (15 tests)**: Upload workflow, database search, resume storage, node sequencing, error propagation, state management

### API Layer (20 tests)
- **FastAPI Endpoints (20 tests)**: Match endpoint, search endpoint, storage endpoint, validation, error handling, CORS, documentation

### Integration Layer (12 tests)
- **End-to-End (12 tests)**: Complete workflows, data flow consistency, threshold filtering, skill recommendation logic, persistence, error recovery, batch performance

## Test Fixtures

### Data Fixtures (conftest.py)
- `sample_jd_data`: Complete job description structure
- `sample_resume_data`: Resume with all fields
- `sample_high_match_resume`: 85%+ matching resume
- `sample_low_match_resume`: <65% matching resume
- `sample_potential_match_resume`: 65-79% matching resume
- `sample_embedding`: 768-dimensional vector
- `sample_pdf_path`: Temporary PDF file generator

### Mock Fixtures (conftest.py)
- `mock_gemini_client`: Mocked Google Gemini client
- `mock_openrouter_client`: Mocked OpenRouter client
- `mock_pinecone_index`: Mocked Pinecone index
- `mock_mongodb_collection`: Mocked MongoDB collection

### Environment Fixtures
- `setup_env_vars`: Auto-configured environment variables (autouse)

## Key Testing Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation(mock_client):
    result = await agent.process_data()
    assert result is not None
```

### Mocking External APIs
```python
@pytest.fixture
def mock_gemini_client():
    client = Mock()
    client.models.generate_content = Mock(return_value=mock_response)
    return client
```

### Testing Error Handling
```python
@pytest.mark.asyncio
async def test_api_error_handling(mock_client):
    mock_client.generate = AsyncMock(side_effect=Exception("API Error"))
    result = await agent.extract(text)
    assert result is None  # Graceful failure
```

### Testing Batch Processing
```python
@pytest.mark.asyncio
async def test_batch_processing(agent, sample_data):
    results = await agent.process_batch([sample_data] * 10)
    assert len(results) == 10
```

## Coverage Requirements

- **Minimum Coverage**: 80% overall
- **Critical Paths**: 100% (scoring algorithm, threshold filtering)
- **Error Scenarios**: All error paths tested
- **External Services**: All mocked (no real API calls)

## Coverage Report

After running tests, open the HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Continuous Integration

### Pre-commit Testing
```bash
# Run before committing
python run_tests.py

# Quick smoke test (fast tests only)
pytest tests/ -m "not slow" -v
```

### CI Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    cd backend
    pip install -r requirements.txt
    python run_tests.py
```

## Debugging Failed Tests

### View Detailed Output
```bash
pytest tests/test_name.py -v -s --tb=long
```

### Run Single Test
```bash
pytest tests/test_api.py::TestMainAPI::test_match_resumes_success -v -s
```

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use pytest Breakpoints
```python
def test_something():
    result = function()
    import pdb; pdb.set_trace()  # Debugger breakpoint
    assert result == expected
```

## Test Data

### Sample JD
- Job Title: "Senior Python Developer"
- Required Skills: ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
- Experience: 5 years
- Education: "Bachelor's degree"

### Sample Resumes
- **High Match (85%+)**: Strong Python developer with FastAPI and cloud experience
- **Potential Match (65-79%)**: Python developer missing some key skills
- **Low Match (<65%)**: Developer with different tech stack

## Common Issues

### Import Errors
```bash
# Ensure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Warnings
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Coverage Not Generating
```bash
# Install coverage packages
pip install pytest-cov coverage
```

## Best Practices

1. **Mock External Services**: Never hit real APIs (Gemini, OpenRouter, Pinecone, MongoDB)
2. **Use Fixtures**: Reuse test data via conftest.py fixtures
3. **Test Edge Cases**: Empty inputs, invalid data, API failures
4. **Async Patterns**: Use `@pytest.mark.asyncio` for async tests
5. **Clear Test Names**: Descriptive names like `test_extract_jd_data_with_retry`
6. **Assertions**: Multiple assertions per test for comprehensive validation
7. **Cleanup**: Use fixtures with proper teardown
8. **Isolation**: Tests should not depend on each other

## Future Enhancements

- [ ] Performance benchmarking tests
- [ ] Load testing for API endpoints
- [ ] Frontend integration tests (Playwright/Cypress)
- [ ] Security testing (input validation, injection attacks)
- [ ] Stress testing for large PDF files
- [ ] Mock LLM response variation testing
- [ ] Embedding similarity accuracy tests

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests pass: `python run_tests.py`
3. Maintain 80%+ coverage
4. Update this documentation
5. Add fixtures to conftest.py if needed

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [LangGraph Testing Guide](https://python.langchain.com/docs/langgraph/)
