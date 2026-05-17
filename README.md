# Enterprise Policy & Knowledge Assistant

A production-ready AI chatbot that answers queries using:
- Internal documents (PDF, DOCX, TXT)
- Google Drive files
- Web search fallback (DuckDuckGo)

## Tech Stack

- **Backend:** FastAPI (Python) + LangChain + Groq (chat) + HuggingFace (embeddings)
- **Vector DB:** FAISS
- **Database:** PostgreSQL (SQLAlchemy)
- **Frontend:** React + TypeScript + TailwindCSS + Vite
- **Auth:** JWT
- **Deployment:** Docker

## Project Structure

```
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── docker-compose.yml
└── README.md
```

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- [Groq API key](https://console.groq.com/keys) (free tier available)

### 1. Clone & Configure

```bash
cd ChatbotRag

# Copy and edit environment variables
cp .env.example .env

# Edit .env with your Groq API key
GROQ_API_KEY=gsk_your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
```

Embeddings run locally via HuggingFace (`sentence-transformers/all-MiniLM-L6-v2` by default). The first backend start may download the model (~90MB); no separate embedding API key is required.

### 2. Run with Docker

```bash
# Production mode
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend:** http://localhost
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 4. Create First User

```bash
# Register via API or use the frontend
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "password123", "full_name": "Admin User"}'
```

## Development Mode (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (PostgreSQL must be running)
cp .env.example .env
# Edit .env with your database URL and Groq API key (see backend/.env.example)

# Run
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## Features

### Authentication
- JWT-based auth with 30min expiration
- User registration/login
- Role-based access (admin/user)

### Document Management
- Upload PDF, DOCX, TXT files
- Automatic text extraction & chunking
- FAISS vector embeddings
- Document deletion

### RAG Chat
- Automatic query classification (internal/general)
- Document-based answers for internal queries
- Web search (DuckDuckGo) for general queries
- Source citations
- Chat history

### Google Drive Integration
- OAuth2 authentication
- Sync Drive files
- Auto-process supported file types

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/auth/me` | GET | Current user |
| `/api/v1/documents/upload` | POST | Upload document |
| `/api/v1/documents/` | GET | List documents |
| `/api/v1/query/` | POST | Ask question |
| `/api/v1/query/history` | GET | Chat history |
| `/api/v1/google-drive/files` | GET | List Drive files |
| `/api/v1/google-drive/sync/{id}` | POST | Sync Drive file |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for chat / LLM ([console.groq.com](https://console.groq.com/keys)) |
| `GROQ_MODEL` | No | Groq model id (default: `llama-3.3-70b-versatile`) |
| `HUGGINGFACE_EMBEDDING_MODEL` | No | Local embedding model (default: `sentence-transformers/all-MiniLM-L6-v2`) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT secret key |
| `GOOGLE_DRIVE_CREDENTIALS_PATH` | No | Path to Google credentials.json |

## Groq Setup

1. Sign up at [Groq Console](https://console.groq.com/).
2. Create an API key under **API Keys**.
3. Set `GROQ_API_KEY` in `.env` (Docker) or `backend/.env` (local dev).
4. Optionally change `GROQ_MODEL` — see [supported models](https://console.groq.com/docs/models).

Chat responses use Groq; document embeddings use HuggingFace locally and do not consume Groq quota.

## Google Drive Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to `backend/credentials.json`
5. First run will prompt for browser authentication

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

### Groq API Errors
- Verify `GROQ_API_KEY` is set correctly in `.env` or `backend/.env`
- Confirm the key is active at [console.groq.com](https://console.groq.com/keys)
- Check rate limits on the free tier; try a different `GROQ_MODEL` if a model is deprecated

### Embedding / HuggingFace Issues
- First run downloads the embedding model; ensure disk space and network access
- Set `HUGGINGFACE_EMBEDDING_MODEL` in `backend/.env` to use another [Sentence Transformers](https://huggingface.co/sentence-transformers) model
- If you changed the embedding model, delete `data/faiss_index` and re-upload documents (vector dimension must match)

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## License

MIT
