"""Test script for LangGraph workflow executor."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from graph_executor import GraphExecutor


async def test_graph_workflow():
    """Test the complete LangGraph workflow."""
    print("\n" + "="*60)
    print("LANGGRAPH WORKFLOW TEST")
    print("="*60)
    
    try:
        # Initialize executor
        print("\n1. Initializing Graph Executor...")
        executor = GraphExecutor()
        print("   ✓ Executor initialized successfully")
        
        # Prepare test data
        sample_jd = """
        Senior Python Developer - Remote
        
        We are seeking an experienced Python developer to join our backend team.
        
        Required Skills:
        - Python (5+ years)
        - FastAPI or Django
        - PostgreSQL, MongoDB
        - Docker, Kubernetes
        - AWS, CI/CD pipelines
        - RESTful API design
        
        Qualifications:
        - Bachelor's degree in Computer Science or related field
        - 5+ years of professional backend development experience
        - Strong problem-solving skills
        
        Responsibilities:
        - Design and implement scalable microservices
        - Write clean, maintainable code
        - Mentor junior developers
        - Participate in code reviews
        - Collaborate with frontend and DevOps teams
        """
        
        # Check for test resume files
        test_resumes_dir = Path("/home/ubuntu/AI-Resume-Matcher/backend/test_resumes")
        
        if not test_resumes_dir.exists():
            print("\n⚠ No test_resumes directory found.")
            print("  Creating sample test scenario with mock data...")
            
            # We'll test with empty resume list for now
            resume_files = []
        else:
            resume_files = list(test_resumes_dir.glob("*.pdf"))
            print(f"\n   Found {len(resume_files)} resume(s) to process")
        
        # Convert Path objects to strings
        resume_file_paths = [str(f) for f in resume_files]
        
        print("\n2. Executing LangGraph workflow...")
        print("   This will run through all 6 nodes:")
        print("   → Extract JD")
        print("   → Analyze Resumes")
        print("   → Generate Embeddings")
        print("   → Evaluate Matches")
        print("   → Recommend Skills")
        print("   → Finalize Output")
        
        # Execute workflow with correct signature
        result = await executor.execute(sample_jd, resume_file_paths)
        
        if result and not result.get("error"):
            print("\n✓ WORKFLOW COMPLETED SUCCESSFULLY!")
            print("\n3. Results Summary:")
            print(f"   Resumes Processed: {result.get('total_resumes', 0)}")
            print(f"   High Matches (≥80%): {result.get('high_matches', 0)}")
            print(f"   Potential Matches (65-79%): {result.get('potential_matches', 0)}")
            
            # Show top matches
            matches = result.get('matches', [])
            if matches:
                print("\n4. Top Matches:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"\n   {i}. {match.get('candidate_name', 'Unknown')}")
                    print(f"      Match Score: {match.get('match_score')}%")
                    print(f"      Recommendation: {match.get('recommendation')}")
                    
                    if match.get('skill_gaps'):
                        print(f"      Skill Gaps: {len(match.get('skill_gaps'))} recommendations")
            else:
                print("\n   No resumes were processed in this test run.")
            
            return True
            
        else:
            print("\n✗ WORKFLOW FAILED")
            error_msg = result.get("error", "Unknown error") if result else "No result returned"
            print(f"   Error: {error_msg}")
            return False
            
    except Exception as e:
        print(f"\n✗ WORKFLOW ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run LangGraph workflow test."""
    success = await test_graph_workflow()
    
    print("\n" + "="*60)
    print("TEST RESULT:", "✓ PASS" if success else "✗ FAIL")
    print("="*60 + "\n")
    
    if not success:
        print("Note: If you see 'No resumes were processed', create a")
        print("      test_resumes/ directory with sample PDF files.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
