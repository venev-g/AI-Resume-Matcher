---
applyTo:
  - "Dockerfile"
  - "docker-compose.yml"
  - ".github/workflows/**/*.yml"
---

# Deployment Configuration Instructions

## Docker Configuration

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

# System dependencies for PDF processing
RUN apt-get update && apt-get install -y \\
    libmagic1 \\
    poppler-utils \\
    tesseract-ocr \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy application
COPY . .

# Build Next.js app
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### Docker Compose
- Use **environment files** (.env) for secrets
- Define **named volumes** for persistent data
- Set up **networks** for service isolation
- Add **health checks** for all services
- Use **restart: unless-stopped** for production

## Environment Management

### Production .env
```bash
# Never commit this file!
# Use secret management (AWS Secrets Manager, etc.)

# API Keys
GEMINI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
PINECONE_API_KEY=...

# Database URLs
MONGODB_URI=mongodb+srv://...
PINECONE_INDEX_NAME=resume-matcher-prod

# Server Config
API_HOST=0.0.0.0
API_PORT=8000
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.yourapp.com
```

## Deployment Platforms

### Vercel (Frontend)
- **next.config.ts**: Configure output: 'standalone' for optimal bundle
- **Environment Variables**: Set in Vercel dashboard
- **Build Command**: npm run build
- **Output Directory**: .next
- Enable **Edge Functions** for global distribution

### AWS Lambda (Backend)
- Use **Mangum** adapter for FastAPI
- Set **timeout** to 30s minimum (LLM calls)
- Allocate **1024MB+ memory** for PDF processing
- Use **Lambda Layers** for dependencies
- Configure **VPC** for MongoDB access (if needed)

### Render (Backend Alternative)
- **Build Command**: pip install -r requirements.txt
- **Start Command**: uvicorn main:app --host 0.0.0.0 --port $PORT
- Set **environment variables** in dashboard
- Enable **auto-deploy** from main branch

## CI/CD with GitHub Actions

### Example Workflow
```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST "https://api.render.com/v1/services/$SERVICE_ID/deploys"
```

## Security Checklist
- ✅ API keys in environment variables (not code)
- ✅ CORS configured with specific origins
- ✅ HTTPS enforced for all external APIs
- ✅ Rate limiting enabled
- ✅ Input validation on all endpoints
- ✅ File upload size limits (10MB max)
- ✅ Error messages don't expose internals
- ✅ Dependencies regularly updated

## Monitoring & Logging
- Use **structured logging** (JSON format)
- Send logs to **centralized service** (CloudWatch, Datadog)
- Monitor **API response times**
- Track **LLM API usage** (stay within quotas)
- Set up **error alerting** (Sentry, etc.)
- Monitor **database connection pools**