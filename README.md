# Enterprise Policy & Knowledge Assistant

A production-ready AI chatbot that answers queries using:
- Internal documents (PDF, DOCX, TXT)
- Google Drive files
- Web search fallback (DuckDuckGo)

## Tech Stack

- **Backend:** FastAPI (Python) + LangChain + OpenAI
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
- OpenAI API Key

### 1. Clone & Configure

```bash
cd ChatbotRag

# Copy and edit environment variables
cp .env.example .env

# Edit .env with your OpenAI API key
OPENAI_API_KEY=sk-your-api-key
```

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
# Edit .env with your database URL and OpenAI key

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
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT secret key |
| `GOOGLE_DRIVE_CREDENTIALS_PATH` | No | Path to Google credentials.json |

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

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is set correctly in `.env`
- Check API key has sufficient credits

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## License

MIT
