#!/bin/bash

# Quick Test Commands Reference
# ==============================

echo "🧪 AI Resume Matcher - Quick Test Commands"
echo "=========================================="
echo ""

# Install dependencies
echo "📦 Install Test Dependencies:"
echo "  pip install -r requirements.txt"
echo ""

# Run all tests
echo "🚀 Run All Tests:"
echo "  python run_tests.py"
echo "  pytest tests/ -v"
echo ""

# Run with coverage
echo "📊 Run with Coverage Report:"
echo "  pytest tests/ -v --cov=. --cov-report=html"
echo "  pytest tests/ --cov=. --cov-report=term-missing"
echo ""

# Run specific test files
echo "🎯 Run Specific Test Suites:"
echo "  python run_tests.py jd_extractor"
echo "  python run_tests.py resume_analyzer"
echo "  python run_tests.py embedding_agent"
echo "  python run_tests.py match_evaluator"
echo "  python run_tests.py skill_recommender"
echo "  python run_tests.py pinecone_service"
echo "  python run_tests.py mongodb_service"
echo "  python run_tests.py graph_executor"
echo "  python run_tests.py api"
echo "  python run_tests.py integration"
echo ""

# Run specific test
echo "🔍 Run Specific Test Method:"
echo "  pytest tests/test_match_evaluator.py::TestMatchEvaluator::test_weighted_scoring_formula -v"
echo ""

# Debugging options
echo "🐛 Debugging Options:"
echo "  pytest tests/ -v -s                    # Show print statements"
echo "  pytest tests/ -v --tb=long            # Detailed tracebacks"
echo "  pytest tests/ -x                      # Stop at first failure"
echo "  pytest tests/ --maxfail=3             # Stop after 3 failures"
echo ""

# Performance
echo "⚡ Performance Testing:"
echo "  pytest tests/ --durations=10          # Show 10 slowest tests"
echo ""

# View coverage report
echo "📈 View Coverage Report:"
echo "  open htmlcov/index.html               # macOS"
echo "  xdg-open htmlcov/index.html           # Linux"
echo "  start htmlcov/index.html              # Windows"
echo ""

echo "✅ For detailed testing documentation, see:"
echo "   - backend/tests/README.md"
echo "   - backend/TESTING_SUMMARY.md"
