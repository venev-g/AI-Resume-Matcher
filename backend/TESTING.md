# Testing Guide - AI Resume Matcher Backend

This guide explains how to test the AI Resume Matcher backend system.

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Ensure `.env` file exists with all required API keys:
     - `GEMINI_API_KEY`
     - `OPENROUTER_API_KEY`
     - `PINECONE_API_KEY`
     - `MONGODB_URI`

3. **Optional: Create Test Resumes**
   ```bash
   mkdir -p backend/test_resumes
   # Add sample PDF resumes to this directory
   ```

## Test Structure

The backend testing is divided into three levels:

### 1. Individual Agent Tests (`test_agents.py`)
Tests each of the 5 AI agents independently:
- ✅ **JD Extractor Agent** - Extracts structured data from job descriptions
- ✅ **Resume Analyzer Agent** - Parses PDF resumes (requires test PDF)
- ✅ **Embedding Agent** - Generates 768-dim vectors using Gemini
- ✅ **Match Evaluator Agent** - Calculates weighted match scores
- ✅ **Skill Recommender Agent** - Generates skill gap recommendations

**Run:**
```bash
cd backend
python test_agents.py
```

**What it tests:**
- Agent initialization with API keys
- LLM API calls (Gemini, OpenRouter)
- Error handling and retry logic
- Data validation and parsing

**Expected output:**
```
====================================================================
TEST 1: JD Extractor Agent
====================================================================
✓ Agent initialized successfully
Extracting JD data...
✓ JD Extraction successful!
  Job Title: Senior Python Developer
  Required Skills: ['Python', 'FastAPI', 'Django', ...]
  Experience Years: 5
```

### 2. LangGraph Workflow Test (`test_langgraph.py`)
Tests the complete orchestrated workflow:
- Graph executor initialization
- Sequential execution through 6 nodes
- State management between nodes
- Database operations (Pinecone, MongoDB)

**Run:**
```bash
cd backend
python test_langgraph.py
```

**What it tests:**
- LangGraph StateGraph compilation
- Node execution order (extract → analyze → embed → evaluate → recommend → finalize)
- Error propagation and handling
- Result aggregation

**Expected output:**
```
====================================================================
LANGGRAPH WORKFLOW TEST
====================================================================
1. Initializing Graph Executor...
   ✓ Executor initialized successfully
2. Executing LangGraph workflow...
   This will run through all 6 nodes:
   → Extract JD
   → Analyze Resumes
   → Generate Embeddings
   → Evaluate Matches
   → Recommend Skills
   → Finalize Output
✓ WORKFLOW COMPLETED SUCCESSFULLY!
```

### 3. FastAPI Server Tests (`test_fastapi.py`)
Tests all HTTP endpoints:
- `GET /health` - Health check
- `POST /api/match` - Match resumes to JD
- `GET /api/statistics` - System statistics
- `GET /api/history` - Match history

**Setup:**
First, start the FastAPI server in a separate terminal:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then run tests:
```bash
cd backend
python test_fastapi.py
```

**What it tests:**
- Server connectivity
- Request/response handling
- Multipart form data (file uploads)
- Database queries
- CORS configuration

**Expected output:**
```
====================================================================
TEST 1: Health Check Endpoint
====================================================================
✓ Health check successful!
  Status: healthy
  Timestamp: 2025-10-27T12:34:56
```

## Running All Tests

Use the master test runner to run all three test suites:

```bash
cd backend
python run_all_tests.py
```

This will:
1. Run agent tests sequentially
2. Execute the LangGraph workflow
3. Test FastAPI endpoints (requires server running)
4. Provide a comprehensive summary

## Test Scenarios

### Scenario 1: Quick Smoke Test (No PDFs)
Tests the system with JD only, no resume files:
```bash
python test_agents.py  # Resume Analyzer will be skipped
python test_langgraph.py  # Will process JD only
```

### Scenario 2: Full Integration Test (With PDFs)
Tests with actual resume files:
```bash
# 1. Add test resumes
mkdir -p backend/test_resumes
cp /path/to/resumes/*.pdf backend/test_resumes/

# 2. Run tests
python test_agents.py
python test_langgraph.py
```

### Scenario 3: API Endpoint Testing
Tests the REST API:
```bash
# Terminal 1: Start server
uvicorn main:app --reload

# Terminal 2: Run tests
python test_fastapi.py
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "GEMINI_API_KEY environment variable not set"
**Solution:** Check `.env` file exists and contains API keys
```bash
cat .env  # Verify keys are present
```

### Issue: "Cannot connect to MongoDB"
**Solution:** Verify MongoDB URI is correct
```bash
# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('YOUR_MONGODB_URI'); print(client.server_info())"
```

### Issue: "Pinecone index not found"
**Solution:** Index is created automatically on first run. Wait a few seconds and retry.

### Issue: "Rate limit exceeded" (Gemini API)
**Solution:** Gemini has 60 RPM limit. Wait 1 minute and retry.

### Issue: Test resumes not processed
**Solution:** Ensure PDFs are valid and in `backend/test_resumes/` directory
```bash
ls -lh backend/test_resumes/*.pdf
```

## Performance Expectations

- **Agent Tests**: ~30-60 seconds (depends on LLM API response times)
- **LangGraph Workflow**: ~1-2 minutes (with 3-5 resumes)
- **FastAPI Tests**: ~30-90 seconds (depends on /api/match endpoint)

## Test Coverage

Current test coverage includes:
- ✅ All 5 agent initialization and execution
- ✅ LLM API calls (Gemini, OpenRouter)
- ✅ Embedding generation (768-dim vectors)
- ✅ Match scoring algorithm (40/30/30 weighting)
- ✅ Skill recommendation logic (65-79% threshold)
- ✅ LangGraph state management
- ✅ FastAPI request/response handling
- ✅ Database operations (MongoDB, Pinecone)

## Next Steps

After successful testing:

1. **Deploy to Production**
   ```bash
   docker-compose up -d
   ```

2. **Monitor Logs**
   ```bash
   docker-compose logs -f backend
   ```

3. **Run Frontend Tests**
   ```bash
   cd frontend
   npm test
   ```

## Support

For issues or questions:
- Check logs: `tail -f backend/app.log`
- Review agent code: `backend/agents/*.py`
- Inspect graph executor: `backend/graph_executor.py`
- FastAPI docs: `http://localhost:8000/docs` (when server running)
