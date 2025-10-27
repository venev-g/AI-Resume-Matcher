"""Test script for individual AI agents."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.jd_extractor import JDExtractorAgent
from agents.resume_analyzer import ResumeAnalyzerAgent
from agents.embedding_agent import EmbeddingAgent
from agents.match_evaluator import MatchEvaluatorAgent
from agents.skill_recommender import SkillRecommenderAgent


async def test_jd_extractor():
    """Test JD Extractor Agent."""
    print("\n" + "="*60)
    print("TEST 1: JD Extractor Agent")
    print("="*60)
    
    try:
        agent = JDExtractorAgent()
        print("✓ Agent initialized successfully")
        
        sample_jd = """
        Senior Python Developer
        
        We are looking for an experienced Python developer with 5+ years of experience.
        
        Required Skills:
        - Python, FastAPI, Django
        - PostgreSQL, MongoDB
        - Docker, Kubernetes
        - AWS, CI/CD
        
        Qualifications:
        - Bachelor's degree in Computer Science
        - 5+ years of backend development experience
        
        Responsibilities:
        - Design and implement scalable APIs
        - Mentor junior developers
        - Collaborate with cross-functional teams
        """
        
        print("\nExtracting JD data...")
        result = await agent.extract_jd_data(sample_jd)
        
        if result:
            print("\n✓ JD Extraction successful!")
            print(f"  Job Title: {result.get('job_title')}")
            print(f"  Required Skills: {result.get('required_skills')}")
            print(f"  Experience Years: {result.get('experience_years')}")
            print(f"  Qualifications: {result.get('qualifications')}")
            return result
        else:
            print("\n✗ JD Extraction failed")
            return None
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_resume_analyzer():
    """Test Resume Analyzer Agent."""
    print("\n" + "="*60)
    print("TEST 2: Resume Analyzer Agent")
    print("="*60)
    
    try:
        agent = ResumeAnalyzerAgent()
        print("✓ Agent initialized successfully")
        
        # Create a simple test PDF (we'll skip this if no PDF exists)
        test_pdf = Path("/home/ubuntu/AI-Resume-Matcher/backend/test_resume.pdf")
        
        if not test_pdf.exists():
            print("\n⚠ No test PDF found. Skipping Resume Analyzer test.")
            print("  To test this agent, create a test_resume.pdf file in the backend directory.")
            return None
        
        print(f"\nAnalyzing resume: {test_pdf}")
        result = await agent.analyze_resume(str(test_pdf))
        
        if result:
            print("\n✓ Resume Analysis successful!")
            print(f"  Candidate Name: {result.get('candidate_name')}")
            print(f"  Email: {result.get('email')}")
            print(f"  Skills: {result.get('skills')[:5]}...")  # Show first 5
            print(f"  Experience Years: {result.get('experience_years')}")
            return result
        else:
            print("\n✗ Resume Analysis failed")
            return None
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_embedding_agent(jd_data):
    """Test Embedding Agent."""
    print("\n" + "="*60)
    print("TEST 3: Embedding Agent")
    print("="*60)
    
    try:
        agent = EmbeddingAgent()
        print("✓ Agent initialized successfully")
        
        if not jd_data:
            print("\n⚠ No JD data available. Using sample data.")
            jd_data = {
                "job_title": "Senior Python Developer",
                "required_skills": ["Python", "FastAPI", "MongoDB"],
                "experience_years": 5,
                "qualifications": ["Bachelor's degree"],
                "responsibilities": ["Design APIs", "Mentor team"]
            }
        
        print("\nGenerating JD embedding...")
        jd_embedding = await agent.embed_jd(jd_data)
        
        if jd_embedding:
            print(f"\n✓ JD Embedding successful!")
            print(f"  Embedding dimension: {len(jd_embedding)}")
            print(f"  First 5 values: {jd_embedding[:5]}")
            return jd_embedding
        else:
            print("\n✗ JD Embedding failed")
            return None
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_match_evaluator(jd_data, jd_embedding):
    """Test Match Evaluator Agent."""
    print("\n" + "="*60)
    print("TEST 4: Match Evaluator Agent")
    print("="*60)
    
    try:
        agent = MatchEvaluatorAgent()
        print("✓ Agent initialized successfully")
        
        # Create sample resume data for testing
        resume_data = {
            "resume_id": "test_001",
            "candidate_name": "John Doe",
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "experience_years": 4.0,
            "work_history": ["Senior Developer at TechCorp (2020-2024)"],
            "education": ["B.S. Computer Science - MIT (2020)"]
        }
        
        # Generate resume embedding
        embedding_agent = EmbeddingAgent()
        resume_embedding = await embedding_agent.embed_resume(resume_data)
        
        if not resume_embedding or not jd_embedding:
            print("\n⚠ Missing embeddings. Cannot evaluate match.")
            return None
        
        print("\nEvaluating match...")
        result = await agent.evaluate_match(
            resume_data,
            jd_data,
            resume_embedding,
            jd_embedding
        )
        
        if result:
            print(f"\n✓ Match Evaluation successful!")
            print(f"  Candidate: {result.get('candidate_name')}")
            print(f"  Overall Match Score: {result.get('match_score')}%")
            print(f"  Skill Match: {result.get('skill_match_score')}%")
            print(f"  Experience Match: {result.get('experience_match_score')}%")
            print(f"  Role Match: {result.get('role_match_score')}%")
            print(f"  Matched Skills: {result.get('matched_skills')}")
            print(f"  Missing Skills: {result.get('missing_skills')}")
            return result
        else:
            print("\n✗ Match Evaluation failed")
            return None
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_skill_recommender(match_result, jd_data):
    """Test Skill Recommender Agent."""
    print("\n" + "="*60)
    print("TEST 5: Skill Recommender Agent")
    print("="*60)
    
    try:
        agent = SkillRecommenderAgent()
        print("✓ Agent initialized successfully")
        
        if not match_result:
            print("\n⚠ No match result available. Skipping test.")
            return None
        
        # Create sample data for testing
        resume_data = {
            "candidate_name": "John Doe",
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"]
        }
        
        missing_skills = match_result.get('missing_skills', [])
        match_score = match_result.get('match_score', 0)
        
        print(f"\nGenerating recommendations for {match_score}% match...")
        recommendations = await agent.recommend_skills(
            missing_skills,
            jd_data,
            resume_data,
            match_score
        )
        
        if recommendations:
            print(f"\n✓ Skill Recommendations successful!")
            print(f"  Generated {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n  {i}. {rec.get('missing_skill')} ({rec.get('importance').upper()})")
                print(f"     Reason: {rec.get('reason')}")
                print(f"     Time: {rec.get('estimated_time')}")
            return recommendations
        else:
            print(f"\n⚠ No recommendations generated (score: {match_score}%)")
            print("  Note: Recommendations only for 65-79% match scores")
            return []
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all agent tests."""
    print("\n" + "="*60)
    print("AI RESUME MATCHER - AGENT TESTING")
    print("="*60)
    
    # Test 1: JD Extractor
    jd_data = await test_jd_extractor()
    
    # Test 2: Resume Analyzer (optional if no PDF)
    resume_data = await test_resume_analyzer()
    
    # Test 3: Embedding Agent
    jd_embedding = await test_embedding_agent(jd_data)
    
    # Test 4: Match Evaluator
    match_result = await test_match_evaluator(jd_data, jd_embedding)
    
    # Test 5: Skill Recommender
    recommendations = await test_skill_recommender(match_result, jd_data)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  JD Extractor:      {'✓ PASS' if jd_data else '✗ FAIL'}")
    print(f"  Resume Analyzer:   {'✓ PASS' if resume_data else '⚠ SKIPPED'}")
    print(f"  Embedding Agent:   {'✓ PASS' if jd_embedding else '✗ FAIL'}")
    print(f"  Match Evaluator:   {'✓ PASS' if match_result else '✗ FAIL'}")
    print(f"  Skill Recommender: {'✓ PASS' if recommendations is not None else '✗ FAIL'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
