# ProjectContext.md

## 1. Project Summary

* **What the system actually does:** iphipi is an AI-powered mock interview platform. It parses a candidate's resume, infers their role, and conducts an interactive, multi-round technical interview. It captures audio, evaluates answers using a combination of keyword matching and LLM-based reasoning, dynamically adapts the difficulty based on the candidate's performance, and finally generates a comprehensive feedback report and job recommendations.
* **Current implementation status:** The core logic, including resume parsing, audio transcription, technical evaluation, dynamic difficulty adaptation, and feedback generation, is fully implemented and functional. The platform is running locally using an in-memory datastore backed by Redis (optional cache) and ChromaDB.
* **Main capabilities implemented:** 
  * Multimodal resume parsing (PDF/DOCX/TXT via `pdfplumber`/`spacy`)
  * Adaptive technical questioning based on resume context
  * Live audio transcription and heuristic analysis (Whisper + `librosa`)
  * Fast-path technical answer evaluation (Keywords + Async LLM eval)
  * Comprehensive coaching feedback report generation
  * Semantic job recommendations using vector search
* **Missing/incomplete features:** 
  * Vision analysis (implemented in `services/vision_analyzer.py` but currently skipped/mocked with neutral defaults in the main `api/interview.py` sync fast-path due to latency).
  * WebSockets for real-time streaming (currently uses REST polling).
  * Persistent relational database (SQLAlchemy models exist, but `interview.py` uses in-memory dictionaries for speed/simplicity).
  * Celery background task wiring for the fast-path (audio is processed synchronously via `asyncio.wait_for` instead of Celery in the current API implementation).

---

## 2. Complete Tech Stack

* **Frontend framework:** Next.js 16.2.6 (App Router), React 19.2.4 (Used for all UI, routing, and client-side logic).
* **State Management:** Zustand v5 (Used for lightweight, global interview state management on the frontend).
* **Styling:** TailwindCSS v4, shadcn/ui, Recharts (For UI components, layout, and score visualization).
* **Backend framework:** FastAPI 0.115.0, Uvicorn, Pydantic 2 (Used for high-performance, async API endpoints and request validation).
* **Database:** In-Memory Python Dictionaries (Primary session store in `interview.py`), PostgreSQL (Configured via SQLAlchemy but bypassed in current fast-path).
* **Vector database:** ChromaDB (Local SQLite-backed, used for semantic job recommendations and RAG question generation).
* **Cache/Session:** Redis (Used as an optional caching layer for session and profile states).
* **AI SDKs:** `groq` Python SDK, `langchain-groq`, `langchain`, `langgraph` (Used for LLM orchestration and API communication).
* **LLM providers/models:** Groq API `llama-3.3-70b-versatile` (Used for orchestration, evaluation, question generation, and feedback).
* **Speech models:** Groq API `whisper-large-v3-turbo` (Used for fast STT), `librosa` (Used for audio feature heuristics like hesitation and speaking rate).
* **CV models:** MediaPipe FaceMesh, DeepFace, `llama-3.2-90b-vision-preview` (Implemented in services, but currently skipped in active API flow).
* **Embeddings models:** `sentence-transformers` `all-MiniLM-L6-v2` (Used locally to encode candidate profiles and jobs).
* **Deployment stack:** Docker, Docker Compose (Configurations exist for local containerization and prod parity).
* **Package managers:** `npm` (Frontend), `pip` (Backend).
* **Websocket usage:** None. The application uses REST APIs.
* **Queue/workers:** Celery + Redis broker (Tasks defined but audio is processed synchronously with timeouts in the active `api/interview.py` for lower latency).
* **Testing stack:** `pytest`, `pytest-asyncio` (Backend), `jest`/`eslint` (Frontend).

---

## 3. Repository Structure

* `frontend/` - Next.js UI application
  * `app/` - App router pages (Landing, Interview room, Feedback report)
  * `components/` - React UI components (ResumeUploader, InterviewRoom, AudioRecorder)
  * `store/` - Zustand global state definitions
