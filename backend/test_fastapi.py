"""Test script for FastAPI server endpoints."""

import asyncio
import requests
import time
from pathlib import Path
import sys


def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Health check successful!")
            print(f"  Status: {data.get('status')}")
            print(f"  Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"\n✗ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server at http://localhost:8000")
        print("  Make sure the server is running with:")
        print("  cd backend && uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def test_match_endpoint():
    """Test the match endpoint with sample data."""
    print("\n" + "="*60)
    print("TEST 2: Match Endpoint")
    print("="*60)
    
    try:
        # Prepare sample JD
        jd_text = """
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
        """
        
        # Check for test resumes
        test_resumes_dir = Path("/home/ubuntu/AI-Resume-Matcher/backend/test_resumes")
        resume_files = []
        
        if test_resumes_dir.exists():
            resume_files = list(test_resumes_dir.glob("*.pdf"))[:5]  # Max 5 for testing
        
        if not resume_files:
            print("\n⚠ No test resumes found. Testing with JD only...")
            print("  Create test_resumes/ directory with PDF files for full test.")
        
        # Prepare multipart form data
        data = {"jd_text": jd_text}
        files = []
        
        for resume_file in resume_files:
            files.append(("resumes", (resume_file.name, open(resume_file, "rb"), "application/pdf")))
        
        print(f"\nSending request with {len(resume_files)} resume(s)...")
        print("This may take 30-60 seconds depending on LLM API response times...")
        
        response = requests.post(
            "http://localhost:8000/api/match",
            data=data,
            files=files,
            timeout=120
        )
        
        # Close file handles
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Match request successful!")
            print(f"\n  Results:")
            print(f"    Total Resumes: {result.get('total_resumes', 0)}")
            print(f"    High Matches (≥80%): {result.get('high_matches', 0)}")
            print(f"    Potential Matches (65-79%): {result.get('potential_matches', 0)}")
            print(f"    Execution Time: {result.get('execution_time', 'N/A')}")
            
            # Show top matches
            matches = result.get('matches', [])
            if matches:
                print(f"\n  Top {min(3, len(matches))} Matches:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"\n    {i}. {match.get('candidate_name', 'Unknown')}")
                    print(f"       Score: {match.get('match_score')}%")
                    print(f"       Matched Skills: {len(match.get('matched_skills', []))}")
                    print(f"       Missing Skills: {len(match.get('missing_skills', []))}")
            else:
                print("\n  No matches returned (no resumes processed)")
            
            return True
            
        else:
            print(f"\n✗ Match request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out after 120 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server at http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics_endpoint():
    """Test the statistics endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Statistics Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/api/statistics", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Statistics request successful!")
            print(f"  Total Jobs Processed: {data.get('total_jobs_processed', 0)}")
            print(f"  Total Resumes Analyzed: {data.get('total_resumes_analyzed', 0)}")
            print(f"  Average Match Score: {data.get('average_match_score', 'N/A')}")
            return True
        else:
            print(f"\n✗ Statistics request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def test_history_endpoint():
    """Test the history endpoint."""
    print("\n" + "="*60)
    print("TEST 4: History Endpoint")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/api/history?limit=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            print(f"\n✓ History request successful!")
            print(f"  Records returned: {len(history)}")
            
            if history:
                print(f"\n  Recent matches:")
                for i, record in enumerate(history[:3], 1):
                    print(f"    {i}. Job: {record.get('jd_data', {}).get('job_title', 'Unknown')}")
                    print(f"       Timestamp: {record.get('timestamp', 'N/A')}")
                    print(f"       Resumes: {record.get('total_resumes', 0)}")
            else:
                print("  No history records found (database may be empty)")
            
            return True
        else:
            print(f"\n✗ History request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def main():
    """Run all FastAPI tests."""
    print("\n" + "="*60)
    print("FASTAPI SERVER TESTING")
    print("="*60)
    print("\nNote: Make sure the server is running with:")
    print("  cd backend && uvicorn main:app --reload")
    print("\nWaiting 3 seconds before starting tests...")
    time.sleep(3)
    
    # Run tests
    results = {
        "Health Check": test_health_endpoint(),
        "Match Endpoint": test_match_endpoint(),
        "Statistics": test_statistics_endpoint(),
        "History": test_history_endpoint()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("="*60)
    print(f"\nOVERALL: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
