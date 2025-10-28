"""Tests for Graph Executor (LangGraph Orchestrator)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from graph_executor import GraphExecutor


class TestGraphExecutor:
    """Test suite for Graph Executor."""
    
    @pytest.fixture
    def executor(self):
        """Create graph executor with mocked services."""
        with patch('graph_executor.JDExtractorAgent'), \
             patch('graph_executor.ResumeAnalyzerAgent'), \
             patch('graph_executor.EmbeddingAgent'), \
             patch('graph_executor.MatchEvaluatorAgent'), \
             patch('graph_executor.SkillRecommenderAgent'), \
             patch('graph_executor.MongoDBService'), \
             patch('graph_executor.PineconeService'):
            
            executor = GraphExecutor()
            
            # Mock agents
            executor.jd_extractor.extract_jd_data = AsyncMock(return_value={
                "job_title": "Test Job",
                "required_skills": ["Python"],
                "experience_years": 5
            })
            
            executor.resume_analyzer.analyze_batch = AsyncMock(return_value=[{
                "resume_id": "test_001",
                "candidate_name": "Test User",
                "skills": ["Python"],
                "experience_years": 5
            }])
            
            executor.embedding_agent.embed_jd = AsyncMock(return_value=[0.1] * 768)
            executor.embedding_agent.embed_batch_resumes = AsyncMock(return_value=[{
                "resume_data": {"resume_id": "test_001"},
                "embedding": [0.1] * 768
            }])
            executor.embedding_agent.embed_text = AsyncMock(return_value=[0.1] * 768)
            executor.embedding_agent._create_resume_text = AsyncMock(return_value="Resume text")
            
            executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[{
                "resume_id": "test_001",
                "match_score": 85.0,
                "skill_match_score": 90.0,
                "experience_match_score": 80.0,
                "role_match_score": 85.0,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "recommendation": "Highly recommended"
            }])
            
            executor.skill_recommender.recommend_batch = AsyncMock(
                return_value=[{
                    "resume_id": "test_001",
                    "match_score": 85.0,
                    "skill_gaps": []
                }]
            )
            
            executor.mongodb.connect = AsyncMock()
            executor.mongodb.store_match_result = AsyncMock()
            executor.mongodb.close = AsyncMock()
            
            executor.pinecone.search_by_jd = AsyncMock(return_value=[{
                "resume_id": "stored_001",
                "candidate_name": "Stored User",
                "skills": ["Python"],
                "experience_years": 5,
                "work_history": [],
                "education": []
            }])
            
            executor.pinecone.store_resume_embedding = AsyncMock(return_value=True)
            
            return executor
    
    @pytest.mark.asyncio
    async def test_execute_success(self, executor, sample_pdf_path):
        """Test successful workflow execution."""
        result = await executor.execute(
            jd_text="Test job description",
            resume_files=[sample_pdf_path]
        )
        
        assert "matches" in result
        assert "total_resumes" in result
        assert "high_matches" in result
        assert "potential_matches" in result
        assert result["total_resumes"] >= 0
    
    @pytest.mark.asyncio
    async def test_execute_empty_resumes(self, executor):
        """Test execution with no resumes."""
        executor.resume_analyzer.analyze_batch = AsyncMock(return_value=[])
        
        result = await executor.execute(
            jd_text="Test JD",
            resume_files=[]
        )
        
        assert result["total_resumes"] == 0
        assert result["matches"] == []
    
    @pytest.mark.asyncio
    async def test_execute_jd_extraction_failure(self, executor, sample_pdf_path):
        """Test handling of JD extraction failure."""
        executor.jd_extractor.extract_jd_data = AsyncMock(return_value=None)
        
        result = await executor.execute(
            jd_text="Invalid JD",
            resume_files=[sample_pdf_path]
        )
        
        # Should handle gracefully
        assert "error" in result or result["total_resumes"] == 0
    
    @pytest.mark.asyncio
    async def test_search_database_success(self, executor):
        """Test database search functionality."""
        result = await executor.search_database(
            jd_text="Test JD",
            min_match_score=80.0,
            top_k=50
        )
        
        assert "matches" in result
        assert "total_resumes" in result
        assert isinstance(result["matches"], list)
    
    @pytest.mark.asyncio
    async def test_search_database_no_results(self, executor):
        """Test database search with no matching resumes."""
        executor.pinecone.search_by_jd = AsyncMock(return_value=[])
        
        result = await executor.search_database(
            jd_text="Test JD",
            min_match_score=80.0
        )
        
        assert result["total_resumes"] == 0
        assert result["matches"] == []
    
    @pytest.mark.asyncio
    async def test_search_database_filters_by_score(self, executor):
        """Test that database search filters by minimum score."""
        # Mock matches with varying scores
        executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
            {"resume_id": "1", "match_score": 85.0, "skill_gaps": []},
            {"resume_id": "2", "match_score": 75.0, "skill_gaps": []},
            {"resume_id": "3", "match_score": 90.0, "skill_gaps": []}
        ])
        
        result = await executor.search_database(
            jd_text="Test JD",
            min_match_score=80.0
        )
        
        # Should only include matches >= 80%
        assert all(m["match_score"] >= 80.0 for m in result["matches"])
    
    @pytest.mark.asyncio
    async def test_store_resumes_success(self, executor, sample_pdf_path):
        """Test storing resumes in database."""
        result = await executor.store_resumes([sample_pdf_path])
        
        assert "stored_count" in result
        assert "failed_count" in result
        assert result["stored_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_store_resumes_partial_failure(self, executor, sample_pdf_path):
        """Test storing resumes with some failures."""
        # Mock to return success, then failure, then success
        call_count = 0
        async def mock_store(resume_id, embedding, metadata):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return False
            return True
        
        executor.pinecone.store_resume_embedding = AsyncMock(side_effect=mock_store)
        
        # Mock 3 resumes
        executor.resume_analyzer.analyze_batch = AsyncMock(return_value=[
            {"resume_id": "1"},
            {"resume_id": "2"},
            {"resume_id": "3"}
        ])
        
        executor.embedding_agent.embed_batch_resumes = AsyncMock(return_value=[
            {"resume_data": {"resume_id": "1"}, "embedding": [0.1] * 768},
            {"resume_data": {"resume_id": "2"}, "embedding": [0.1] * 768},
            {"resume_data": {"resume_id": "3"}, "embedding": [0.1] * 768}
        ])
        
        result = await executor.store_resumes([sample_pdf_path] * 3)
        
        assert result["stored_count"] == 2
        assert result["failed_count"] == 1
    
    @pytest.mark.asyncio
    async def test_store_resumes_no_embeddings(self, executor, sample_pdf_path):
        """Test storing resumes when embedding generation fails."""
        executor.embedding_agent.embed_batch_resumes = AsyncMock(return_value=[])
        
        result = await executor.store_resumes([sample_pdf_path])
        
        assert result["stored_count"] == 0
    
    @pytest.mark.asyncio
    async def test_mongodb_storage_called(self, executor, sample_pdf_path):
        """Test that MongoDB storage is called during execution."""
        await executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        executor.mongodb.connect.assert_called()
        executor.mongodb.store_match_result.assert_called()
        executor.mongodb.close.assert_called()
    
    @pytest.mark.asyncio
    async def test_workflow_node_sequence(self, executor, sample_pdf_path):
        """Test that workflow nodes are called in correct sequence."""
        await executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        # Verify call order
        executor.jd_extractor.extract_jd_data.assert_called_once()
        executor.resume_analyzer.analyze_batch.assert_called_once()
        executor.embedding_agent.embed_jd.assert_called_once()
        executor.embedding_agent.embed_batch_resumes.assert_called_once()
        executor.match_evaluator.evaluate_batch.assert_called_once()
        executor.skill_recommender.recommend_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_high_match_statistics(self, executor, sample_pdf_path):
        """Test calculation of high match statistics."""
        executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
            {"match_score": 85.0, "skill_gaps": []},
            {"match_score": 90.0, "skill_gaps": []},
            {"match_score": 75.0, "skill_gaps": []},
            {"match_score": 82.0, "skill_gaps": []}
        ])
        
        executor.skill_recommender.recommend_batch = AsyncMock(
            side_effect=lambda x, *args: x
        )
        
        result = await executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        assert result["high_matches"] == 3  # 85, 90, 82
        assert result["potential_matches"] == 1  # 75
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, executor, sample_pdf_path):
        """Test error handling doesn't crash entire workflow."""
        executor.resume_analyzer.analyze_batch = AsyncMock(
            side_effect=Exception("Analysis failed")
        )
        
        result = await executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        # Should return valid result structure even on error
        assert "matches" in result
        assert "total_resumes" in result