* `backend/` - FastAPI application
  * `api/` - REST endpoints (`interview.py`, `resume.py`, `feedback.py`, `jobs.py`)
  * `agents/` - LLM orchestration logic (`difficulty_adapter.py`, `question_generator.py`)
  * `services/` - Core processing services (`audio_analyzer.py`, `resume_parser.py`, `job_recommender.py`)
  * `scoring/` - Evaluation and score aggregation logic
  * `prompts/` - System prompts for Groq LLM interactions
  * `models/` - Pydantic schemas and SQLAlchemy DB models
  * `utils/` - Redis and ChromaDB client wrappers
* `ml/` - Utility functions for audio and vision feature extraction
* `data/` - Static datasets (e.g., `jobs_dataset.json` for recommendations)
* `scripts/` - Seeding scripts for ChromaDB (`seed_jobs.py`, `seed_questions.py`)

---

## 4. Environment Variables

* `GROQ_API_KEY`: **[REQUIRED]** API key for LLM, STT, and Vision models.
* `DATABASE_URL`: **[OPTIONAL]** PostgreSQL connection string (defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/iphipi`).
* `REDIS_URL`: **[OPTIONAL]** Redis connection string (defaults to `redis://localhost:6379/0`).
* `CHROMA_HOST`: **[OPTIONAL]** ChromaDB host (defaults to `localhost`).
* `CHROMA_PORT`: **[OPTIONAL]** ChromaDB port (defaults to `8000`).

---

## 5. Implemented Features

* **Resume Parsing:** [IMPLEMENTED] Uses `pdfplumber`, `python-docx`, and OCR fallbacks to extract text. `spacy` extracts skills. Entry: `backend/services/resume_parser.py`.
* **Role Inference:** [IMPLEMENTED] Uses LLM to determine top 3 suitable roles and seniority based on parsed skills. Entry: `backend/services/role_inferrer.py`.
* **Interview Orchestration:** [IMPLEMENTED] FSM-based state tracking (Intro -> Technical -> Feedback). Entry: `backend/api/interview.py`.
* **Adaptive Questioning:** [IMPLEMENTED] Dynamically adjusts difficulty and shifts topics based on correctness and confidence scores. Entry: `backend/agents/difficulty_adapter.py`.
* **Technical Scoring:** [IMPLEMENTED] Hybrid scoring using fast keyword matching and async LLM depth evaluation. Entry: `backend/scoring/technical_evaluator.py`.
* **Audio Analysis:** [IMPLEMENTED] STT via Whisper and heuristic extraction (confidence, speaking rate) via `librosa`. Entry: `backend/services/audio_analyzer.py`.
* **Vision Analysis:** [MOCKED/SKIPPED] Logic exists in `backend/services/vision_analyzer.py` but is bypassed in `api/interview.py` (hardcoded to neutral `0.65`) to ensure low latency during sync responses.
* **Feedback Generation:** [IMPLEMENTED] Generates detailed, actionable coaching reports using aggregate session data. Entry: `backend/agents/feedback_agent.py`.
* **Job Recommendations:** [IMPLEMENTED] Semantic similarity search using ChromaDB embeddings against a seeded static dataset. Entry: `backend/services/job_recommender.py`.
* **Session Persistence:** [PARTIAL] Uses Python in-memory dictionaries as the primary store in `interview.py`, with Redis as a secondary cache.
* **Authentication:** [PLANNED/MISSING] No auth implemented; uses generated UUIDs for sessions/candidates.
* **Deployment:** [PARTIAL] Dockerfiles exist, but primarily run natively via Uvicorn/Next.js dev server.

---

## 6. AI Architecture

* **Prompts (`backend/prompts/`):**
  * `resume_parse.py`: Schema-enforced JSON extraction from raw resume text.
  * `role_infer.py`: Rank suitable job roles based on skills/projects.
  * `question_gen.py`: Generate contextual technical questions avoiding repetition.
  * `answer_eval.py`: Rate answers (0.0-1.0) on correctness, depth, and relevance.
  * `feedback_gen.py`: Synthesize interview transcripts and scores into an actionable report.
* **Orchestration Logic:** Rather than a compiled LangGraph loop on the API layer, `backend/api/interview.py` acts as a stateful controller. It maintains an FSM (Introduction -> Technical). On each turn, it evaluates the answer, updates rolling scores, adapts difficulty, and generates the next question sequentially.
* **Adaptation Logic:** Handled by `difficulty_adapter.py`. If correctness < 0.4, difficulty drops. If correctness > 0.8 and depth > 0.7, difficulty increases. 2 consecutive weak answers trigger a topic shift based on the candidate's parsed focus areas.
* **Scoring Logic:** Final scores are a weighted average: Technical (40%), Depth (20%), Communication (15%), Confidence (15%), Engagement (10%). Answer evaluation uses a "fast path" keyword match (60%) combined with an async "background" LLM evaluation (40%).

---

## 7. Data Flow

1. **Resume Upload:** `POST /api/resume/upload` -> Parsed via `resume_parser.py` -> Skills extracted -> `role_inferrer.py` determines role -> Profile cached in dict/Redis.
2. **Interview Start:** `POST /api/interview/start` -> FSM initialized -> First contextual question generated via `question_generator.py` -> State cached.
3. **Response Capture:** `POST /api/interview/response` -> Audio base64 decoded -> `audio_analyzer.py` (Whisper STT + Librosa heuristics with 5s timeout) -> Keyword matching -> Async LLM evaluation triggered -> State updated.
4. **Adaptation:** `difficulty_adapter.py` calculates `next_action` (continue, shift topic, followup) based on recent performance.
5. **Question Generation:** `POST /api/interview/question` -> RAG via ChromaDB question bank -> LLM contextualizes question -> Returns to UI.
6. **Final Feedback:** `POST /api/interview/{id}/end` -> `GET /api/interview/{id}/feedback` -> Aggregates all answer scores -> `feedback_agent.py` generates final markdown/JSON report -> `job_recommender.py` queries ChromaDB for matches.

---

## 8. API Inventory

| Route | Method | Purpose | Request | Response |
|---|---|---|---|---|
| `/api/health` | GET | Check system status | None | `{status, timestamp, version}` |
| `/api/resume/upload` | POST | Parse resume & infer roles | `multipart/form-data` (file) | `{candidate_id, profile: {...}}` |
| `/api/interview/start` | POST | Init FSM and get first Q | `{candidate_id, role?}` | `{session_id, intro_message, first_question}` |
| `/api/interview/question` | POST | Generate next question | `{session_id}` | `{question, state_snapshot}` |
| `/api/interview/response` | POST | Submit answer (audio/text) | `{session_id, question_id, audio_b64?, transcript?}` | `{answer_id, next_action}` |
| `/api/interview/{id}/state` | GET | Fetch current FSM state | None | `{InterviewSession}` |
| `/api/interview/{id}/end` | POST | Mark session completed | None | `{session_id, status: "completed"}` |
| `/api/interview/{id}/feedback`| GET | Get final report & scores | None | `{ScoringOutput, FeedbackOutput}` |
| `/api/jobs/recommendations` | GET | Get matched jobs | `?candidate_id=` | `[JobRecommendation]` |

---

## 9. Database + Storage

* **Schemas/Models:** Pydantic models defined in `backend/models/schemas.py` (`CandidateProfile`, `InterviewSession`, `Question`, `ScoringOutput`). SQLAlchemy ORM models exist in `db_models.py` but are bypassed for speed in the current active implementation.
* **Vector Storage:** Local ChromaDB (SQLite-backed). Used for seeding/querying job embeddings (`data/jobs_dataset.json`) and RAG question generation.
* **Session Storage:** Primarily Python in-memory dictionaries (`_sessions`, `_profiles`, `_questions`, `_answers` in `interview.py`) with Redis acting as a secondary fallback/cache.
* **File Handling:** Uploaded resumes and captured WebM audio blobs are stored in temporary system directories, processed, and immediately cleaned up via `backend/utils/file_utils.py`.

---

## 10. Prompt Inventory

* **`resume_parse`** (`backend/prompts/resume_parse.py`): Extracts strict JSON profile from raw text. Nulls unknown fields. (Model: Llama 3.3 70B).
* **`role_infer`** (`backend/prompts/role_infer.py`): Infers top 3 job roles, seniority, weak areas, and focus areas from skills. (Model: Llama 3.3 70B).
* **`question_gen`** (`backend/prompts/question_gen.py`): Generates a specific, non-repeating technical question matching the target difficulty and topic. (Model: Llama 3.3 70B).
* **`answer_eval`** (`backend/prompts/answer_eval.py`): Rates an answer's correctness, depth, and relevance strictly between 0.0-1.0. (Model: Llama 3.3 70B).
* **`feedback_gen`** (`backend/prompts/feedback_gen.py`): Synthesizes interview Q&A history into an actionable, encouraging coaching report referencing specific session moments. (Model: Llama 3.3 70B).

---

## 11. Model Inventory

* **Groq Llama-3.3-70b-versatile**: Primary workhorse. Used for all text generation, orchestration, role inference, question generation, and evaluation. Extremely fast latency on GroqCloud.
* **Groq Whisper-large-v3-turbo**: Used for fast Speech-to-Text conversion in the `response` API. Critical latency-sensitive path.
* **sentence-transformers (all-MiniLM-L6-v2)**: Local embedding model used to encode candidate profiles and job descriptions for ChromaDB semantic search.
* **librosa**: Local DSP library. Calculates audio RMS energy and zero-crossing rates for confidence heuristics.
* **Groq Llama-3.2-90b-vision-preview / MediaPipe / DeepFace**: CV stack implemented but structurally bypassed in active demo flow to preserve API speed.

---

## 12. Demo-Relevant Features

* **Resume-Driven Context:** [MUST SHOW] [High Impact] Uploading a resume and seeing the first question directly reference a project or skill from it.
* **Adaptive Difficulty:** [MUST SHOW] [Technically Impressive] Purposefully answering a question poorly or briefly, and watching the system follow up with an easier or foundational question.
* **Audio Interactivity:** [MUST SHOW] [Visually Impressive] Speaking an answer, having it transcribed instantly via Whisper, and evaluated in real-time.
* **Actionable Feedback Report:** [MUST SHOW] [Highest Impact] The final screen showing detailed breakdowns, multi-dimensional radar charts (Communication, Technical), and specific job matches.
* **Vision Analysis:** [SKIP IN DEMO] The backend skips this to maintain speed. Do not attempt to demo webcam emotion analysis as scores will default to neutral 0.65.

---

## 13. Recommended Demo Flow

1. **Setup & Context (0:00-0:30):** Explain the architecture (FastAPI, Next.js, Groq Llama 3.3 70B for ultra-fast inference). Emphasize the stateful orchestration.
2. **Resume Upload (0:30-1:00):** Navigate to the landing page. Upload a tailored Software Engineering resume. Note how fast parsing and role inference occur.
3. **Question 1 - Strong Answer (1:00-2:00):** System asks an introductory technical question based on the resume. Use the microphone to provide a strong, keyword-rich answer. Point out the instant Whisper transcription and how the system dynamically increases difficulty for the next question.
4. **Question 2 - Weak Answer (2:00-3:00):** System asks a harder question. Provide a weak or confused audio answer. Explain the `difficulty_adapter` logic taking effect. Show the next question shifting to an easier follow-up or a new topic to support the candidate.
5. **Session End & Feedback (3:00-4:00):** End the interview manually. Show the generated feedback report. Highlight the radar chart dimensions (Technical vs Confidence), the specific actionable feedback that references the exact answers given, and the semantic Job Recommendations pulled via ChromaDB.
6. **Architecture Wrap-up (4:00-5:00):** Explain the "fast-path" keyword matching vs async LLM evaluation strategy used to keep the UI snappy.
* **Fallback Plan:** If audio fails due to mic permissions, type the answers. The fast-path text evaluation will still trigger the adaptive logic.

---

## 14. Best Demo Resume

* **Use:** A Mid-level Full Stack Developer (React, Node.js, AWS) resume.
* **Why:** It provides a broad set of skills, allowing the `difficulty_adapter` to easily shift topics (e.g., from Frontend React to Backend Node.js) if an answer is weak.
* **Triggers:** Will reliably trigger "Software Developer" role inference and seed ChromaDB with high-quality tech stack questions.

---

## 15. Best Demo Questions

* **Strong Generation Moment:** When the system asks a question referencing a specific project from the resume (e.g., "In your e-commerce project, how did you handle React state reconciliation?").
* **Adaptive Flow:** The transition from a failed hard question ("Explain the internal workings of V8 garbage collection") to a supportive, foundational question ("Let's step back, can you explain the difference between let and var?").
* **Feedback:** The final report citing exactly what the user said (e.g., "You correctly identified virtual DOM diffing, but missed the concept of React Fiber. Review X...").

---

## 16. Known Weaknesses

* **Vision Pipeline Latency:** The CV models (MediaPipe/DeepFace) are fully implemented but too slow for synchronous API responses.
  * *Demo Strategy:* Do not mention live emotion tracking during the demo, focus heavily on the text/audio adaptation and LLM reasoning.
* **In-Memory State Volatility:** The system relies heavily on Python dictionaries (`_sessions`) in `interview.py` rather than Postgres. If the backend restarts during the demo, the session is lost.
  * *Demo Strategy:* Ensure the Uvicorn server is stable and do not save/reload backend files during the presentation.
* **Transcription Timeouts:** Whisper API can occasionally exceed the strict 5.0-second `asyncio.wait_for` timeout in the fast path.
  * *Demo Strategy:* Keep audio answers under 30 seconds to guarantee fast processing and avoid the fallback empty transcript.

---

## 17. Deployment Status

* **Deployment Readiness:** Local/Hackathon ready. Not production ready (lacks auth, relies on in-memory state).
* **Local Run Instructions:**
  1. Set `GROQ_API_KEY` in `.env`.
  2. Start backend: `uvicorn backend.main:app --reload --port 8001`
  3. Start frontend: `cd frontend && npm run dev`
* **Demo Recommendation:** Run entirely locally. Groq API provides cloud-level AI performance without needing cloud hosting for the application itself.

---

## 18. Judge-Facing Talking Points

* **Orchestration:** "Instead of a generic single-prompt chatbot, iphipi uses a stateful Finite State Machine where every turn dynamically evaluates correctness and confidence to adapt difficulty in real-time."
* **Latency Optimization:** "To achieve sub-second conversational latency, we implemented a dual-eval pipeline: synchronous keyword heuristics immediately drive the FSM, while an async LLM evaluates depth in the background and blends the final score."
* **Multimodal Architecture:** "We ingest not just text, but live audio heuristics like hesitation and speaking rate using Whisper and `librosa`, directly feeding the candidate's confidence score into the adaptation logic."
* **Scalability:** "The architecture is decoupled; heavy audio and vision tasks are designed to be offloaded to Celery workers backed by Redis, keeping the main FastAPI event loop completely unblocked."

---

## 19. Final Demo Checklist

* [ ] Ensure `GROQ_API_KEY` is active and funded.
* [ ] Verify microphone permissions in the browser (`localhost:3000`).
* [ ] Run `python scripts/seed_jobs.py` to ensure ChromaDB is populated for the recommendation screen.
* [ ] Do a dry-run interview of exactly 3 questions to ensure the 5-second `asyncio.wait_for` timeout isn't hit on your network.
* [ ] Keep the demo resume PDF easily accessible on the desktop.
* [ ] Keep a pre-completed feedback URL ready in a hidden tab in case the live session encounters an API rate limit.
