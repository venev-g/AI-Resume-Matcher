"""Pytest configuration and shared fixtures for all tests."""

import os
import sys
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_jd_data() -> Dict[str, Any]:
    """Sample job description data for testing."""
    return {
        "job_title": "Senior Python Developer",
        "required_skills": [
            "Python", "FastAPI", "MongoDB", "PostgreSQL",
            "Docker", "Kubernetes", "REST API", "Git"
        ],
        "experience_years": 5.0,
        "qualifications": [
            "Bachelor's degree in Computer Science",
            "5+ years Python development experience",
            "Experience with cloud platforms"
        ],
        "responsibilities": [
            "Design and develop backend APIs",
            "Mentor junior developers",
            "Review code and ensure quality"
        ]
    }


@pytest.fixture
def sample_resume_data() -> Dict[str, Any]:
    """Sample resume data for testing."""
    return {
        "resume_id": "resume_test_001",
        "candidate_name": "John Doe",
        "email": "john.doe@example.com",
        "skills": [
            "Python", "FastAPI", "MongoDB", "Docker",
            "REST API", "Git", "Linux", "AWS"
        ],
        "experience_years": 6.0,
        "work_history": [
            "Senior Software Engineer at Tech Corp (2020-2024)",
            "Software Developer at StartupXYZ (2018-2020)"
        ],
        "education": [
            "B.S. Computer Science, MIT (2018)",
            "Online Courses: Docker, Kubernetes"
        ]
    }


@pytest.fixture
def sample_resume_data_low_match() -> Dict[str, Any]:
    """Sample resume data with low match for testing."""
    return {
        "resume_id": "resume_test_002",
        "candidate_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "skills": [
            "Java", "Spring Boot", "Oracle", "Jenkins"
        ],
        "experience_years": 3.0,
        "work_history": [
            "Java Developer at Enterprise Inc (2021-2024)"
        ],
        "education": [
            "B.S. Information Systems (2021)"
        ]
    }


@pytest.fixture
def sample_resume_data_potential() -> Dict[str, Any]:
    """Sample resume data for potential match (65-79%) testing."""
    return {
        "resume_id": "resume_test_003",
        "candidate_name": "Alice Johnson",
        "email": "alice.j@example.com",
        "skills": [
            "Python", "Flask", "PostgreSQL", "Git", "Linux"
        ],
        "experience_years": 4.0,
        "work_history": [
            "Python Developer at WebCo (2020-2024)"
        ],
        "education": [
            "B.S. Computer Engineering (2020)"
        ]
    }


@pytest.fixture
def sample_embedding() -> List[float]:
    """Sample 768-dimensional embedding vector."""
    import random
    random.seed(42)
    return [random.random() for _ in range(768)]


@pytest.fixture
def sample_jd_embedding(sample_embedding) -> List[float]:
    """Sample JD embedding."""
    return sample_embedding


@pytest.fixture
def sample_resume_embedding() -> List[float]:
    """Sample resume embedding (slightly different from JD)."""
    import random
    random.seed(43)
    return [random.random() for _ in range(768)]


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    client = Mock()
    
    # Mock generate_content response
    mock_response = Mock()
    mock_response.text = '{"job_title": "Test Job", "required_skills": ["Python"], "experience_years": 5}'
    client.models.generate_content = Mock(return_value=mock_response)
    
    # Mock embed_content response
    mock_embed_response = Mock()
    mock_embed_response.embeddings = [Mock(values=[0.1] * 768)]
    client.models.embed_content = Mock(return_value=mock_embed_response)
    
    return client


@pytest.fixture
def mock_openrouter_client():
    """Mock OpenRouter client for testing."""
    client = Mock()
    
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"candidate_name": "Test User", "skills": ["Python"]}'))
    ]
    client.chat.completions.create = Mock(return_value=mock_response)
    
    return client


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for testing."""
    index = Mock()
    
    # Mock upsert
    index.upsert = Mock(return_value={"upserted_count": 1})
    
    # Mock query
    mock_match = Mock()
    mock_match.id = "resume_001"
    mock_match.score = 0.85
    mock_match.metadata = {
        "candidate_name": "Test User",
        "skills": ["Python", "FastAPI"],
        "experience_years": 5.0
    }
    
    mock_results = Mock()
    mock_results.matches = [mock_match]
    index.query = Mock(return_value=mock_results)
    
    # Mock delete
    index.delete = Mock(return_value={})
    
    # Mock describe_index_stats
    mock_stats = Mock()
    mock_stats.total_vector_count = 10
    mock_stats.dimension = 768
    mock_stats.index_fullness = 0.1
    index.describe_index_stats = Mock(return_value=mock_stats)
    
    return index


@pytest.fixture
def mock_mongodb_collection():
    """Mock MongoDB collection for testing."""
    collection = Mock()
    
    # Mock insert_one
    collection.insert_one = AsyncMock(return_value=Mock(inserted_id="test_id"))
    
    # Mock find
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[
        {
            "_id": "test_id",
            "jd_text": "Test JD",
            "matches": [],
            "created_at": "2024-01-01"
        }
    ])
    collection.find = Mock(return_value=mock_cursor)
    
    # Mock aggregate
    mock_agg_cursor = AsyncMock()
    mock_agg_cursor.to_list = AsyncMock(return_value=[
        {"total_matches": 100, "avg_score": 75.5}
    ])
    collection.aggregate = Mock(return_value=mock_agg_cursor)
    
    return collection


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test_resume.pdf"
    
    # Create a minimal PDF file
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Resume) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
307
%%EOF
"""
    
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)


@pytest.fixture
def sample_skill_gaps() -> List[Dict[str, Any]]:
    """Sample skill gap recommendations."""
    return [
        {
            "missing_skill": "Docker",
            "importance": "high",
            "reason": "Containerization is essential for modern DevOps practices",
            "learning_path": "Complete Docker Mastery course on Udemy",
            "estimated_time": "2-3 months"
        },
        {
            "missing_skill": "Kubernetes",
            "importance": "high",
            "reason": "Container orchestration is critical for scalable applications",
            "learning_path": "Kubernetes certification program",
            "estimated_time": "3-4 months"
        },
        {
            "missing_skill": "PostgreSQL",
            "importance": "medium",
            "reason": "Relational database knowledge is important for backend development",
            "learning_path": "PostgreSQL tutorials and practice projects",
            "estimated_time": "1-2 months"
        }
    ]


@pytest.fixture
def sample_match_result() -> Dict[str, Any]:
    """Sample match evaluation result."""
    return {
        "resume_id": "resume_001",
        "candidate_name": "John Doe",
        "match_score": 87.5,
        "skill_match_score": 90.0,
        "experience_match_score": 85.0,
        "role_match_score": 87.5,
        "matched_skills": ["Python", "FastAPI", "MongoDB", "Docker"],
        "missing_skills": ["Kubernetes", "PostgreSQL"],
        "skill_gaps": [],
        "recommendation": "Highly recommended - Strong match across all criteria"
    }


@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch):
    """Set up environment variables for all tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_openrouter_key")
    monkeypatch.setenv("PINECONE_API_KEY", "test_pinecone_key")
    monkeypatch.setenv("PINECONE_ENVIRONMENT", "us-east-1")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "test-index")
    monkeypatch.setenv("MONGODB_URI", "mongodb://test:test@localhost:27017/test")
    monkeypatch.setenv("MONGODB_DATABASE", "test_db")
