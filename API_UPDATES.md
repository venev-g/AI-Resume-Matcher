# API Updates - Database Search & Resume Storage

## Overview

The AI Resume Matcher now supports **two modes of operation**:

1. **Upload Mode** (Original): Upload resumes and match them against a JD in real-time
2. **Search Mode** (New): Search previously stored resumes in Pinecone database by JD

## New Features

### 1. Resume Storage
Store resume embeddings in Pinecone for future searches without reprocessing.

### 2. Database Search
Search stored resumes using semantic similarity with configurable match thresholds (default: ≥80%).

### 3. Skill Gap Recommendations
Automatically generate recommendations for candidates scoring 65-79% with actionable learning paths.

---

## New API Endpoints

### POST `/api/search-database`

Search stored resumes in database by job description.

**Request:**
- `Content-Type: multipart/form-data`
- `jd_text` (string, required): Job description text
- `min_match_score` (float, optional): Minimum match score (0-100, default: 80.0)
- `top_k` (int, optional): Maximum results from database (1-1000, default: 100)

**Response:**
```json
{
  "matches": [
    {
      "resume_id": "resume_123",
      "candidate_name": "Jane Smith",
      "match_score": 87.5,
      "skill_match_score": 90.0,
      "experience_match_score": 85.0,
      "role_match_score": 87.5,
      "matched_skills": ["Python", "FastAPI", "MongoDB"],
      "missing_skills": ["Docker", "Kubernetes"],
      "skill_gaps": [],
      "recommendation": "Highly recommended - Strong match across all criteria"
    }
  ],
  "total_resumes": 5,
  "high_matches": 3,
  "potential_matches": 2
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/api/search-database" \
  -F "jd_text=Senior Python Developer with 5+ years experience..." \
  -F "min_match_score=80" \
  -F "top_k=50"
```

---

### POST `/api/store-resumes`

Store resume PDFs in database for future matching.

**Request:**
- `Content-Type: multipart/form-data`
- `files` (File[], required): Resume PDF files (max 100, 10MB each)

**Response:**
```json
{
  "success": true,
  "total_files": 25,
  "stored_count": 24,
  "failed_count": 1,
  "message": "Successfully stored 24 resumes"
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/api/store-resumes" \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf" \
  -F "files=@resume3.pdf"
```

---

## Updated Workflow

### Upload Mode (Original)
```
1. Upload JD + Resume PDFs
   ↓
2. Extract JD Data (Gemini)
   ↓
3. Analyze Resumes (OpenRouter + Unstructured)
   ↓
4. Generate Embeddings (Gemini)
   ↓
5. Evaluate Matches (Weighted Scoring)
   ↓
6. Generate Skill Recommendations (65-79% matches)
   ↓
7. Return Results
```

### Search Mode (New)
```
1. Enter JD Text + Min Score Threshold
   ↓
2. Extract JD Data (Gemini)
   ↓
3. Generate JD Embedding (Gemini)
   ↓
4. Search Pinecone (Semantic Similarity)
   ↓
5. Evaluate Retrieved Resumes (Weighted Scoring)
   ↓
6. Filter by Min Score (≥80% default)
   ↓
7. Generate Skill Recommendations (65-79% matches)
   ↓
8. Return Results
```

### Storage Workflow (New)
```
1. Upload Resume PDFs
   ↓
2. Analyze Resumes (OpenRouter + Unstructured)
   ↓
3. Generate Embeddings (Gemini)
   ↓
4. Store in Pinecone with Metadata
   ↓
5. Return Storage Statistics
```

---

## Key Implementation Details

### Matching Algorithm (Unchanged)
```
Overall Score = (Skill Match × 40%) + 
                (Experience Match × 30%) + 
                (Role Similarity × 30%)
```

- **80%+ Match**: High match - Highly recommended
- **65-79% Match**: Potential candidate - Skill gaps identified with recommendations
- **<65% Match**: Not recommended - Significant gaps

### Skill Gap Recommendations
Activated automatically for 65-79% matches:
- Top 5 most important missing skills
- Importance level (high/medium/low)
- Specific learning paths (courses, certifications, projects)
- Estimated time to acquire skill
- Reasoning for why skill is important

### Database Search Parameters

**min_similarity** (Internal): 0.5 cosine similarity threshold for initial Pinecone retrieval
- Ensures broad candidate pool before weighted scoring
- Final filtering happens after complete evaluation

