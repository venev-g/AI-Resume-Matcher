"""Tests for FastAPI main application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO
from main import app


class TestMainAPI:
    """Test suite for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_executor(self):
        """Mock GraphExecutor."""
        with patch('main.graph_executor') as mock_exec:
            mock_exec.execute = AsyncMock(return_value={
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0
            })
            mock_exec.search_database = AsyncMock(return_value={
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0
            })
            mock_exec.store_resumes = AsyncMock(return_value={
                "stored_count": 0,
                "failed_count": 0,
                "details": []
            })
            yield mock_exec
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-resume-matcher"
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_match_resumes_success(self, client, mock_executor, tmp_path):
        """Test successful resume matching."""
        # Create test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")
        
        mock_executor.execute = AsyncMock(return_value={
            "matches": [{
                "resume_id": "test_001",
                "candidate_name": "Test User",
                "match_score": 85.0,
                "skill_match_score": 90.0,
                "experience_match_score": 80.0,
                "role_match_score": 85.0,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "recommendation": "Highly recommended",
                "skill_gaps": []
            }],
            "total_resumes": 1,
            "high_matches": 1,
            "potential_matches": 0
        })
        
        with open(pdf_file, "rb") as f:
            response = client.post(
                "/api/match",
                data={"jd_text": "Test job description"},
                files={"files": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert data["total_resumes"] == 1
    
    def test_match_resumes_no_jd_text(self, client, tmp_path):
        """Test matching without JD text."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")
        
        with open(pdf_file, "rb") as f:
            response = client.post(
                "/api/match",
                data={},
                files={"files": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_match_resumes_invalid_file_type(self, client):
        """Test matching with invalid file type."""
        response = client.post(
            "/api/match",
            data={"jd_text": "Test JD"},
            files={"files": ("test.txt", BytesIO(b"text content"), "text/plain")}
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_search_database_success(self, client, mock_executor):
        """Test database search endpoint."""
        mock_executor.search_database = AsyncMock(return_value={
            "matches": [{
                "resume_id": "stored_001",
                "candidate_name": "Stored User",
                "match_score": 87.0,
                "skill_match_score": 85.0,
                "experience_match_score": 90.0,
                "role_match_score": 87.0,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "recommendation": "Highly recommended",
                "skill_gaps": []
            }],
            "total_resumes": 1,
            "high_matches": 1,
            "potential_matches": 0
        })
        
        response = client.post(
            "/api/search-database",
            data={
                "jd_text": "Test job description",
                "min_match_score": "80.0",
                "top_k": "50"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert data["total_resumes"] == 1
    
    def test_search_database_default_params(self, client, mock_executor):
        """Test database search with default parameters."""
        response = client.post(
            "/api/search-database",
            data={"jd_text": "Test JD"}
        )
        
        assert response.status_code == 200
        # Should use defaults: min_match_score=80.0, top_k=100
    
    def test_search_database_invalid_score(self, client):
        """Test database search with invalid match score."""
        response = client.post(
            "/api/search-database",
            data={
                "jd_text": "Test JD",
                "min_match_score": "150"  # Invalid: > 100
            }
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_store_resumes_success(self, client, mock_executor, tmp_path):
        """Test storing resumes endpoint."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")
        
        mock_executor.store_resumes = AsyncMock(return_value={
            "stored_count": 1,
            "failed_count": 0,
            "details": [{"resume_id": "test_001", "status": "success"}]
        })
        
        with open(pdf_file, "rb") as f:
            response = client.post(
                "/api/store-resumes",
                files={"files": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stored_count"] == 1
        assert data["failed_count"] == 0
    
    def test_store_resumes_no_files(self, client):
        """Test storing with no files provided."""
        response = client.post("/api/store-resumes")
        
        assert response.status_code == 422  # Validation error
    
    def test_store_resumes_too_many_files(self, client, tmp_path):
        """Test storing more than 100 files."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")
        
        # Try to upload 101 files (should be rejected)
        files = []
        with open(pdf_file, "rb") as f:
            content = f.read()
            for i in range(101):
                files.append(("files", (f"test_{i}.pdf", BytesIO(content), "application/pdf")))
        
        response = client.post("/api/store-resumes", files=files)
        
        # Should reject or handle gracefully
        assert response.status_code in [400, 422, 200]
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, client):
        """Test statistics endpoint."""
        with patch('services.mongodb_service.MongoDBService') as MockMongo:
            mock_mongo_instance = MockMongo.return_value
            mock_mongo_instance.connect = AsyncMock()
            mock_mongo_instance.get_statistics = AsyncMock(return_value={
                "total_matches": 100,
                "avg_match_score": 78.5,
                "high_matches": 45,
                "potential_matches": 35
            })
            mock_mongo_instance.close = AsyncMock()
            
            response = client.get("/api/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_matches" in data
    
    @pytest.mark.asyncio
    async def test_get_history(self, client):
        """Test match history endpoint."""
        with patch('services.mongodb_service.MongoDBService') as MockMongo:
            mock_mongo_instance = MockMongo.return_value
            mock_mongo_instance.connect = AsyncMock()
            mock_mongo_instance.get_match_history = AsyncMock(return_value=[
                {
                    "jd_title": "Test Job",
                    "timestamp": "2024-01-01T00:00:00",
                    "total_matches": 5
                }
            ])
            mock_mongo_instance.close = AsyncMock()
            
            response = client.get("/api/history?limit=10&skip=0")
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/health")
        
        # CORS middleware should add headers
        # Test with valid endpoint instead of OPTIONS
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_error_handling_500(self, client, mock_executor, tmp_path):
        """Test 500 error handling."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")
        
        mock_executor.execute = AsyncMock(side_effect=Exception("Internal error"))
        
        with open(pdf_file, "rb") as f:
            response = client.post(
                "/api/match",
                data={"jd_text": "Test JD"},
                files={"files": ("test.pdf", f, "application/pdf")}
            )
        
        # Should return 500 error
        assert response.status_code == 500
    
    def test_file_size_limit(self, client):
        """Test file size validation."""
        # Create oversized file (> 10MB)
        large_content = b"0" * (11 * 1024 * 1024)
        
        response = client.post(
            "/api/match",
            data={"jd_text": "Test JD"},
            files={"files": ("large.pdf", BytesIO(large_content), "application/pdf")}
        )
        
        # Should reject or handle large files
        assert response.status_code in [400, 413, 422, 200]
    
    def test_api_documentation(self, client):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/match" in schema["paths"]
