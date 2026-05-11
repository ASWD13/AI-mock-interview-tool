# InterviewPrep — AI Mock Interview Platform

AI-powered mock interview platform that parses resumes, conducts adaptive multi-round interviews with audio and visual intelligence, evaluates performance across multiple dimensions, and generates coaching feedback with job recommendations.

## Quick Start

### 1. (Optional) Database Setup
The platform is fully configured to run without external dependencies (using in-memory Python dictionaries and local SQLite files for ChromaDB). You do NOT need Docker to run this application.

### 2. Backend Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Seed Data
```bash
python scripts/seed_jobs.py
python scripts/seed_questions.py
```

### 4. Start Backend
```bash
uvicorn backend.main:app --reload --port 8001
```

### 5. Start Celery Worker
```bash
celery -A backend.tasks.celery_tasks worker --loglevel=info
```

### 6. Frontend Setup
```bash
cd frontend && npm install && npm run dev
```

### 7. Verify
```bash
curl http://localhost:8001/api/health
```

## Architecture

- **Frontend:** Next.js 14 (App Router) + TailwindCSS + Zustand
- **Backend:** FastAPI + LangGraph + Groq AI
- **Database:** Optional PostgreSQL + Redis. Defaults to In-Memory store and SQLite-backed ChromaDB.
- **ML:** Sentence Transformers + MediaPipe + DeepFace
- **STT:** Groq Whisper Large v3 Turbo
- **Vision:** Groq Llama 4 Scout + MediaPipe FaceMesh

## Environment Variables

Set `GROQ_API_KEY` in `.env` for AI features. All services can run natively on your machine without Docker.

## Testing

```bash
pytest backend/tests/ -v
```
