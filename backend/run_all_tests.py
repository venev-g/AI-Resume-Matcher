"""Master test runner for AI Resume Matcher backend."""

import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def run_test(test_name, test_script):
    """Run a test script and return success status."""
    print_header(f"Running: {test_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_script],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_name}: {e}")
        return False


def main():
    """Run all tests in sequence."""
    print_header("AI RESUME MATCHER - COMPREHENSIVE TEST SUITE")
    
    print("This test suite will validate:")
    print("  1. Individual AI Agents (5 agents)")
    print("  2. LangGraph Workflow Orchestration")
    print("  3. FastAPI Server Endpoints (4 endpoints)")
    print("\nNote: Make sure to install dependencies first:")
    print("  pip install -r requirements.txt")
    print("\nFor FastAPI tests, start the server in another terminal:")
    print("  cd backend && uvicorn main:app --reload")
    input("\nPress Enter to continue...")
    
    tests = [
        ("Individual Agent Tests", "test_agents.py"),
        ("LangGraph Workflow Test", "test_langgraph.py"),
        ("FastAPI Server Tests", "test_fastapi.py")
    ]
    
    results = {}
    
    for test_name, test_script in tests:
        success = run_test(test_name, test_script)
        results[test_name] = success
        
        if not success:
            print(f"\n⚠ {test_name} had failures. Continue? (y/n): ", end="")
            response = input().strip().lower()
            if response != 'y':
                break
    
    # Final summary
    print_header("FINAL TEST SUMMARY")
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    print(f"  OVERALL: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