**min_match_score** (User-facing): Configurable 0-100 threshold
- Default: 80% (high-quality matches only)
- Adjustable via API or frontend slider
- Recommended: 65-80% to include potential candidates

### Pinecone Storage
Resumes stored with metadata:
- `candidate_name`: String
- `email`: String
- `skills`: Array (limited to 50)
- `experience_years`: Float
- `work_history`: Array (limited to 10)
- `education`: Array (limited to 5)

**Embedding**: 768-dimensional Gemini text-embedding-004 vector

---

## Frontend Changes

### Mode Toggle
- **Upload Mode**: Process new resumes immediately
- **Search Mode**: Query stored resumes from database

### New Features
1. Mode selector (Upload/Search)
2. Match score threshold slider (0-100%)
3. Resume storage section (always visible)
4. Success/error messages for storage operations

### UI Enhancements
- Color-coded match results (green ≥80%, yellow 65-79%, red <65%)
- Skill gap recommendations displayed for potential matches
- Separate loading indicators for different operations

---

## Testing the New Features

### 1. Store Resumes
```bash
# Store sample resumes
curl -X POST "http://localhost:8000/api/store-resumes" \
  -F "files=@backend/test_resumes/resume1.pdf" \
  -F "files=@backend/test_resumes/resume2.pdf"
```

### 2. Search Database
```bash
# Search for matches
curl -X POST "http://localhost:8000/api/search-database" \
  -F "jd_text=Looking for a Senior Python Developer with FastAPI experience..." \
  -F "min_match_score=70"
```

### 3. Check Index Stats
```python
from services.pinecone_service import PineconeService

pinecone = PineconeService()
stats = await pinecone.get_index_stats()
print(f"Total vectors: {stats['total_vectors']}")
```

---

## Performance Considerations

### Upload Mode
- **Time**: ~5-10 seconds per resume
- **Batch Size**: Up to 50 resumes
- **Bottleneck**: PDF parsing + LLM calls

### Search Mode
- **Time**: ~2-5 seconds total (much faster!)
- **Batch Size**: Search up to 100 stored resumes
- **Bottleneck**: Embedding generation for JD only

### Storage
- **Time**: ~5-8 seconds per resume
- **Batch Size**: Up to 100 resumes
- **One-time Cost**: Storage happens once, searches are instant

---

## Migration Guide

### For Existing Users

1. **No Changes Required**: Original upload mode still works exactly the same

2. **Optional Enhancement**: Store your frequently used resumes:
   ```bash
   # Store your resume database
   curl -X POST "http://localhost:8000/api/store-resumes" \
     -F "files=@resume1.pdf" \
     -F "files=@resume2.pdf" \
     # ... add all your resumes
   ```

3. **Use Search Mode**: For faster matching of stored resumes against new JDs

### For New Users

1. **Start with Upload Mode**: Test the system with a few resumes
2. **Build Your Database**: Use storage endpoint to build resume database
3. **Switch to Search Mode**: Use for rapid matching as you receive new JDs

---

## Error Handling

### Common Errors

**"No matching resumes found in database"**
- Solution: Store resumes first using `/api/store-resumes`
- Or: Lower `min_match_score` threshold

**"Database search failed"**
- Check: Pinecone connection and API key
- Check: JD text is not empty

**"Failed to store resumes"**
- Check: File size limits (10MB per file)
- Check: Valid PDF files only
- Check: Batch size limit (100 files)

---

## Future Enhancements

1. **Resume Update API**: Update existing resume embeddings
2. **Metadata Filtering**: Filter by experience, location, etc.
3. **Batch JD Search**: Match multiple JDs against database
4. **Resume Deletion**: Remove specific resumes from database
5. **Advanced Analytics**: Track match trends over time

---

## Configuration

### Environment Variables (No Changes)
```bash
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=resume-jd-matcher
MONGODB_URI=your_mongodb_uri
```

### New Optional Settings
```bash
# Pinecone search defaults
DEFAULT_MIN_SIMILARITY=0.5
DEFAULT_TOP_K=100

# Match score defaults
DEFAULT_MIN_MATCH_SCORE=80.0
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs backend`
2. Verify Pinecone index: Use Pinecone console
3. Test with sample data first
4. Open GitHub issue with error details

---

**Last Updated**: October 28, 2025
**Version**: 2.0.0 (Database Search Update)
