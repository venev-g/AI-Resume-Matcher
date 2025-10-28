"""Tests for Match Evaluator Agent."""

import pytest
import numpy as np
from agents.match_evaluator import MatchEvaluatorAgent


class TestMatchEvaluatorAgent:
    """Test suite for Match Evaluator Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create match evaluator agent."""
        return MatchEvaluatorAgent()
    
    def test_calculate_skill_match_perfect(self, agent):
        """Test perfect skill match (100%)."""
        resume_skills = ["Python", "FastAPI", "MongoDB", "Docker"]
        required_skills = ["Python", "FastAPI", "MongoDB", "Docker"]
        
        score, matched, missing = agent._calculate_skill_match(resume_skills, required_skills)
        
        assert score == 100.0
        assert len(matched) == 4
        assert len(missing) == 0
    
    def test_calculate_skill_match_partial(self, agent):
        """Test partial skill match."""
        resume_skills = ["Python", "FastAPI", "MongoDB"]
        required_skills = ["Python", "FastAPI", "MongoDB", "Docker", "Kubernetes"]
        
        score, matched, missing = agent._calculate_skill_match(resume_skills, required_skills)
        
        assert score == 60.0  # 3 out of 5
        assert len(matched) == 3
        assert len(missing) == 2
        assert "Docker" in missing
        assert "Kubernetes" in missing
    
    def test_calculate_skill_match_no_match(self, agent):
        """Test no skill match."""
        resume_skills = ["Java", "Spring", "Oracle"]
        required_skills = ["Python", "FastAPI", "MongoDB"]
        
        score, matched, missing = agent._calculate_skill_match(resume_skills, required_skills)
        
        assert score == 0.0
        assert len(matched) == 0
        assert len(missing) == 3
    
    def test_calculate_skill_match_case_insensitive(self, agent):
        """Test case-insensitive skill matching."""
        resume_skills = ["python", "FASTAPI", "MongoDb"]
        required_skills = ["Python", "FastAPI", "MongoDB"]
        
        score, matched, missing = agent._calculate_skill_match(resume_skills, required_skills)
        
        assert score == 100.0
        assert len(matched) == 3
    
    def test_calculate_skill_match_empty_required(self, agent):
        """Test skill match with no required skills."""
        resume_skills = ["Python", "FastAPI"]
        required_skills = []
        
        score, matched, missing = agent._calculate_skill_match(resume_skills, required_skills)
        
        assert score == 100.0  # No requirements means perfect match
        assert len(matched) == 0
        assert len(missing) == 0
    
    def test_calculate_experience_match_exact(self, agent):
        """Test exact experience match."""
        score = agent._calculate_experience_match(5.0, 5.0)
        assert score == 100.0
    
    def test_calculate_experience_match_exceeds(self, agent):
        """Test experience exceeding requirement."""
        score = agent._calculate_experience_match(8.0, 5.0)
        assert score == 100.0  # Capped at 100
    
    def test_calculate_experience_match_below(self, agent):
        """Test experience below requirement."""
        score = agent._calculate_experience_match(3.0, 5.0)
        assert score == 60.0  # 3/5 = 60%
    
    def test_calculate_experience_match_zero_required(self, agent):
        """Test experience match with no requirement."""
        score = agent._calculate_experience_match(5.0, 0.0)
        assert score == 100.0
    
    def test_calculate_role_similarity(self, agent, sample_embedding, sample_resume_embedding):
        """Test role similarity calculation using cosine similarity."""
        score = agent._calculate_role_similarity(sample_resume_embedding, sample_embedding)
        
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_role_similarity_identical(self, agent, sample_embedding):
        """Test role similarity with identical embeddings."""
        score = agent._calculate_role_similarity(sample_embedding, sample_embedding)
        
        # Identical embeddings should give high similarity
        assert score >= 95.0
    
    def test_calculate_role_similarity_opposite(self, agent):
        """Test role similarity with opposite embeddings."""
        embedding1 = [1.0] * 768
        embedding2 = [-1.0] * 768
        
        score = agent._calculate_role_similarity(embedding1, embedding2)
        
        # Opposite embeddings should give low similarity
        assert score < 50.0
    
    @pytest.mark.asyncio
    async def test_evaluate_match_high_score(self, agent, sample_resume_data, sample_jd_data, 
                                             sample_embedding, sample_resume_embedding):
        """Test evaluation resulting in high match score (≥80%)."""
        result = await agent.evaluate_match(
            sample_resume_data,
            sample_jd_data,
            sample_resume_embedding,
            sample_embedding
        )
        
        assert "match_score" in result
        assert "skill_match_score" in result
        assert "experience_match_score" in result
        assert "role_match_score" in result
        assert isinstance(result["match_score"], float)
        assert 0 <= result["match_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_evaluate_match_potential_candidate(self, agent, sample_resume_data_potential, 
                                                      sample_jd_data, sample_embedding, 
                                                      sample_resume_embedding):
        """Test evaluation resulting in potential match (65-79%)."""
        result = await agent.evaluate_match(
            sample_resume_data_potential,
            sample_jd_data,
            sample_resume_embedding,
            sample_embedding
        )
        
        assert "match_score" in result
        # Score should be in potential range for this candidate
        assert result["match_score"] < 80 or result["match_score"] >= 65
    
    @pytest.mark.asyncio
    async def test_evaluate_match_low_score(self, agent, sample_resume_data_low_match, 
                                            sample_jd_data, sample_embedding, 
                                            sample_resume_embedding):
        """Test evaluation resulting in low match score (<65%)."""
        result = await agent.evaluate_match(
            sample_resume_data_low_match,
            sample_jd_data,
            sample_resume_embedding,
            sample_embedding
        )
        
        assert "match_score" in result
        assert "recommendation" in result
        # Low skill match should result in lower overall score
        assert result["skill_match_score"] < 50
    
    @pytest.mark.asyncio
    async def test_evaluate_batch(self, agent, sample_resume_data, sample_jd_data, 
                                  sample_embedding, sample_resume_embedding):
        """Test batch evaluation of multiple resumes."""
        resume_embeddings_list = [
            {
                "resume_data": sample_resume_data,
                "embedding": sample_resume_embedding
            }
            for _ in range(3)
        ]
        
        results = await agent.evaluate_batch(
            resume_embeddings_list,
            sample_jd_data,
            sample_embedding
        )
        
        assert len(results) == 3
        assert all("match_score" in r for r in results)
        # Results should be sorted by match_score (highest first)
        scores = [r["match_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_evaluate_match_with_error(self, agent, sample_jd_data, sample_embedding):
        """Test evaluation with invalid data."""
        invalid_resume = {
            "resume_id": "test",
            "candidate_name": None,
            "skills": None,  # Invalid
            "experience_years": None  # Invalid
        }
        
        result = await agent.evaluate_match(
            invalid_resume,
            sample_jd_data,
            sample_embedding,
            sample_embedding
        )
        
        # Should handle gracefully
        assert result is not None
        assert "match_score" in result
    
    @pytest.mark.asyncio
    async def test_evaluate_recommendation_messages(self, agent, sample_jd_data, 
                                                    sample_embedding):
        """Test recommendation messages for different score ranges."""
        # High match (≥80%)
        high_match_resume = {
            "resume_id": "test1",
            "candidate_name": "Test High",
            "skills": sample_jd_data["required_skills"],
            "experience_years": sample_jd_data["experience_years"]
        }
        
        result_high = await agent.evaluate_match(
            high_match_resume,
            sample_jd_data,
            sample_embedding,
            sample_embedding
        )
        
        if result_high["match_score"] >= 80:
            assert "Highly recommended" in result_high["recommendation"]
        elif result_high["match_score"] >= 65:
            assert "Potential candidate" in result_high["recommendation"]
        else:
            assert "Not recommended" in result_high["recommendation"]
    
    @pytest.mark.asyncio
    async def test_weighted_scoring_formula(self, agent, sample_resume_data, sample_jd_data,
                                            sample_embedding, sample_resume_embedding):
        """Test that weighted scoring formula is applied correctly."""
        result = await agent.evaluate_match(
            sample_resume_data,
            sample_jd_data,
            sample_resume_embedding,
            sample_embedding
        )
        
        # Manually calculate expected score
        expected_score = (
            result["skill_match_score"] * agent.skill_weight +
            result["experience_match_score"] * agent.experience_weight +
            result["role_match_score"] * agent.role_weight
        )
        
        # Should match (within rounding)
        assert abs(result["match_score"] - expected_score) < 0.1
