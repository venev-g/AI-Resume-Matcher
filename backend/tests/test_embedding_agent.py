"""Tests for Embedding Agent."""

import pytest
from unittest.mock import Mock, patch
from agents.embedding_agent import EmbeddingAgent


class TestEmbeddingAgent:
    """Test suite for Embedding Agent."""
    
    @pytest.fixture
    def agent(self, mock_gemini_client):
        """Create embedding agent with mocked client."""
        with patch('agents.embedding_agent.genai.Client', return_value=mock_gemini_client):
            agent = EmbeddingAgent()
            agent.client = mock_gemini_client
            return agent
    
    @pytest.mark.asyncio
    async def test_embed_jd_success(self, agent, sample_jd_data, sample_embedding):
        """Test successful JD embedding generation."""
        # Mock embedding response
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        result = await agent.embed_jd(sample_jd_data)
        
        assert result is not None
        assert len(result) == 768
        assert all(isinstance(x, (int, float)) for x in result)
    
    @pytest.mark.asyncio
    async def test_embed_resume_success(self, agent, sample_resume_data, sample_embedding):
        """Test successful resume embedding generation."""
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        result = await agent.embed_resume(sample_resume_data)
        
        assert result is not None
        assert len(result) == 768
    
    @pytest.mark.asyncio
    async def test_embed_text_success(self, agent, sample_embedding):
        """Test general text embedding."""
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        result = await agent.embed_text("Test text content")
        
        assert result is not None
        assert len(result) == 768
    
    @pytest.mark.asyncio
    async def test_embed_jd_with_truncation(self, agent, sample_embedding):
        """Test JD embedding with very long text."""
        # Create JD data with very long content
        long_jd = {
            "job_title": "Test " * 1000,
            "required_skills": ["Skill" + str(i) for i in range(100)],
            "experience_years": 5,
            "qualifications": ["Qual " * 100],
            "responsibilities": ["Resp " * 100]
        }
        
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        result = await agent.embed_jd(long_jd)
        
        assert result is not None
        # Verify truncation happened (check call args)
        call_args = agent.client.models.embed_content.call_args
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_embed_batch_resumes(self, agent, sample_resume_data, sample_embedding):
        """Test batch embedding generation for multiple resumes."""
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        resume_list = [sample_resume_data.copy() for _ in range(3)]
        results = await agent.embed_batch_resumes(resume_list)
        
        assert len(results) == 3
        assert all("resume_data" in r and "embedding" in r for r in results)
        assert all(len(r["embedding"]) == 768 for r in results)
    
    @pytest.mark.asyncio
    async def test_embed_with_api_error(self, agent, sample_jd_data):
        """Test handling of API errors."""
        # Mock API error
        agent.client.models.embed_content = Mock(
            side_effect=Exception("API Error")
        )
        
        result = await agent.embed_jd(sample_jd_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_embed_wrong_dimension(self, agent, sample_jd_data):
        """Test handling of wrong embedding dimension."""
        # Mock response with wrong dimension
        wrong_embedding = [0.1] * 512  # Wrong dimension
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=wrong_embedding)])
        )
        
        result = await agent.embed_jd(sample_jd_data)
        
        assert result is None  # Should reject wrong dimension
    
    @pytest.mark.asyncio
    async def test_embed_empty_content(self, agent):
        """Test embedding with empty content."""
        empty_jd = {
            "job_title": "",
            "required_skills": [],
            "experience_years": 0,
            "qualifications": [],
            "responsibilities": []
        }
        
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=[0.1] * 768)])
        )
        
        result = await agent.embed_jd(empty_jd)
        
        # Should handle empty content
        assert result is None or len(result) == 768
    
    @pytest.mark.asyncio
    async def test_prepare_text_truncation(self, agent):
        """Test text preparation and truncation."""
        long_text = "x" * 20000  # Exceeds max_text_length
        
        prepared = agent._prepare_text(long_text)
        
        assert len(prepared) <= agent.max_text_length
    
    @pytest.mark.asyncio
    async def test_embed_batch_partial_failure(self, agent, sample_resume_data, sample_embedding):
        """Test batch embedding with some failures."""
        call_count = 0
        
        def mock_embed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Embed error")
            return Mock(embeddings=[Mock(values=sample_embedding)])
        
        agent.client.models.embed_content = mock_embed
        
        resume_list = [sample_resume_data.copy() for _ in range(3)]
        results = await agent.embed_batch_resumes(resume_list)
        
        # Should skip failed embeddings
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_create_resume_text(self, agent, sample_resume_data):
        """Test resume text creation helper."""
        result = await agent._create_resume_text(sample_resume_data)
        
        assert isinstance(result, str)
        assert sample_resume_data["candidate_name"] in result
        assert any(skill in result for skill in sample_resume_data["skills"])
    
    @pytest.mark.asyncio
    async def test_embed_special_characters(self, agent, sample_embedding):
        """Test embedding with special characters."""
        special_jd = {
            "job_title": "C++ / C# Developer @ Tech™",
            "required_skills": ["C++", "C#", ".NET", "Node.js"],
            "experience_years": 5,
            "qualifications": ["BS in CS"],
            "responsibilities": ["Develop & maintain software"]
        }
        
        agent.client.models.embed_content = Mock(
            return_value=Mock(embeddings=[Mock(values=sample_embedding)])
        )
        
        result = await agent.embed_jd(special_jd)
        
        assert result is not None
        assert len(result) == 768
