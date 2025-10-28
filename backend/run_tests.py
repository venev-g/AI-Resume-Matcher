"""Run all backend tests with coverage reporting."""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Execute all test suites with coverage."""
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests"
    
    if not tests_dir.exists():
        print("❌ Tests directory not found!")
        return 1
    
    print("=" * 70)
    print("🧪 Running AI Resume Matcher Backend Tests")
    print("=" * 70)
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        str(tests_dir),
        "-v",  # Verbose output
        "--cov=.",  # Coverage for all backend code
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # Generate HTML report
        "--cov-fail-under=80",  # Require 80% coverage
        "-s",  # Don't capture stdout (for debugging)
        "--tb=short",  # Shorter traceback format
        "--maxfail=5"  # Stop after 5 failures
    ]
    
    try:
        result = subprocess.run(cmd, cwd=backend_dir)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("✅ All tests passed!")
            print("=" * 70)
            print(f"\n📊 Coverage report generated: {backend_dir / 'htmlcov' / 'index.html'}")
        else:
            print("\n" + "=" * 70)
            print("❌ Some tests failed!")
            print("=" * 70)
        
        return result.returncode
    
    except FileNotFoundError:
        print("❌ pytest not found! Install dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return 130


def run_specific_suite(suite_name: str):
    """Run a specific test suite."""
    backend_dir = Path(__file__).parent
    test_file = backend_dir / "tests" / f"test_{suite_name}.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print(f"🧪 Running {suite_name} tests...")
    
    cmd = [
        "pytest",
        str(test_file),
        "-v",
        "-s"
    ]
    
    result = subprocess.run(cmd, cwd=backend_dir)
    return result.returncode


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test suite
        suite_name = sys.argv[1]
        return run_specific_suite(suite_name)
    else:
        # Run all tests
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
