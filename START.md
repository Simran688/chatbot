# Project Setup & Validation Guide

## Code Validation Summary

All 10 steps have been implemented with production-ready code:

| Component | Files Created | Status |
|-----------|--------------|--------|
| Backend Core | 15+ Python files | ✅ Valid |
| Frontend React | 12+ TSX/TS files | ✅ Valid |
| Database Models | User, Document, ChatHistory | ✅ Valid |
| API Routes | Auth, Documents, Query, Google Drive | ✅ Valid |
| Services | RAG Pipeline (Groq), Web Search, Embeddings (HuggingFace) | ✅ Valid |
| Docker Config | 6 config files | ✅ Valid |

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Docker Desktop** installed (Windows/Mac) OR Docker + Docker Compose (Linux)
- [ ] **Groq API Key** from https://console.groq.com/keys (free tier)
- [ ] Git (optional, for cloning)
- [ ] 4GB+ free RAM
- [ ] Ports 80, 8000, 5432 available

---

## Quick Start (Recommended)

### Step 1: Environment Setup (2 minutes)

```bash
# Navigate to project
cd c:\project\ChatbotRag

# Create environment file
copy .env.example .env

# Edit .env with your Groq key
notepad .env
```

**Required in `.env`:**
```env
GROQ_API_KEY=gsk_your-actual-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
SECRET_KEY=your-super-secret-key-here
```

Embeddings use HuggingFace locally (`sentence-transformers/all-MiniLM-L6-v2`). No embedding API key is required; the first backend start may download ~90MB of model weights.

### Step 2: Launch with Docker (5 minutes)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

**First run will:**
1. Download PostgreSQL, Python, Node images
2. Install all dependencies (including PyTorch + sentence-transformers for embeddings)
3. Create database tables automatically
4. Build frontend production bundle
5. Download the HuggingFace embedding model on first document upload or query (one-time)

### Step 3: Verify Installation

| Service | URL | Expected Result |
|---------|-----|-----------------|
| Frontend | http://localhost | Login page loads |
| API Health | http://localhost:8000/health | `{"status": "healthy"}` |
| API Docs | http://localhost:8000/docs | Swagger UI loads |

### Step 4: Create First User

Via web UI:
1. Go to http://localhost
2. Click "Sign up"
3. Register with email/password

Or via API:
```bash
curl -X POST "http://localhost/api/v1/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"admin@company.com\", \"password\": \"password123\", \"full_name\": \"Admin User\"}"
```

---

## Development Mode (Without Docker)

### Backend Only

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
copy .env.example .env
# Edit .env: Set DATABASE_URL and GROQ_API_KEY

# 4. Ensure PostgreSQL is running locally

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

**Verify:** http://localhost:8000/docs

### Frontend Only

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
```

**Verify:** http://localhost:5173

---

## Testing the Application

### Test 1: Upload a Document

1. Login at http://localhost
2. Navigate to "Documents"
3. Click "Upload Document"
4. Select a PDF or DOCX file
5. Wait for processing (chunks created)

### Test 2: Ask a Question

1. Go to "Chat"
2. Ask: "What is in the document I just uploaded?"
3. View response with sources

### Test 3: Web Search

Ask: "Who won the FIFA World Cup 2022?"
- Should use web search (DuckDuckGo)
- Shows "Web search used" indicator

---

## Troubleshooting

### Issue: Docker fails to start

```bash
# Check what's running on ports
netstat -ano | findstr :80
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Stop existing containers
docker-compose down

# Clean start
docker-compose down -v
docker-compose up --build
```

### Issue: "Cannot connect to database"

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Wait for DB to be ready before backend starts
# (docker-compose.yml has healthcheck configured)
```

### Issue: "Groq API error" or chat returns errors

- Verify `GROQ_API_KEY` in `.env` (Docker) or `backend/.env` (local dev)
- Confirm the key is active at https://console.groq.com/keys
- Key format: `gsk_...`
- Try another `GROQ_MODEL` if a model was deprecated (see https://console.groq.com/docs/models)

### Issue: Embeddings slow or fail on first run

- First run downloads `sentence-transformers/all-MiniLM-L6-v2` (~90MB); ensure network access
- If you migrated from OpenAI embeddings, delete `backend/data/faiss_index` and re-upload documents (vector size changed from 1536 to 384)

### Issue: Frontend shows "Failed to fetch"

- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Vite proxy is configured in `vite.config.ts`

### Issue: Google Drive sync fails

1. Create project at https://console.cloud.google.com/
2. Enable Google Drive API
3. Create OAuth 2.0 Desktop credentials
4. Download `credentials.json` to `backend/credentials.json`
5. Restart: `docker-compose restart backend`

---

## File Structure Validation

Run this to verify all files exist:

```bash
# Backend check
dir backend\app\api\routes\
dir backend\app\services\
dir backend\app\models\
dir backend\app\schemas\
dir backend\app\core\
dir backend\app\db\

# Frontend check
dir frontend\src\pages
dir frontend\src\components
dir frontend\src\contexts
dir frontend\src\lib
dir frontend\src\types

# Docker check
if exist docker-compose.yml echo "✅ docker-compose.yml exists"
if exist backend\Dockerfile echo "✅ Backend Dockerfile exists"
if exist frontend\Dockerfile echo "✅ Frontend Dockerfile exists"
```

---

## API Endpoints Reference

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/auth/register` | POST | No | Create account |
| `/api/v1/auth/login` | POST | No | Get JWT token |
| `/api/v1/auth/me` | GET | Yes | Current user info |
| `/api/v1/documents/upload` | POST | Yes | Upload PDF/DOCX |
| `/api/v1/documents/` | GET | Yes | List documents |
| `/api/v1/documents/{id}` | DELETE | Yes | Delete document |
| `/api/v1/query/` | POST | Yes | Ask question |
| `/api/v1/query/history` | GET | Yes | Chat history |
| `/api/v1/google-drive/files` | GET | Yes | List Drive files |
| `/api/v1/google-drive/sync/{id}` | POST | Yes | Sync Drive file |
| `/health` | GET | No | Health check |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | - | Groq API key for chat / LLM |
| `GROQ_MODEL` | ❌ No | `llama-3.3-70b-versatile` | Groq model id |
| `HUGGINGFACE_EMBEDDING_MODEL` | ❌ No | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `DATABASE_URL` | ✅ Yes (Docker) | Auto-set | PostgreSQL connection |
| `SECRET_KEY` | ✅ Yes | - | JWT signing key |
| `GOOGLE_DRIVE_CREDENTIALS_PATH` | ❌ No | - | Google OAuth credentials |

---

## Next Steps After Setup

1. **Upload Documents**: Start with company policies, HR docs
2. **Test Queries**: Try internal and general questions
3. **Configure Google Drive**: Optional integration
4. **Create Admin User**: Use for user management
5. **Production Deploy**: Use cloud PostgreSQL, secure secrets

---

## Support

- API Docs: http://localhost:8000/docs (when running)
- Backend logs: `docker-compose logs -f backend`
- Frontend logs: `docker-compose logs -f frontend`
- Database logs: `docker-compose logs -f postgres`
