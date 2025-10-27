# Enterprise AI Resume Matcher

> **Autonomous resume-to-job-description matching with 80%+ similarity detection and intelligent skill gap recommendations**

A production-ready, multi-agent AI system built with LangGraph orchestration, featuring specialized agents for job description parsing, resume analysis, semantic matching, and skill recommendations.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.0-green)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.1.0-black)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0.1-purple)](https://github.com/langchain-ai/langgraph)

---

## 🎯 Features

### Core Capabilities
- **Multi-Agent Architecture**: 5 specialized AI agents orchestrated by LangGraph
- **Smart Matching**: Weighted scoring algorithm (40% skills, 30% experience, 30% role fit)
- **Semantic Search**: Gemini text-embedding-004 with 768-dimensional vectors
- **Batch Processing**: Handle up to 50 resumes per request
- **Intelligent Recommendations**: Automated skill gap analysis with learning paths

### Technical Highlights
- **Async/Await**: Fully asynchronous Python backend for optimal performance
- **Enterprise Databases**: Pinecone serverless + MongoDB Atlas integration
- **Advanced PDF Parsing**: Unstructured library with OCR support
- **Modern Frontend**: Next.js 15 with React 19 and Tailwind CSS
- **Production Ready**: Docker containerization with health checks

---

## 🏗️ Architecture

### Five-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                     LangGraph Orchestrator                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ JD Extractor │──▶│Resume Analyzer│──▶│Embedding Agent│   │
│  │  (Gemini)    │   │  (OpenRouter)│   │   (Gemini)    │   │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         │                   │                    │           │
│         └───────────────────┴────────────────────┘          │
│                           │                                  │
│                           ▼                                  │
│                  ┌──────────────────┐                       │
│                  │ Match Evaluator  │                       │
│                  │ (scikit-learn)   │                       │
│                  └──────────────────┘                       │
│                           │                                  │
│                           ▼                                  │
│                  ┌──────────────────┐                       │
│                  │Skill Recommender │                       │
│                  │    (Gemini)      │                       │
│                  └──────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Agent Details

1. **JD Extractor Agent** (`jd_extractor.py`)
   - LLM: Gemini 2.5 Flash
   - Extracts: job_title, required_skills, experience_years, qualifications, responsibilities
   - Retry logic: 3 attempts with JSON parsing

2. **Resume Analyzer Agent** (`resume_analyzer.py`)
   - Parser: Unstructured (hi_res strategy with OCR)
   - LLM: OpenRouter GPT-4 Turbo
   - Extracts: candidate_name, email, skills, experience_years, work_history, education

3. **Embedding Agent** (`embedding_agent.py`)
   - Model: Gemini text-embedding-004
   - Dimension: 768
   - Combines multiple fields for rich context

4. **Match Evaluator Agent** (`match_evaluator.py`)
   - Algorithm: Weighted scoring (40/30/30)
   - Skills: Intersection-based matching
   - Experience: Ratio with cap at 100%
   - Role: Cosine similarity of embeddings

5. **Skill Recommender Agent** (`skill_recommender.py`)
   - Activation: 65-79% match scores
   - Output: Top 5 recommendations with learning paths
   - Fields: importance, reason, estimated_time

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (optional)
- **API Keys**:
  - Google Gemini API Key
  - OpenRouter API Key
  - Pinecone API Key
  - MongoDB Atlas URI

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd AI-Resume-Matcher

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

#### Option 2: Manual Setup

**Backend Setup:**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libmagic1 poppler-utils tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend Setup:**

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
npm start
```

---

## ⚙️ Configuration

### Backend Environment Variables

```bash
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Databases
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=resume-jd-matcher
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=resume_system

# Server
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📖 API Documentation

### Endpoints

#### `POST /api/match`

Match resumes to job description.

**Request:**
- `Content-Type: multipart/form-data`
- `jd_text` (string): Job description text
- `files` (File[]): PDF resume files (max 50, 10MB each)

**Response:**
```json
{
  "matches": [
    {
      "resume_id": "resume_1",
      "candidate_name": "John Doe",
      "match_score": 87.50,
      "skill_match_score": 90.00,
      "experience_match_score": 85.00,
      "role_match_score": 87.50,
      "matched_skills": ["Python", "FastAPI", "MongoDB"],
      "missing_skills": ["Docker", "Kubernetes"],
      "skill_gaps": [],
      "recommendation": "Highly recommended - Strong match across all criteria"
    }
  ],
  "total_resumes": 10,
  "high_matches": 3,
  "potential_matches": 5
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-resume-matcher",
  "version": "1.0.0"
}
```

#### `GET /api/statistics`

Get aggregate statistics from MongoDB.

#### `GET /api/history?limit=10&skip=0`

Retrieve match history with pagination.

---

## 🎨 Frontend Usage

1. **Enter Job Description**: Paste the job posting in the text area
2. **Upload Resumes**: Select multiple PDF resume files (max 50)
3. **Submit**: Click "Match Resumes" to start processing
4. **View Results**: See color-coded match cards:
   - **Green (≥80%)**: High matches - Recommended candidates
   - **Yellow (65-79%)**: Potential matches - With skill gap recommendations
   - **Red (<65%)**: Not recommended

---

## 🔬 Development

### Project Structure

```
AI-Resume-Matcher/
├── backend/
│   ├── agents/
│   │   ├── jd_extractor.py
│   │   ├── resume_analyzer.py
│   │   ├── embedding_agent.py
│   │   ├── match_evaluator.py
│   │   └── skill_recommender.py
│   ├── services/
│   │   ├── pinecone_service.py
│   │   └── mongodb_service.py
│   ├── models/
│   │   └── schemas.py
│   ├── graph_executor.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── UploadSection.tsx
│   │   └── ResultsView.tsx
│   ├── types/
│   │   └── index.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
cd backend
pytest tests/ -v --cov=agents --cov=services
```

### Code Quality

```bash
# Python linting
black backend/
flake8 backend/

# TypeScript linting
cd frontend
npm run lint
```

---

## 📊 Scoring Algorithm

The system uses a weighted formula to calculate match scores:

```
Overall Score = (Skill Match × 0.40) + 
                (Experience Match × 0.30) + 
                (Role Similarity × 0.30)
```

- **Skill Match**: `len(matched_skills) / len(required_skills) × 100`
- **Experience Match**: `min(resume_exp / jd_exp, 1.0) × 100`
- **Role Similarity**: `cosine_similarity(embeddings) × 100`

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | FastAPI | 0.119.0 |
| Orchestration | LangGraph | 1.0.1 |
| Multi-Agent | CrewAI | 0.86.0 |
| LLM (Primary) | Google Gemini | 2.5 Flash |
| LLM (Secondary) | OpenRouter GPT-4 | Turbo |
| Vector DB | Pinecone | 5.0.1 |
| Metadata DB | MongoDB | 4.10.0 |
| PDF Parser | Unstructured | 0.16.0 |
| ML Library | scikit-learn | 1.5.0 |
| Frontend Framework | Next.js | 15.1.0 |
| UI Library | React | 19.0.0 |
| Styling | Tailwind CSS | 3.4.0 |

---

## 🔒 Security Considerations

- **API Keys**: Never commit `.env` files to version control
- **File Validation**: Only PDF files accepted, max 10MB per file
- **CORS**: Configure `ALLOWED_ORIGINS` for production
- **Rate Limiting**: Implement rate limiting in production environments
- **Input Sanitization**: All user inputs are validated before processing

---

## 🐛 Troubleshooting

### Common Issues

**1. PDF Parsing Fails**
```bash
# Ensure system dependencies are installed
sudo apt-get install poppler-utils tesseract-ocr libmagic1
```

**2. Pinecone Connection Error**
```bash
# Verify API key and environment in .env
# Check if index exists or create it manually
```

**3. MongoDB Connection Timeout**
```bash
# Verify MongoDB URI format
# Check network connectivity and whitelist IP in Atlas
```

**4. Frontend Can't Connect to Backend**
```bash
# Update NEXT_PUBLIC_API_URL in frontend/.env.local
# Ensure backend is running on specified port
```

---

## 📈 Performance

- **Processing Time**: ~5-10 seconds per resume
- **Batch Capacity**: Up to 50 resumes per request
- **Embedding Dimension**: 768 (optimized for speed/accuracy)
- **API Timeout**: 5 minutes for large batches

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **LangGraph** for workflow orchestration
- **Google Gemini** for embeddings and extraction
- **OpenRouter** for resume parsing
- **Unstructured** for PDF processing
- **Pinecone** for vector search
- **MongoDB** for data persistence

---

## 📧 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ using cutting-edge AI technology**