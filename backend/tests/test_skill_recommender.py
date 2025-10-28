"""Tests for Skill Recommender Agent."""

import pytest
from unittest.mock import Mock, patch
from agents.skill_recommender import SkillRecommenderAgent


class TestSkillRecommenderAgent:
    """Test suite for Skill Recommender Agent."""
    
    @pytest.fixture
    def agent(self, mock_gemini_client):
        """Create skill recommender agent with mocked client."""
        with patch('agents.skill_recommender.genai.Client', return_value=mock_gemini_client):
            agent = SkillRecommenderAgent()
            agent.client = mock_gemini_client
            return agent
    
    @pytest.mark.asyncio
    async def test_recommend_skills_potential_candidate(self, agent, sample_jd_data, 
                                                        sample_resume_data_potential, 
                                                        sample_skill_gaps):
        """Test skill recommendations for potential candidate (65-79%)."""
        import json
        
        missing_skills = ["Docker", "Kubernetes", "PostgreSQL"]
        match_score = 72.0
        
        # Mock LLM response with skill gaps
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(sample_skill_gaps))
        )
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("missing_skill" in r for r in result)
        assert all("importance" in r for r in result)
        assert all("learning_path" in r for r in result)
        assert all("estimated_time" in r for r in result)
    
    @pytest.mark.asyncio
    async def test_recommend_skills_high_match_skipped(self, agent, sample_jd_data, 
                                                       sample_resume_data):
        """Test that recommendations are skipped for high matches (≥80%)."""
        missing_skills = ["Docker"]
        match_score = 85.0
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data,
            match_score
        )
        
        assert result == []  # No recommendations for high matches
    
    @pytest.mark.asyncio
    async def test_recommend_skills_low_match_skipped(self, agent, sample_jd_data, 
                                                      sample_resume_data_low_match):
        """Test that recommendations are skipped for low matches (<65%)."""
        missing_skills = ["Docker", "Python", "FastAPI"]
        match_score = 45.0
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_low_match,
            match_score
        )
        
        assert result == []  # No recommendations for very low matches
    
    @pytest.mark.asyncio
    async def test_recommend_skills_no_missing(self, agent, sample_jd_data, sample_resume_data):
        """Test recommendations when no skills are missing."""
        missing_skills = []
        match_score = 75.0
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data,
            match_score
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_recommend_skills_with_markdown(self, agent, sample_jd_data, 
                                                   sample_resume_data_potential):
        """Test handling of markdown-formatted LLM response."""
        import json
        
        missing_skills = ["Docker"]
        match_score = 70.0
        
        recommendations = [
            {
                "missing_skill": "Docker",
                "importance": "high",
                "reason": "Essential for deployment",
                "learning_path": "Docker course",
                "estimated_time": "2 months"
            }
        ]
        
        # Mock response with markdown
        markdown_response = f"```json\n{json.dumps(recommendations)}\n```"
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=markdown_response)
        )
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        assert len(result) == 1
        assert result[0]["missing_skill"] == "Docker"
    
    @pytest.mark.asyncio
    async def test_recommend_skills_invalid_importance(self, agent, sample_jd_data, 
                                                       sample_resume_data_potential):
        """Test handling of invalid importance levels."""
        import json
        
        missing_skills = ["Docker"]
        match_score = 70.0
        
        recommendations = [
            {
                "missing_skill": "Docker",
                "importance": "invalid_level",  # Invalid
                "reason": "Test",
                "learning_path": "Test",
                "estimated_time": "Test"
            }
        ]
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(recommendations))
        )
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        # Should normalize invalid importance to "medium"
        assert result[0]["importance"] == "medium"
    
    @pytest.mark.asyncio
    async def test_recommend_skills_incomplete_data(self, agent, sample_jd_data, 
                                                    sample_resume_data_potential):
        """Test handling of incomplete recommendation data."""
        import json
        
        missing_skills = ["Docker"]
        match_score = 70.0
        
        # Mock response with missing fields
        incomplete_recommendations = [
            {
                "missing_skill": "Docker",
                "importance": "high"
                # Missing other fields
            }
        ]
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(incomplete_recommendations))
        )
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        # Should skip incomplete recommendations
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_recommend_skills_max_limit(self, agent, sample_jd_data, 
                                              sample_resume_data_potential):
        """Test that recommendations are limited to max_recommendations."""
        import json
        
        missing_skills = ["Skill" + str(i) for i in range(10)]
        match_score = 70.0
        
        # Mock response with more than max recommendations
        many_recommendations = [
            {
                "missing_skill": f"Skill{i}",
                "importance": "medium",
                "reason": "Test",
                "learning_path": "Test",
                "estimated_time": "1 month"
            }
            for i in range(10)
        ]
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(many_recommendations))
        )
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        # Should limit to max_recommendations (5)
        assert len(result) <= agent.max_recommendations
    
    @pytest.mark.asyncio
    async def test_recommend_batch(self, agent, sample_jd_data, sample_match_result, 
                                   sample_skill_gaps):
        """Test batch recommendations for multiple match results."""
        import json
        
        # Create match results with different scores
        match_results = [
            {**sample_match_result, "match_score": 75.0, "missing_skills": ["Docker"]},
            {**sample_match_result, "match_score": 85.0, "missing_skills": []},
            {**sample_match_result, "match_score": 50.0, "missing_skills": ["Many", "Skills"]}
        ]
        
        resume_data_dict = {
            sample_match_result["resume_id"]: {
                "candidate_name": "Test",
                "skills": ["Python"],
                "experience_years": 5
            }
        }
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(sample_skill_gaps))
        )
        
        results = await agent.recommend_batch(
            match_results,
            sample_jd_data,
            resume_data_dict
        )
        
        assert len(results) == 3
        # Only the 75% match should have recommendations
        assert len(results[0]["skill_gaps"]) > 0
        assert len(results[1]["skill_gaps"]) == 0  # High match
        assert len(results[2]["skill_gaps"]) == 0  # Low match
    
    @pytest.mark.asyncio
    async def test_format_recommendations_text(self, agent, sample_skill_gaps):
        """Test formatting of recommendations as text."""
        text = agent.format_recommendations_text(sample_skill_gaps)
        
        assert isinstance(text, str)
        assert "Docker" in text
        assert "Kubernetes" in text
        assert "high" in text.lower()
    
    @pytest.mark.asyncio
    async def test_format_recommendations_empty(self, agent):
        """Test formatting of empty recommendations."""
        text = agent.format_recommendations_text([])
        
        assert isinstance(text, str)
        assert "No specific" in text or "no" in text.lower()
    
    @pytest.mark.asyncio
    async def test_recommend_skills_with_retry(self, agent, sample_jd_data, 
                                               sample_resume_data_potential, sample_skill_gaps):
        """Test retry logic for rate limit errors."""
        import json
        from google.api_core import exceptions
        
        missing_skills = ["Docker"]
        match_score = 70.0
        
        call_count = 0
        
        def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise exceptions.ResourceExhausted("Rate limit")
            return Mock(text=json.dumps(sample_skill_gaps))
        
        agent.client.models.generate_content = mock_generate
        
        result = await agent.recommend_skills(
            missing_skills,
            sample_jd_data,
            sample_resume_data_potential,
            match_score
        )
        
        assert len(result) > 0
        assert call_count == 2  # Should retry once
