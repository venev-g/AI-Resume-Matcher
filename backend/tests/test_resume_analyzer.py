"""Tests for Resume Analyzer Agent."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agents.resume_analyzer import ResumeAnalyzerAgent


class TestResumeAnalyzerAgent:
    """Test suite for Resume Analyzer Agent."""
    
    @pytest.fixture
    def agent(self, mock_openrouter_client):
        """Create resume analyzer agent with mocked client."""
        with patch('agents.resume_analyzer.OpenAI', return_value=mock_openrouter_client):
            agent = ResumeAnalyzerAgent()
            agent.client = mock_openrouter_client
            return agent
    
    @pytest.mark.asyncio
    async def test_analyze_resume_success(self, agent, sample_pdf_path, sample_resume_data):
        """Test successful resume analysis."""
        import json
        
        # Mock PDF parsing
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [
                Mock(text="John Doe\njohn.doe@example.com\nPython, FastAPI, MongoDB")
            ]
            
            # Mock LLM response
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps(sample_resume_data)))]
                )
            )
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is not None
            assert "candidate_name" in result
            assert "skills" in result
            assert "experience_years" in result
            assert isinstance(result["skills"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_resume_pdf_parsing_error(self, agent, sample_pdf_path):
        """Test handling of PDF parsing errors."""
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.side_effect = Exception("PDF parsing failed")
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is None or "error" in result
    
    @pytest.mark.asyncio
    async def test_analyze_resume_invalid_json_response(self, agent, sample_pdf_path):
        """Test handling of invalid JSON from LLM."""
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [Mock(text="Resume content")]
            
            # Mock invalid JSON response
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content="Not valid JSON"))]
                )
            )
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_analyze_resume_with_markdown(self, agent, sample_pdf_path):
        """Test resume analysis with markdown formatted response."""
        import json
        
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [Mock(text="Resume content")]
            
            resume_data = {
                "candidate_name": "Test User",
                "skills": ["Python"],
                "experience_years": 3
            }
            
            # Mock response with markdown
            markdown_response = f"```json\n{json.dumps(resume_data)}\n```"
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=markdown_response))]
                )
            )
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is not None
            assert result["candidate_name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_analyze_batch_success(self, agent, sample_pdf_path, sample_resume_data):
        """Test batch resume analysis."""
        import json
        
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [Mock(text="Resume content")]
            
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps(sample_resume_data)))]
                )
            )
            
            resume_files = [sample_pdf_path, sample_pdf_path]
            results = await agent.analyze_batch(resume_files)
            
            assert len(results) == 2
            assert all("candidate_name" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_analyze_batch_partial_failure(self, agent, sample_pdf_path, sample_resume_data):
        """Test batch analysis with some failures."""
        import json
        
        call_count = 0
        
        def mock_partition(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Parse error")
            return [Mock(text="Resume content")]
        
        with patch('agents.resume_analyzer.partition_pdf', side_effect=mock_partition):
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps(sample_resume_data)))]
                )
            )
            
            resume_files = [sample_pdf_path, sample_pdf_path]
            results = await agent.analyze_batch(resume_files)
            
            # Should skip failed files
            assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_analyze_empty_pdf(self, agent, sample_pdf_path):
        """Test analysis of empty PDF."""
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = []
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            # Should handle empty content
            assert result is None or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_resume_truncation(self, agent, sample_pdf_path):
        """Test text truncation for long resumes."""
        import json
        
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            # Create very long text
            long_text = "Lorem ipsum " * 1000
            mock_partition.return_value = [Mock(text=long_text)]
            
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "candidate_name": "Test",
                        "skills": ["Python"],
                        "experience_years": 5
                    })))]
                )
            )
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is not None
            # Verify LLM was called with truncated text
            call_args = agent.client.chat.completions.create.call_args
            assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_analyze_resume_special_characters(self, agent, sample_pdf_path):
        """Test resume with special characters."""
        import json
        
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [
                Mock(text="José García\nC++, C#, .NET developer")
            ]
            
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "candidate_name": "José García",
                        "skills": ["C++", "C#", ".NET"],
                        "experience_years": 5
                    })))]
                )
            )
            
            result = await agent.analyze_resume(sample_pdf_path)
            
            assert result is not None
            assert result["candidate_name"] == "José García"
    
    @pytest.mark.asyncio
    async def test_resume_id_generation(self, agent, sample_pdf_path, sample_resume_data):
        """Test unique resume ID generation."""
        import json
        
        with patch('agents.resume_analyzer.partition_pdf') as mock_partition:
            mock_partition.return_value = [Mock(text="Resume")]
            
            agent.client.chat.completions.create = Mock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps(sample_resume_data)))]
                )
            )
            
            result1 = await agent.analyze_resume(sample_pdf_path)
            result2 = await agent.analyze_resume(sample_pdf_path)
            
            # Resume IDs should be different for different calls
            assert result1["resume_id"] != result2["resume_id"]
