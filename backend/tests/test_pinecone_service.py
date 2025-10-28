"""Tests for Pinecone Service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.pinecone_service import PineconeService


class TestPineconeService:
    """Test suite for Pinecone Service."""
    
    @pytest.fixture
    def service(self, mock_pinecone_index):
        """Create Pinecone service with mocked index."""
        with patch('services.pinecone_service.Pinecone') as mock_pinecone:
            # Mock Pinecone client
            mock_client = Mock()
            mock_client.list_indexes = Mock(return_value=[Mock(name="test-index")])
            mock_client.Index = Mock(return_value=mock_pinecone_index)
            mock_pinecone.return_value = mock_client
            
            service = PineconeService()
            service.index = mock_pinecone_index
            return service
    
    @pytest.mark.asyncio
    async def test_upsert_resume_success(self, service, sample_embedding, sample_resume_data):
        """Test successful resume upsert."""
        result = await service.upsert_resume(
            resume_id="test_resume_001",
            embedding=sample_embedding,
            metadata=sample_resume_data
        )
        
        assert result is True
        service.index.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_resume_wrong_dimension(self, service, sample_resume_data):
        """Test upsert with wrong embedding dimension."""
        wrong_embedding = [0.1] * 512  # Wrong dimension
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            await service.upsert_resume(
                resume_id="test_resume",
                embedding=wrong_embedding,
                metadata=sample_resume_data
            )
    
    @pytest.mark.asyncio
    async def test_upsert_batch_success(self, service, sample_embedding):
        """Test batch upsert."""
        vectors = [
            {
                "id": f"resume_{i}",
                "values": sample_embedding,
                "metadata": {"candidate_name": f"Candidate {i}"}
            }
            for i in range(5)
        ]
        
        result = await service.upsert_batch(vectors)
        
        assert result is True
        # Should be called once for small batch
        assert service.index.upsert.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_upsert_batch_large(self, service, sample_embedding):
        """Test batch upsert with large number of vectors."""
        # Create 250 vectors (more than batch size of 100)
        vectors = [
            {
                "id": f"resume_{i}",
                "values": sample_embedding,
                "metadata": {"candidate_name": f"Candidate {i}"}
            }
            for i in range(250)
        ]
        
        result = await service.upsert_batch(vectors)
        
        assert result is True
        # Should be called multiple times for batching
        assert service.index.upsert.call_count == 3  # 100, 100, 50
    
    @pytest.mark.asyncio
    async def test_query_similar_success(self, service, sample_embedding):
        """Test querying for similar resumes."""
        results = await service.query_similar(
            embedding=sample_embedding,
            top_k=10
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert "id" in results[0]
        assert "score" in results[0]
        assert "metadata" in results[0]
    
    @pytest.mark.asyncio
    async def test_query_similar_with_min_score(self, service, sample_embedding):
        """Test query with minimum score filter."""
        # Mock response with varying scores
        mock_matches = [
            Mock(id=f"resume_{i}", score=0.9 - i*0.1, metadata={})
            for i in range(5)
        ]
        service.index.query = Mock(return_value=Mock(matches=mock_matches))
        
        results = await service.query_similar(
            embedding=sample_embedding,
            top_k=10,
            min_score=0.7
        )
        
        # Should filter out results below 0.7
        assert all(r["score"] >= 0.7 for r in results)
    
    @pytest.mark.asyncio
    async def test_query_similar_wrong_dimension(self, service):
        """Test query with wrong embedding dimension."""
        wrong_embedding = [0.1] * 512
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            await service.query_similar(embedding=wrong_embedding)
    
    @pytest.mark.asyncio
    async def test_search_by_jd(self, service, sample_jd_embedding):
        """Test searching resumes by JD embedding."""
        # Mock query results
        mock_matches = [
            Mock(
                id=f"resume_{i}",
                score=0.85 - i*0.05,
                metadata={
                    "candidate_name": f"Candidate {i}",
                    "skills": ["Python", "FastAPI"],
                    "experience_years": 5.0,
                    "work_history": [],
                    "education": []
                }
            )
            for i in range(3)
        ]
        service.index.query = Mock(return_value=Mock(matches=mock_matches))
        
        results = await service.search_by_jd(
            jd_embedding=sample_jd_embedding,
            top_k=10,
            min_similarity=0.5
        )
        
        assert len(results) == 3
        assert all("resume_id" in r for r in results)
        assert all("candidate_name" in r for r in results)
        assert all("similarity_score" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_store_resume_embedding(self, service, sample_embedding, sample_resume_data):
        """Test storing resume embedding with metadata."""
        result = await service.store_resume_embedding(
            resume_id="test_resume",
            embedding=sample_embedding,
            resume_data=sample_resume_data
        )
        
        assert result is True
        service.index.upsert.assert_called_once()
        
        # Verify metadata is properly formatted
        call_args = service.index.upsert.call_args
        vectors = call_args[1]["vectors"]
        assert len(vectors) == 1
        assert "metadata" in vectors[0]
    
    @pytest.mark.asyncio
    async def test_store_resume_embedding_truncates_arrays(self, service, sample_embedding):
        """Test that large arrays in metadata are truncated."""
        large_resume_data = {
            "candidate_name": "Test",
            "skills": ["Skill" + str(i) for i in range(100)],  # > 50
            "work_history": ["Job" + str(i) for i in range(20)],  # > 10
            "education": ["Edu" + str(i) for i in range(10)],  # > 5
            "experience_years": 5
        }
        
        result = await service.store_resume_embedding(
            resume_id="test",
            embedding=sample_embedding,
            resume_data=large_resume_data
        )
        
        assert result is True
        
        # Check that arrays were truncated
        call_args = service.index.upsert.call_args
        metadata = call_args[1]["vectors"][0]["metadata"]
        assert len(metadata["skills"]) <= 50
        assert len(metadata["work_history"]) <= 10
        assert len(metadata["education"]) <= 5
    
    @pytest.mark.asyncio
    async def test_delete_resume_success(self, service):
        """Test deleting a resume."""
        result = await service.delete_resume("test_resume")
        
        assert result is True
        service.index.delete.assert_called_once_with(ids=["test_resume"])
    
    @pytest.mark.asyncio
    async def test_delete_resume_error(self, service):
        """Test handling delete errors."""
        service.index.delete = Mock(side_effect=Exception("Delete failed"))
        
        result = await service.delete_resume("test_resume")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_index_stats(self, service):
        """Test retrieving index statistics."""
        stats = await service.get_index_stats()
        
        assert "total_vectors" in stats
        assert "dimension" in stats
        assert "index_fullness" in stats
        assert stats["dimension"] == 768
    
    @pytest.mark.asyncio
    async def test_get_index_stats_error(self, service):
        """Test handling stats retrieval errors."""
        service.index.describe_index_stats = Mock(side_effect=Exception("Stats failed"))
        
        stats = await service.get_index_stats()
        
        assert stats == {}
    
    @pytest.mark.asyncio
    async def test_upsert_resume_api_error(self, service, sample_embedding, sample_resume_data):
        """Test handling API errors during upsert."""
        service.index.upsert = Mock(side_effect=Exception("API Error"))
        
        result = await service.upsert_resume(
            resume_id="test",
            embedding=sample_embedding,
            metadata=sample_resume_data
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_query_with_filter(self, service, sample_embedding):
        """Test query with metadata filter."""
        filter_dict = {"experience_years": {"$gte": 5}}
        
        await service.query_similar(
            embedding=sample_embedding,
            top_k=10,
            filter_dict=filter_dict
        )
        
        # Verify filter was passed to query
        call_args = service.index.query.call_args
        assert call_args[1]["filter"] == filter_dict
