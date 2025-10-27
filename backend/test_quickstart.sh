#!/bin/bash

# Quick Start Script for Testing AI Resume Matcher Backend
# This script guides you through testing all components

echo "=============================================================="
echo "  AI RESUME MATCHER - BACKEND TESTING QUICK START"
echo "=============================================================="
echo ""

# Check if in backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the backend directory"
    echo "  cd backend && bash test_quickstart.sh"
    exit 1
fi

# Step 1: Check dependencies
echo "Step 1: Checking Python dependencies..."
python3 -c "import fastapi, google.genai, pinecone, pymongo" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Dependencies not installed. Installing now..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "✗ Failed to install dependencies"
        exit 1
    fi
    echo "✓ Dependencies installed successfully"
else
    echo "✓ All dependencies installed"
fi

# Step 2: Check environment variables
echo ""
echo "Step 2: Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "✗ .env file not found"
    echo "  Copy .env.example to .env and add your API keys"
    exit 1
fi

if grep -q "your_api_key_here" .env 2>/dev/null; then
    echo "⚠ Warning: .env file contains placeholder values"
    echo "  Please add real API keys before running tests"
fi
echo "✓ .env file found"

# Step 3: Create test resumes directory
echo ""
echo "Step 3: Setting up test environment..."
mkdir -p test_resumes
echo "✓ test_resumes directory ready"
echo "  Tip: Add sample PDF resumes to test_resumes/ for full testing"

# Step 4: Test selection menu
echo ""
echo "=============================================================="
echo "  SELECT TEST TO RUN"
echo "=============================================================="
echo ""
echo "1. Test Individual Agents (recommended first)"
echo "2. Test LangGraph Workflow"
echo "3. Test FastAPI Server (requires server running)"
echo "4. Run All Tests"
echo "5. Start FastAPI Server"
echo "6. Exit"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "Running Individual Agent Tests..."
        python3 test_agents.py
        ;;
    2)
        echo ""
        echo "Running LangGraph Workflow Test..."
        python3 test_langgraph.py
        ;;
    3)
        echo ""
        echo "Testing FastAPI Server..."
        echo "Make sure the server is running in another terminal:"
        echo "  uvicorn main:app --reload"
        echo ""
        read -p "Press Enter when server is ready..."
        python3 test_fastapi.py
        ;;
    4)
        echo ""
        echo "Running All Tests..."
        python3 run_all_tests.py
        ;;
    5)
        echo ""
        echo "Starting FastAPI Server..."
        echo "Server will start on http://localhost:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "=============================================================="
echo "  Test completed!"
echo "=============================================================="
echo ""
echo "Next steps:"
echo "  - Review TESTING.md for detailed testing guide"
echo "  - Check logs for any errors"
echo "  - Run other test suites"
echo ""
