"""Tests for JD Extractor Agent."""

import pytest
from unittest.mock import Mock, patch
from agents.jd_extractor import JDExtractorAgent


class TestJDExtractorAgent:
    """Test suite for JD Extractor Agent."""
    
    @pytest.fixture
    def agent(self, mock_gemini_client):
        """Create JD extractor agent with mocked client."""
        with patch('agents.jd_extractor.genai.Client', return_value=mock_gemini_client):
            agent = JDExtractorAgent()
            agent.client = mock_gemini_client
            return agent
    
    @pytest.fixture
    def sample_jd_text(self):
        """Sample job description text."""
        return """
        Senior Python Developer
        
        We are seeking an experienced Python developer to join our team.
        
        Requirements:
        - 5+ years of Python development experience
        - Strong knowledge of FastAPI and web frameworks
        - Experience with MongoDB and PostgreSQL
        - Familiarity with Docker and Kubernetes
        - Understanding of REST API design principles
        - Excellent problem-solving skills
        
        Qualifications:
        - Bachelor's degree in Computer Science or related field
        - Experience with cloud platforms (AWS, GCP, Azure)
        - Strong communication skills
        
        Responsibilities:
        - Design and develop scalable backend services
        - Collaborate with frontend developers
        - Mentor junior team members
        - Participate in code reviews
        """
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_success(self, agent, sample_jd_text, sample_jd_data):
        """Test successful JD extraction."""
        # Mock the LLM response
        import json
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(sample_jd_data))
        )
        
        result = await agent.extract_jd_data(sample_jd_text)
        
        assert result is not None
        assert "job_title" in result
        assert "required_skills" in result
        assert "experience_years" in result
        assert isinstance(result["required_skills"], list)
        assert isinstance(result["experience_years"], (int, float))
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_with_markdown(self, agent, sample_jd_text):
        """Test JD extraction when response has markdown formatting."""
        import json
        jd_data = {
            "job_title": "Test Job",
            "required_skills": ["Python"],
            "experience_years": 5
        }
        
        # Mock response with markdown code blocks
        markdown_response = f"```json\n{json.dumps(jd_data)}\n```"
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=markdown_response)
        )
        
        result = await agent.extract_jd_data(sample_jd_text)
        
        assert result is not None
        assert result["job_title"] == "Test Job"
        assert "Python" in result["required_skills"]
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_empty_input(self, agent):
        """Test JD extraction with empty input."""
        result = await agent.extract_jd_data("")
        
        # Should return default structure or None
        assert result is None or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_retry_on_rate_limit(self, agent, sample_jd_text):
        """Test retry logic on rate limit error."""
        import json
        from google.api_core import exceptions
        
        # Mock rate limit error on first call, success on second
        call_count = 0
        
        def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise exceptions.ResourceExhausted("Rate limit exceeded")
            return Mock(text=json.dumps({"job_title": "Test", "required_skills": [], "experience_years": 0}))
        
        agent.client.models.generate_content = mock_generate
        
        result = await agent.extract_jd_data(sample_jd_text)
        
        assert result is not None
        assert call_count == 2  # Should retry once
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_invalid_json(self, agent, sample_jd_text):
        """Test handling of invalid JSON response."""
        # Mock invalid JSON response
        agent.client.models.generate_content = Mock(
            return_value=Mock(text="This is not valid JSON")
        )
        
        result = await agent.extract_jd_data(sample_jd_text)
        
        assert result is None  # Should handle parsing error gracefully
    
    @pytest.mark.asyncio
    async def test_extract_jd_data_partial_data(self, agent, sample_jd_text):
        """Test extraction with partial data."""
        import json
        
        # Mock response with only some fields
        partial_data = {
            "job_title": "Developer",
            "required_skills": ["Python"]
            # Missing experience_years and other fields
        }
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps(partial_data))
        )
        
        result = await agent.extract_jd_data(sample_jd_text)
        
        assert result is not None
        assert "job_title" in result
        assert "required_skills" in result
    
    @pytest.mark.asyncio
    async def test_strip_markdown_json(self, agent):
        """Test markdown stripping utility."""
        test_cases = [
            ("```json\n{\"test\": 1}\n```", "{\"test\": 1}"),
            ("```\n{\"test\": 2}\n```", "{\"test\": 2}"),
            ("{\"test\": 3}", "{\"test\": 3}"),
            ("  ```json\n{\"test\": 4}\n```  ", "{\"test\": 4}"),
        ]
        
        for input_text, expected in test_cases:
            result = agent._strip_markdown_json(input_text)
            assert result.strip() == expected.strip()
    
    @pytest.mark.asyncio
    async def test_extract_with_special_characters(self, agent):
        """Test extraction with special characters in JD."""
        jd_with_special = """
        Senior Developer @ Tech Corp!
        Skills: C++, C#, .NET, Node.js
        Salary: $120,000-$150,000
        """
        
        import json
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps({
                "job_title": "Senior Developer @ Tech Corp!",
                "required_skills": ["C++", "C#", ".NET", "Node.js"],
                "experience_years": 5
            }))
        )
        
        result = await agent.extract_jd_data(jd_with_special)
        
        assert result is not None
        assert "C++" in result["required_skills"]
    
    @pytest.mark.asyncio
    async def test_extract_multiple_calls(self, agent, sample_jd_text):
        """Test multiple extraction calls to ensure no state issues."""
        import json
        
        agent.client.models.generate_content = Mock(
            return_value=Mock(text=json.dumps({
                "job_title": "Test Job",
                "required_skills": ["Python"],
                "experience_years": 5
            }))
        )
        
        result1 = await agent.extract_jd_data(sample_jd_text)
        result2 = await agent.extract_jd_data(sample_jd_text)
        
        assert result1 is not None
        assert result2 is not None
        assert result1["job_title"] == result2["job_title"]
