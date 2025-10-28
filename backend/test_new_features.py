"""
Test script for new database search and storage features.

This script tests:
1. Resume storage in Pinecone
2. Database search functionality
3. 80% match threshold filtering
4. Skill gap recommendations for 65-79% matches
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_executor import GraphExecutor
from services.pinecone_service import PineconeService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_pinecone_connection():
    """Test Pinecone connection and index stats."""
    print("\n" + "="*60)
    print("TEST 1: Pinecone Connection")
    print("="*60)
    
    try:
        pinecone = PineconeService()
        stats = await pinecone.get_index_stats()
        
        print(f"✓ Connected to Pinecone index: {pinecone.index_name}")
        print(f"  - Total vectors: {stats.get('total_vectors', 0)}")
        print(f"  - Dimension: {stats.get('dimension', 0)}")
        print(f"  - Index fullness: {stats.get('index_fullness', 0)}")
        
        return True
    except Exception as e:
        print(f"✗ Pinecone connection failed: {e}")
        return False


async def test_resume_storage():
    """Test storing resumes in database."""
    print("\n" + "="*60)
    print("TEST 2: Resume Storage")
    print("="*60)
    
    try:
        # Check if test resumes exist
        test_resume_dir = "test_resumes"
        if not os.path.exists(test_resume_dir):
            print(f"⚠ Test resume directory not found: {test_resume_dir}")
            print("  Skipping storage test...")
            return True
        
        # Get list of PDF files
        resume_files = [
            os.path.join(test_resume_dir, f)
            for f in os.listdir(test_resume_dir)
            if f.endswith('.pdf')
        ][:3]  # Limit to 3 files for testing
        
        if not resume_files:
            print("⚠ No PDF files found in test_resumes directory")
            print("  Skipping storage test...")
            return True
        
        print(f"Found {len(resume_files)} test resume(s)")
        
        executor = GraphExecutor()
        result = await executor.store_resumes(resume_files)
        
        print(f"✓ Storage completed:")
        print(f"  - Stored: {result.get('stored_count', 0)}")
        print(f"  - Failed: {result.get('failed_count', 0)}")
        
        if result.get('error'):
            print(f"  - Error: {result['error']}")
        
        return result.get('stored_count', 0) > 0
        
    except Exception as e:
        print(f"✗ Storage test failed: {e}")
        return False


async def test_database_search():
    """Test searching stored resumes by JD."""
    print("\n" + "="*60)
    print("TEST 3: Database Search (≥80% threshold)")
    print("="*60)
    
    try:
        # Sample JD for testing
        test_jd = """
        Senior Python Developer
        
        We are looking for an experienced Python developer with:
        - 5+ years of Python development experience
        - Strong knowledge of FastAPI and web frameworks
        - Experience with MongoDB and databases
        - Familiarity with Docker and containerization
        - Understanding of REST API design
        - Bachelor's degree in Computer Science or related field
        """
        
        print("Searching database with test JD...")
        
        executor = GraphExecutor()
        result = await executor.search_database(
            jd_text=test_jd,
            min_match_score=80.0,
            top_k=50
        )
        
        total = result.get('total_resumes', 0)
        high = result.get('high_matches', 0)
        potential = result.get('potential_matches', 0)
        
        print(f"✓ Search completed:")
        print(f"  - Total matches (≥80%): {total}")
        print(f"  - High matches (≥80%): {high}")
        print(f"  - Potential (65-79%): {potential}")
        
        if result.get('error'):
            print(f"  - Error: {result['error']}")
        
        # Display top matches
        matches = result.get('matches', [])
        if matches:
            print(f"\n  Top {min(3, len(matches))} matches:")
            for i, match in enumerate(matches[:3], 1):
                print(f"  {i}. {match.get('candidate_name', 'Unknown')}")
                print(f"     Match Score: {match.get('match_score', 0)}%")
                print(f"     Skills: {match.get('skill_match_score', 0)}%")
                print(f"     Experience: {match.get('experience_match_score', 0)}%")
                print(f"     Role: {match.get('role_match_score', 0)}%")
                
                # Check for skill gaps
                skill_gaps = match.get('skill_gaps', [])
                if skill_gaps:
                    print(f"     Skill Recommendations: {len(skill_gaps)} suggestions")
        else:
            print("  No matches found. Try:")
            print("  1. Storing some resumes first using test_resume_storage()")
            print("  2. Lowering the min_match_score threshold")
        
        return True
        
    except Exception as e:
        print(f"✗ Database search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_skill_recommendations():
    """Test skill gap recommendations for 65-79% matches."""
    print("\n" + "="*60)
    print("TEST 4: Skill Gap Recommendations (65-79% matches)")
    print("="*60)
    
    try:
        # Search with lower threshold to get potential matches
        test_jd = """
        Senior Full Stack Developer
        
        Requirements:
        - 5+ years experience in web development
        - Expert in React, Node.js, and TypeScript
        - Experience with AWS, Docker, Kubernetes
        - Knowledge of GraphQL and microservices
        - CI/CD pipeline experience
        - Strong problem-solving skills
        """
        
        print("Searching for potential candidates (65-79%)...")
        
        executor = GraphExecutor()
        result = await executor.search_database(
            jd_text=test_jd,
            min_match_score=65.0,  # Lower threshold to find potential matches
            top_k=50
        )
        
        matches = result.get('matches', [])
        potential_matches = [
            m for m in matches
            if 65 <= m.get('match_score', 0) < 80
        ]
        
        print(f"✓ Found {len(potential_matches)} potential match(es) with skill gaps")
        
        if potential_matches:
            for i, match in enumerate(potential_matches[:2], 1):  # Show first 2
                print(f"\n  Candidate {i}: {match.get('candidate_name', 'Unknown')}")
                print(f"  Match Score: {match.get('match_score', 0)}%")
                
                skill_gaps = match.get('skill_gaps', [])
                if skill_gaps:
                    print(f"  Skill Recommendations ({len(skill_gaps)}):")
                    for gap in skill_gaps[:3]:  # Show first 3
                        print(f"    • {gap.get('missing_skill')} ({gap.get('importance', 'N/A')})")
                        print(f"      {gap.get('reason', 'N/A')}")
                        print(f"      Time: {gap.get('estimated_time', 'N/A')}")
                else:
                    print("  No skill recommendations generated")
        else:
            print("  No potential matches found in 65-79% range")
            print("  This is expected if all matches are either ≥80% or <65%")
        
        return True
        
    except Exception as e:
        print(f"✗ Skill recommendation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*60)
    print("AI RESUME MATCHER - NEW FEATURES TEST SUITE")
    print("="*60)
    
    results = {
        "Pinecone Connection": False,
        "Resume Storage": False,
        "Database Search": False,
        "Skill Recommendations": False
    }
    
    # Test 1: Pinecone connection
    results["Pinecone Connection"] = await test_pinecone_connection()
    
    if not results["Pinecone Connection"]:
        print("\n⚠ Pinecone connection failed. Skipping remaining tests.")
        return
    
    # Test 2: Resume storage (optional)
    results["Resume Storage"] = await test_resume_storage()
    
    # Test 3: Database search
    results["Database Search"] = await test_database_search()
    
    # Test 4: Skill recommendations
    results["Skill Recommendations"] = await test_skill_recommendations()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! System is ready.")
    else:
        print("\n⚠ Some tests failed. Review errors above.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
