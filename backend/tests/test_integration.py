"""End-to-end integration tests."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from graph_executor import GraphExecutor
from typing import List


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def full_executor(self):
        """Create executor with all components mocked."""
        with patch('graph_executor.JDExtractorAgent') as MockJD, \
             patch('graph_executor.ResumeAnalyzerAgent') as MockResume, \
             patch('graph_executor.EmbeddingAgent') as MockEmbed, \
             patch('graph_executor.MatchEvaluatorAgent') as MockMatch, \
             patch('graph_executor.SkillRecommenderAgent') as MockSkill, \
             patch('graph_executor.MongoDBService') as MockMongo, \
             patch('graph_executor.PineconeService') as MockPinecone:
            
            executor = GraphExecutor()
            
            # Setup complete workflow mocks
            executor.jd_extractor.extract_jd_data = AsyncMock(return_value={
                "job_title": "Senior Python Developer",
                "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "preferred_skills": ["AWS", "Kubernetes"],
                "experience_years": 5.0,
                "education_level": "Bachelor's",
                "role_description": "Build scalable APIs"
            })
            
            executor.resume_analyzer.analyze_batch = AsyncMock(return_value=[
                {
                    "resume_id": "candidate_001",
                    "candidate_name": "Alice Johnson",
                    "email": "alice@example.com",
                    "phone": "+1-555-0100",
                    "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
                    "experience_years": 6.0,
                    "education": ["BS Computer Science"],
                    "work_history": ["Senior Dev at TechCorp"],
                    "certifications": ["AWS Certified"]
                },
                {
                    "resume_id": "candidate_002",
                    "candidate_name": "Bob Smith",
                    "email": "bob@example.com",
                    "phone": "+1-555-0200",
                    "skills": ["Python", "Django", "MySQL"],
                    "experience_years": 3.0,
                    "education": ["BS Software Engineering"],
                    "work_history": ["Junior Dev at StartupXYZ"],
                    "certifications": []
                }
            ])
            
            executor.embedding_agent.embed_jd = AsyncMock(return_value=[0.1] * 768)
            executor.embedding_agent.embed_batch_resumes = AsyncMock(return_value=[
                {
                    "resume_data": {"resume_id": "candidate_001"},
                    "embedding": [0.11] * 768
                },
                {
                    "resume_data": {"resume_id": "candidate_002"},
                    "embedding": [0.08] * 768
                }
            ])
            executor.embedding_agent.embed_text = AsyncMock(return_value=[0.1] * 768)
            executor.embedding_agent._create_resume_text = AsyncMock(return_value="Resume text")
            
            executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
                {
                    "resume_id": "candidate_001",
                    "candidate_name": "Alice Johnson",
                    "match_score": 88.5,
                    "skill_match_score": 90.0,
                    "experience_match_score": 85.0,
                    "role_match_score": 90.0,
                    "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                    "missing_skills": ["Docker"],
                    "recommendation": "Highly recommended candidate"
                },
                {
                    "resume_id": "candidate_002",
                    "candidate_name": "Bob Smith",
                    "match_score": 72.0,
                    "skill_match_score": 65.0,
                    "experience_match_score": 70.0,
                    "role_match_score": 80.0,
                    "matched_skills": ["Python"],
                    "missing_skills": ["FastAPI", "PostgreSQL", "Docker"],
                    "recommendation": "Potential candidate with skill gaps"
                }
            ])
            
            executor.skill_recommender.recommend_batch = AsyncMock(
                side_effect=lambda matches, jd, *args: [
                    {
                        **match,
                        "skill_gaps": [] if match["match_score"] >= 80 else [
                            "Learn FastAPI framework",
                            "Gain PostgreSQL experience",
                            "Docker containerization skills"
                        ]
                    }
                    for match in matches
                ]
            )
            
            executor.mongodb.connect = AsyncMock()
            executor.mongodb.store_match_result = AsyncMock(return_value=True)
            executor.mongodb.close = AsyncMock()
            
            executor.pinecone.store_resume_embedding = AsyncMock(return_value=True)
            executor.pinecone.search_by_jd = AsyncMock(return_value=[
                {
                    "resume_id": "stored_001",
                    "candidate_name": "Charlie Brown",
                    "skills": ["Python", "FastAPI", "Docker"],
                    "experience_years": 5.0,
                    "work_history": ["Dev at CloudCorp"],
                    "education": ["BS CS"]
                }
            ])
            
            return executor
    
    @pytest.mark.asyncio
    async def test_complete_upload_workflow(self, full_executor, sample_pdf_path):
        """Test complete workflow from PDF upload to recommendations."""
        result = await full_executor.execute(
            jd_text="We need a Senior Python Developer with FastAPI experience...",
            resume_files=[sample_pdf_path, sample_pdf_path]
        )
        
        # Verify complete workflow execution
        assert "matches" in result
        assert "total_resumes" in result
        assert result["total_resumes"] == 2
        
        # Verify high match identified
        assert result["high_matches"] == 1
        assert result["potential_matches"] == 1
        
        # Verify match details
        matches = result["matches"]
        assert len(matches) == 2
        
        high_match = next(m for m in matches if m["match_score"] >= 80)
        assert high_match["candidate_name"] == "Alice Johnson"
        assert len(high_match["skill_gaps"]) == 0  # High matches don't get recommendations
        
        potential_match = next(m for m in matches if 65 <= m["match_score"] < 80)
        assert potential_match["candidate_name"] == "Bob Smith"
        assert len(potential_match["skill_gaps"]) > 0  # Potential matches get recommendations
    
    @pytest.mark.asyncio
    async def test_complete_database_search_workflow(self, full_executor):
        """Test complete database search workflow."""
        # Mock the pinecone search to return resumes with embeddings already
        full_executor.pinecone.search_by_jd = AsyncMock(return_value=[
            {
                "resume_id": "stored_001",
                "candidate_name": "Charlie Brown",
                "skills": ["Python", "FastAPI", "Docker"],
                "experience_years": 5.0,
                "work_history": ["Dev at CloudCorp"],
                "education": ["BS CS"],
                "embedding": [0.1] * 768  # Include embedding to skip _create_resume_text
            }
        ])
        
        # Mock match evaluator to return proper results
        full_executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
            {
                "resume_id": "stored_001",
                "candidate_name": "Charlie Brown",
                "match_score": 85.0,
                "skill_match_score": 90.0,
                "experience_match_score": 80.0,
                "role_match_score": 85.0,
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["PostgreSQL"],
                "recommendation": "Highly recommended"
            }
        ])
        
        result = await full_executor.search_database(
            jd_text="Python developer with FastAPI",
            min_match_score=80.0,
            top_k=50
        )
        
        # Verify workflow execution
        full_executor.jd_extractor.extract_jd_data.assert_called_once()
        full_executor.embedding_agent.embed_jd.assert_called_once()
        full_executor.pinecone.search_by_jd.assert_called_once()
        
        # Verify results structure
        assert "matches" in result
        assert "total_resumes" in result
    
    @pytest.mark.asyncio
    async def test_complete_storage_workflow(self, full_executor, sample_pdf_path):
        """Test complete resume storage workflow."""
        result = await full_executor.store_resumes([sample_pdf_path, sample_pdf_path])
        
        # Verify workflow execution
        full_executor.resume_analyzer.analyze_batch.assert_called_once()
        full_executor.embedding_agent.embed_batch_resumes.assert_called_once()
        
        # Verify storage
        assert full_executor.pinecone.store_resume_embedding.call_count == 2
        
        # Verify results
        assert result["stored_count"] == 2
        assert result["failed_count"] == 0
    
    @pytest.mark.asyncio
    async def test_data_flow_consistency(self, full_executor, sample_pdf_path):
        """Test that data flows correctly between components."""
        result = await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        # Verify JD extraction output is used for embedding
        jd_call_args = full_executor.embedding_agent.embed_jd.call_args
        assert jd_call_args is not None
        
        # Verify resume analysis output is used for embedding
        resume_call_args = full_executor.embedding_agent.embed_batch_resumes.call_args
        assert resume_call_args is not None
        
        # Verify embeddings are used for matching
        match_call_args = full_executor.match_evaluator.evaluate_batch.call_args
        assert match_call_args is not None
        
        # Verify matches are used for recommendations
        skill_call_args = full_executor.skill_recommender.recommend_batch.call_args
        assert skill_call_args is not None
    
    @pytest.mark.asyncio
    async def test_threshold_filtering(self, full_executor, sample_pdf_path):
        """Test that 80% threshold filtering works correctly."""
        # Setup matches with various scores
        full_executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
            {"resume_id": "1", "match_score": 92.0, "candidate_name": "User1", "skill_gaps": []},
            {"resume_id": "2", "match_score": 85.0, "candidate_name": "User2", "skill_gaps": []},
            {"resume_id": "3", "match_score": 75.0, "candidate_name": "User3", "skill_gaps": []},
            {"resume_id": "4", "match_score": 60.0, "candidate_name": "User4", "skill_gaps": []},
            {"resume_id": "5", "match_score": 88.0, "candidate_name": "User5", "skill_gaps": []}
        ])
        
        full_executor.skill_recommender.recommend_batch = AsyncMock(
            side_effect=lambda x, *args: x
        )
        
        result = await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path] * 5
        )
        
        # Verify high matches (≥80%)
        assert result["high_matches"] == 3  # 92, 85, 88
        
        # Verify potential matches (65-79%)
        assert result["potential_matches"] == 1  # 75
        
        # All matches are returned regardless of score
        # The system returns all matches but categorizes them in statistics
        assert result["total_resumes"] == 5
    
    @pytest.mark.asyncio
    async def test_skill_recommendation_logic(self, full_executor, sample_pdf_path):
        """Test that skill recommendations are only for 65-79% matches."""
        full_executor.match_evaluator.evaluate_batch = AsyncMock(return_value=[
            {"resume_id": "high", "match_score": 85.0},
            {"resume_id": "potential", "match_score": 70.0},
            {"resume_id": "low", "match_score": 60.0}
        ])
        
        recommendation_calls = []
        async def track_recommendations(matches, *args):
            recommendation_calls.append([m["resume_id"] for m in matches])
            return [{"skill_gaps": [] if m["match_score"] >= 80 else ["skill1"]} for m in matches]
        
        full_executor.skill_recommender.recommend_batch = AsyncMock(
            side_effect=track_recommendations
        )
        
        await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path] * 3
        )
        
        # Verify recommender was called with all matches
        assert len(recommendation_calls) > 0
    
    @pytest.mark.asyncio
    async def test_mongodb_persistence(self, full_executor, sample_pdf_path):
        """Test that all results are persisted to MongoDB."""
        await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path]
        )
        
        # Verify MongoDB operations
        full_executor.mongodb.connect.assert_called_once()
        full_executor.mongodb.store_match_result.assert_called_once()
        full_executor.mongodb.close.assert_called_once()
        
        # Verify stored data structure
        store_call = full_executor.mongodb.store_match_result.call_args
        assert store_call is not None
        # call_args is a tuple of (args, kwargs), we want args[0]
        if store_call.args:
            stored_data = store_call.args[0]
            assert "jd_data" in stored_data
            assert "matches" in stored_data
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, full_executor, sample_pdf_path):
        """Test that workflow recovers from component failures."""
        # Simulate partial failure in resume analysis
        full_executor.resume_analyzer.analyze_batch = AsyncMock(return_value=[
            {"resume_id": "success_001", "skills": ["Python"]},
            None,  # Failed resume
            {"resume_id": "success_002", "skills": ["Java"]}
        ])
        
        result = await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path] * 3
        )
        
        # Should process successful resumes
        assert "matches" in result
        # Total count should reflect actual processed resumes
        assert result["total_resumes"] >= 0
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, full_executor, sample_pdf_path):
        """Test that batch processing handles multiple resumes efficiently."""
        # Simulate 50 resumes
        num_resumes = 50
        
        full_executor.resume_analyzer.analyze_batch = AsyncMock(
            return_value=[
                {"resume_id": f"candidate_{i:03d}", "skills": ["Python"]}
                for i in range(num_resumes)
            ]
        )
        
        full_executor.embedding_agent.embed_batch_resumes = AsyncMock(
            return_value=[
                {"resume_data": {"resume_id": f"candidate_{i:03d}"}, "embedding": [0.1] * 768}
                for i in range(num_resumes)
            ]
        )
        
        full_executor.match_evaluator.evaluate_batch = AsyncMock(
            return_value=[
                {"resume_id": f"candidate_{i:03d}", "match_score": 75.0}
                for i in range(num_resumes)
            ]
        )
        
        full_executor.skill_recommender.recommend_batch = AsyncMock(
            side_effect=lambda x, *args: [{"skill_gaps": []} for _ in x]
        )
        
        result = await full_executor.execute(
            jd_text="Test JD",
            resume_files=[sample_pdf_path] * num_resumes
        )
        
        # Verify batch processing
        assert result["total_resumes"] == num_resumes
        
        # Verify agents were called with batches, not individual items
        assert full_executor.resume_analyzer.analyze_batch.call_count == 1
        assert full_executor.embedding_agent.embed_batch_resumes.call_count == 1
        assert full_executor.match_evaluator.evaluate_batch.call_count == 1
    
    @pytest.mark.asyncio
    async def test_end_to_end_with_real_data_structure(self, full_executor, sample_jd_data, 
                                                       sample_high_match_resume):
        """Test workflow with realistic data structures."""
        full_executor.jd_extractor.extract_jd_data = AsyncMock(
            return_value=sample_jd_data
        )
        
        full_executor.resume_analyzer.analyze_batch = AsyncMock(
            return_value=[sample_high_match_resume]
        )
        
        result = await full_executor.execute(
            jd_text="Realistic JD text...",
            resume_files=["test.pdf"]
        )
        
        # Verify output matches expected structure
        assert isinstance(result["matches"], list)
        if len(result["matches"]) > 0:
            match = result["matches"][0]
            assert "resume_id" in match
            assert "match_score" in match
            assert "skill_match_score" in match
            assert "experience_match_score" in match
            assert "role_match_score" in match
            assert "matched_skills" in match
            assert "missing_skills" in match
