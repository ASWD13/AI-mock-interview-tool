# Implementation.md

## 1. Product Goal

Build an AI-powered mock interview platform that parses a candidate's resume, infers suitable roles, conducts an adaptive multi-round interview (with audio and visual intelligence), evaluates technical and behavioral performance across multiple scoring dimensions, and generates explainable coaching feedback along with job recommendations — all orchestrated by a stateful FSM+LLM agent that adapts difficulty, topic, and tone in real time.

---

## 2. Scope

**Must-Have:**
- PDF/DOCX/TXT resume upload and structured parsing
- Skill extraction, seniority inference, role inference, focus/weak area detection
- Stateful interview orchestrator (FSM + LangGraph) with adaptive difficulty and topic switching
- Dynamic question generation (contextual, role-specific, follow-up aware)
- Transcript capture and technical answer evaluation (LLM + keyword)
- Audio analysis: STT (Whisper), hesitation detection, speaking rate, confidence heuristics
- Visual analysis: face detection (MediaPipe), gaze estimation, stress indicators (DeepFace)
- Multi-dimensional scoring (technical, depth, communication, confidence, engagement)
- Explainable, actionable feedback report generation
- Job recommendation (static dataset fallback acceptable)
- Clean interview UI with webcam/mic capture

**Optional:**
- Live job crawling (LinkedIn, Indeed)
- Advanced emotion AI beyond basic DeepFace
- Coding sandbox / live IDE
- WebSocket streaming for real-time responses
- Multi-language support

**Non-Goals:**
- ATS integration
- HR recruiter dashboard
- Voice cloning interviewer avatar
- Long-term multi-session tracking (MVP: single session)
- Mobile-native apps

---

## 3. Recommended Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js 14 (App Router) | SSR + API routes, ecosystem fit |
| Styling | TailwindCSS + shadcn/ui | Fast, clean, accessible components |
| State (frontend) | Zustand | Lightweight, simple for interview state |
| Video/Audio capture | WebRTC + MediaRecorder API | Native browser, no extra deps |
| Charts | Recharts | Simple, composable, React-native |
| Backend | FastAPI (Python) | Async, fast, ideal for ML integration |
| Async tasks | Celery + Redis | Offload audio/video processing |
| Agent orchestration | LangGraph | FSM+LLM hybrid, stateful graph execution |
| LLM chaining | LangChain | Prompt management, tool use |
| LLM provider | Groq — GPT OSS 120B | Best reasoning + function calling on GroqCloud; use `groq` Python SDK + `ChatGroq` for LangChain |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Fast, local, no API cost |
| STT | Groq — Whisper Large v3 Turbo | API-based, faster than local Whisper, no model weight download |
| Vision (multimodal) | Groq — Llama 4 Scout + MediaPipe + DeepFace + OpenCV | Llama 4 Scout for frame-level VQA; MediaPipe/DeepFace for landmark/emotion heuristics |
| PDF parsing | pdfplumber + pytesseract (fallback) | Reliable text extraction |
| DOCX parsing | python-docx | Standard |
| Main DB | PostgreSQL | Relational, reliable |
| Vector store | ChromaDB (local) | Lightweight, no external service |
| Cache | Redis | Session state, task queue broker |
| Containerization | Docker + docker-compose | Local dev and deployment parity |
| Deployment | Vercel (frontend) + Railway (backend) | Fast, free-tier friendly |
| CI/CD | GitHub Actions | Standard |
| Testing | pytest (backend), jest (frontend) | Standard frameworks |

---

## 4. System Architecture

```
Browser (Next.js)
  │
  ├─ resume upload (PDF/DOCX)   ──►  POST /api/resume/upload
  ├─ interview UI (webcam+mic)  ──►  POST /api/interview/question
  │                                  POST /api/interview/response
  └─ feedback view              ──►  GET  /api/interview/{id}/feedback

FastAPI Backend
  │
  ├─ ResumeEngine
  │   ├─ parse (pdfplumber / python-docx)
  │   ├─ extract_skills (spaCy + custom taxonomy)
  │   └─ infer_role+seniority (Groq GPT OSS 120B)
  │
  ├─ InterviewOrchestrator  ◄──  LangGraph StateGraph
  │   ├─ FSM states: INTRO → RESUME_DISCUSSION → TECHNICAL → FOLLOWUP → BEHAVIORAL → FEEDBACK
  │   ├─ QuestionGenerator  (Groq GPT OSS 120B + ChromaDB RAG)
  │   ├─ DifficultyAdapter  (rule-based on rolling scores)
  │   └─ StateTracker       (Redis session store)
  │
  ├─ EvaluationEngine
  │   ├─ TechnicalEvaluator  (Groq GPT OSS 120B + keyword match)
  │   ├─ AudioAnalyzer       (Groq Whisper Large v3 Turbo + librosa, Celery task)
  │   └─ VisionAnalyzer      (Groq Llama 4 Scout + MediaPipe + DeepFace, Celery task)
  │
  ├─ FeedbackAgent            (Groq GPT OSS 120B, full session context)
  │
  └─ JobRecommender           (embedding similarity on static dataset)

PostgreSQL  ←─ persistent entities
ChromaDB    ←─ question bank + job embeddings
Redis       ←─ session state, Celery broker
```

**Data Flow:**
1. Resume uploaded → parsed → structured profile stored in DB + Redis session
2. Interview start → orchestrator initialized with profile → FSM enters INTRO
3. Each turn: frontend posts audio blob + optional video frame → backend STT → evaluator → orchestrator decides next question → returns JSON {question, difficulty, topic}
4. Session end → all turn scores aggregated → FeedbackAgent generates report → stored in DB
5. Job recommendations fetched from ChromaDB similarity search on profile embedding

**State Flow:** Zustand (frontend) mirrors orchestrator session state via REST polling; no WebSocket in MVP.

---

## 5. Repository Structure

```
project/
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # Landing / resume upload
│   │   ├── interview/
│   │   │   └── [sessionId]/page.tsx  # Interview room
│   │   └── report/
│   │       └── [sessionId]/page.tsx  # Feedback report
│   ├── components/
│   │   ├── ResumeUploader.tsx
│   │   ├── InterviewRoom.tsx         # Webcam + question display
│   │   ├── AudioRecorder.tsx
│   │   ├── ScoreCard.tsx
│   │   └── FeedbackReport.tsx
│   ├── store/
│   │   └── interviewStore.ts         # Zustand
│   ├── lib/
│   │   └── api.ts                    # Typed fetch wrappers
│   └── public/
│
├── backend/
│   ├── main.py                       # FastAPI app entry
│   ├── config.py                     # Settings (pydantic-settings)
│   ├── api/
│   │   ├── resume.py
│   │   ├── interview.py
│   │   ├── feedback.py
│   │   └── jobs.py
│   ├── agents/
│   │   ├── orchestrator.py           # LangGraph StateGraph definition
│   │   ├── question_generator.py
│   │   ├── difficulty_adapter.py
│   │   └── feedback_agent.py
│   ├── services/
│   │   ├── resume_parser.py          # pdfplumber + python-docx
│   │   ├── skill_extractor.py        # spaCy + taxonomy
│   │   ├── role_inferrer.py          # GPT call
│   │   ├── audio_analyzer.py         # Whisper + librosa
│   │   ├── vision_analyzer.py        # MediaPipe + DeepFace
│   │   └── job_recommender.py        # embedding similarity
│   ├── scoring/
│   │   ├── technical_evaluator.py
│   │   └── score_aggregator.py
│   ├── models/
│   │   ├── db_models.py              # SQLAlchemy ORM
│   │   └── schemas.py                # Pydantic request/response models
│   ├── prompts/
│   │   ├── resume_parse.py
│   │   ├── role_infer.py
│   │   ├── question_gen.py
│   │   ├── answer_eval.py
│   │   └── feedback_gen.py
│   ├── workflows/
│   │   └── interview_graph.py        # LangGraph graph definition
│   ├── utils/
│   │   ├── redis_client.py
│   │   ├── chroma_client.py
│   │   └── file_utils.py
│   ├── tasks/
│   │   └── celery_tasks.py           # async audio/video tasks
│   └── tests/
│       ├── test_resume.py
│       ├── test_orchestrator.py
│       ├── test_evaluator.py
│       └── fixtures/
│           ├── sample_resume.pdf
│           └── sample_audio.wav
│
├── ml/
│   ├── audio/
│   │   └── audio_features.py         # librosa feature helpers
│   ├── vision/
│   │   └── vision_features.py        # MediaPipe/DeepFace helpers
│   └── embeddings/
│       └── embed_utils.py
│
├── data/
│   └── jobs_dataset.json             # Static job listings (500+ entries)
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── scripts/
│   ├── seed_jobs.py                  # Populate ChromaDB with job embeddings
│   └── seed_questions.py             # Seed question bank in ChromaDB
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 6. Data Models

### CandidateProfile (parsed resume output, stored in Redis + DB)
```json
{
  "candidate_id": "uuid",
  "name": "string",
  "email": "string",
  "experience_level": "fresher|junior|mid|senior",
  "years_experience": 2,
  "skills": ["React", "Node.js"],
  "skill_categories": {"frontend": ["React"], "backend": ["Node.js"]},
  "projects": [{"title": "str", "tech_stack": ["str"], "description": "str"}],
  "education": [{"degree": "str", "institution": "str", "year": "str"}],
  "certifications": ["str"],
  "possible_roles": ["Frontend Developer"],
  "focus_areas": ["React State Management"],
  "weak_areas": ["System Design"],
  "profile_embedding": "[float]"
}
```

### InterviewSession
```json
{
  "session_id": "uuid",
  "candidate_id": "uuid",
  "role": "Frontend Developer",
  "status": "active|completed",
  "current_state": "TECHNICAL",
  "difficulty": "easy|medium|hard",
  "current_topic": "React",
  "question_count": 5,
  "technical_score": 0.74,
  "communication_score": 0.67,
  "confidence_score": 0.61,
  "engagement_score": 0.72,
  "weak_topics": ["Redux"],
  "strong_topics": ["Hooks"],
  "question_history": ["uuid"],
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

### Question
```json
{
  "question_id": "uuid",
  "session_id": "uuid",
  "text": "Explain React reconciliation.",
  "topic": "React",
  "category": "fundamentals|architecture|behavioral|scenario",
  "difficulty": "easy|medium|hard",
  "expected_keywords": ["virtual DOM", "diffing", "fiber"],
  "is_followup": false,
  "parent_question_id": "uuid|null",
  "order": 3
}
```

### Answer
```json
{
  "answer_id": "uuid",
  "question_id": "uuid",
  "session_id": "uuid",
  "transcript": "string",
  "audio_duration_sec": 45,
  "correctness": 0.81,
  "depth": 0.69,
  "relevance": 0.92,
  "keyword_hits": ["virtual DOM", "diffing"],
  "keyword_miss": ["fiber"],
  "audio_scores": {
    "confidence": 0.71,
    "clarity": 0.63,
    "hesitation": 0.42,
    "speaking_rate_wpm": 132
  },
  "vision_scores": {
    "engagement": 0.74,
    "eye_contact": 0.68,
    "stress_indicator": 0.57
  }
}
```

### ScoringOutput
```json
{
  "session_id": "uuid",
  "technical_score": 0.74,
  "depth_score": 0.65,
  "communication_score": 0.67,
  "confidence_score": 0.61,
  "engagement_score": 0.72,
  "final_score": 0.69,
  "rating": "Good|Excellent|Average|Poor"
}
```

### FeedbackOutput
```json
{
  "session_id": "uuid",
  "overall_rating": "Good",
  "technical_feedback": [{"topic": "str", "observation": "str", "suggestion": "str"}],
  "communication_feedback": [{"observation": "str", "suggestion": "str"}],
  "behavioral_feedback": [{"observation": "str", "suggestion": "str"}],
  "improvement_plan": ["str"],
  "strengths": ["str"],
  "generated_at": "timestamp"
}
```

### JobRecommendation
```json
{
  "job_id": "uuid",
  "job_title": "Frontend Developer",
  "company": "ABC Corp",
  "location": "Remote",
  "required_skills": ["React", "TypeScript"],
  "match_score": 0.87,
  "why_matched": ["Strong React experience"],
  "missing_skills": ["TypeScript"]
}
```

---

## 7. API Contract

### Resume
| Method | Endpoint | Request | Response | Owner |
|---|---|---|---|---|
| POST | `/api/resume/upload` | multipart: file (PDF/DOCX/TXT) | `{candidate_id, profile: CandidateProfile}` | `api/resume.py` |

### Interview
| Method | Endpoint | Request | Response | Owner |
|---|---|---|---|---|
| POST | `/api/interview/start` | `{candidate_id, role?}` | `{session_id, intro_message, first_question: Question}` | `api/interview.py` |
| POST | `/api/interview/question` | `{session_id}` | `{question: Question, state_snapshot}` | `api/interview.py` |
| POST | `/api/interview/response` | `{session_id, question_id, audio_b64?, transcript?, video_frame_b64?}` | `{answer_id, next_action: "continue|followup|shift_topic|end"}` | `api/interview.py` |
| GET | `/api/interview/{session_id}/state` | — | `{InterviewSession}` | `api/interview.py` |
| POST | `/api/interview/{session_id}/end` | — | `{session_id, status: "completed"}` | `api/interview.py` |

### Feedback
| Method | Endpoint | Request | Response | Owner |
|---|---|---|---|---|
| GET | `/api/interview/{session_id}/feedback` | — | `{ScoringOutput, FeedbackOutput}` | `api/feedback.py` |

### Jobs
| Method | Endpoint | Request | Response | Owner |
|---|---|---|---|---|
| GET | `/api/jobs/recommendations` | `?candidate_id=&limit=5` | `[JobRecommendation]` | `api/jobs.py` |

---

## 8. Core Workflows

### 8.1 Resume Upload and Parsing
- **Input:** multipart file upload
- **Steps:**
  1. Detect file type (PDF/DOCX/TXT) via extension + magic bytes
  2. Extract raw text: `pdfplumber` for PDF, `python-docx` for DOCX, plain read for TXT
  3. OCR fallback: if pdfplumber yields < 100 chars → `pytesseract`
  4. Send raw text to `skill_extractor.py` (spaCy NER + skill taxonomy JSON)
  5. Send structured extract to Groq GPT OSS 120B via `resume_parse` prompt → returns `CandidateProfile`
  6. Generate profile embedding with `sentence-transformers`
  7. Store profile in PostgreSQL + Redis (`candidate:{id}:profile`)
- **Output:** `CandidateProfile`
- **Failure:** OCR fails → return error asking for text resume; LLM fails → retry once, then fallback to spaCy-only parse

### 8.2 Role Inference
- **Input:** `CandidateProfile.skills`, `CandidateProfile.projects`
- **Steps:**
  1. Map skills to categories using `skill_categories` taxonomy dict
  2. Call Groq GPT OSS 120B with `role_infer` prompt, passing skills + project summaries
  3. Return ranked list of `possible_roles` (max 3) + seniority level
- **Output:** `possible_roles: ["Frontend Developer", "Full Stack Developer"]`, `experience_level`
- **Failure:** LLM fails → use rule-based mapping table (React→Frontend, AWS→DevOps, etc.)

### 8.3 Job Recommendation Generation
- **Input:** `CandidateProfile.profile_embedding`, `possible_roles`
- **Steps:**
  1. Query ChromaDB with profile embedding, filter by role categories, return top-10 matches
  2. Re-rank by skill overlap score: `len(intersection(candidate_skills, job_skills)) / len(job_skills)`
  3. For top-5: `why_matched` + `missing_skills` computed deterministically (no LLM call needed)
  4. Return top-5 with full `JobRecommendation` objects
- **Output:** `[JobRecommendation]`
- **Failure:** ChromaDB unavailable → return rule-based matches from static `jobs_dataset.json`

### 8.4 Interview Start
- **Input:** `candidate_id`, optional `role` override
- **Steps:**
  1. Load `CandidateProfile` from Redis
  2. Initialize `InterviewSession` in DB with status=active, difficulty=medium
  3. Initialize LangGraph orchestrator state with profile context
  4. FSM enters `INTRODUCTION` state
  5. Generate intro message + first question (resume-level, easy difficulty)
  6. Store session state in Redis (`session:{id}:state`)
- **Output:** `{session_id, intro_message, first_question}`

### 8.5 Question Generation
- **Input:** `session_id`, current FSM state, `InterviewSession` state snapshot
- **Steps:**
  1. Load session state from Redis
  2. Call `QuestionGenerator` with: current_topic, difficulty, question_history (to avoid repeats), candidate weak/strong areas
  3. RAG: query ChromaDB question bank for seed questions matching topic+difficulty
  4. Groq GPT OSS 120B generates final question text conditioned on RAG context
  5. Store `Question` in DB, append to `question_history`
- **Output:** `Question`

### 8.6 Response Capture
- **Input:** `session_id`, `question_id`, audio blob (base64), optional video frame
- **Steps:**
  1. Decode audio → write to temp file → dispatch Celery task `process_audio`
  2. Optionally decode video frame → dispatch Celery task `process_vision`
  3. STT: Whisper transcribes audio → transcript stored immediately
  4. Return `answer_id` + `next_action` (determined after evaluation)
- **Output:** `answer_id`, async task IDs

### 8.7 Audio Scoring
- **Input:** audio file (WAV/WEBM)
- **Steps (Celery task):**
  1. Groq Whisper Large v3 Turbo API call → transcript (POST audio file to `https://api.groq.com/openai/v1/audio/transcriptions`, model=`whisper-large-v3-turbo`)
  2. librosa: extract RMS energy, zero-crossing rate, spectral features from local audio file
  3. Heuristics:
     - `speaking_rate_wpm` = word count / (duration / 60)
     - `hesitation_score` = (pause_count * avg_pause_duration + filler_word_count) / total_words
     - `confidence_score` = normalize(RMS_mean) — higher energy = higher confidence (capped heuristic)
     - `clarity_score` = 1 - hesitation_score (simplified)
  4. Update `Answer.audio_scores` in DB
- **Output:** `audio_scores` dict

### 8.8 Vision Scoring
- **Input:** video frame (JPEG base64) or short video clip
- **Steps (Celery task):**
  1. OpenCV decode → MediaPipe FaceMesh → extract 468 landmarks
  2. Gaze estimation: compute eye landmark ratios → classify as looking_at_screen / looking_away
  3. DeepFace analyze → dominant_emotion (nervous/confused/neutral/confident)
  4. Optional: send sampled frame to Groq Llama 4 Scout with prompt: `"Rate the candidate's engagement and stress level (0-1 each) from this webcam frame. Return JSON: {engagement, stress}"` — merge with heuristic scores (0.5 weight each)
  5. Heuristics:
     - `eye_contact_score` = frames_looking_at_screen / total_frames
     - `engagement_score` = 1 - (looking_away_ratio * 0.5 + excessive_movement_ratio * 0.5)
     - `stress_indicator` = proportion of frames with nervous/fearful emotion
  5. Update `Answer.vision_scores` in DB
- **Output:** `vision_scores` dict

### 8.9 Answer Evaluation (Technical)
- **Input:** transcript, `Question.expected_keywords`, session context
- **Steps:**
  1. Keyword match: `keyword_hits = [k for k in expected_keywords if k.lower() in transcript.lower()]`
  2. Keyword score: `len(keyword_hits) / len(expected_keywords)`
  3. LLM evaluation: call Groq GPT OSS 120B with `answer_eval` prompt → returns `{correctness, depth, relevance}` (0-1 each)
  4. Final technical scores = blend: `correctness = 0.6 * llm_correctness + 0.4 * keyword_score`
  5. Store in `Answer` record
- **Output:** `{correctness, depth, relevance, keyword_hits, keyword_miss}`

### 8.10 Adaptive Follow-Up Logic
- **Input:** latest `Answer` scores, session state
- **Handled in `difficulty_adapter.py`:**
  - `correctness < 0.4` → generate easier follow-up on same topic (difficulty - 1)
  - `correctness > 0.8 AND depth > 0.7` → increase difficulty + ask deeper follow-up
  - `consecutive_weak >= 2` (same topic) → `shift_topic()` → pick next topic from profile's focus_areas
  - `confidence_score < 0.4` → add supportive transition message to next question
  - `question_count >= max_per_topic (3)` → shift topic regardless of scores
- **Output:** `next_action: "continue|followup|shift_topic|end"`, updated session state

### 8.11 Final Report Generation
- **Input:** all `Answer` records for session, `InterviewSession`, `CandidateProfile`
- **Steps:**
  1. `score_aggregator.py`: compute per-dimension rolling averages across all answers
  2. Compute `final_score` using formula (see §10)
  3. Assign `rating`: ≥0.8→Excellent, ≥0.65→Good, ≥0.5→Average, else Poor
  4. Call `feedback_agent.py` with full transcript + scores → Groq GPT OSS 120B generates `FeedbackOutput`
  5. Store `FeedbackOutput` in DB, update `InterviewSession.status=completed`
- **Output:** `{ScoringOutput, FeedbackOutput}`
- **Failure:** Groq API fails → return template feedback based on score ranges

---

## 9. Agent Logic

### FSM States
```
INTRODUCTION
  └─ transition: after greeting + 1 warmup question → RESUME_DISCUSSION

RESUME_DISCUSSION
  └─ topic: candidate's projects + background
  └─ transition: after 2 questions → TECHNICAL_ROUND

TECHNICAL_ROUND  [main state, loops internally]
  └─ loops: question_gen → response → evaluate → adapt → question_gen
  └─ transition: total_questions >= 8 OR all focus_areas exhausted → BEHAVIORAL_ROUND

BEHAVIORAL_ROUND
  └─ topic: situational + soft skill questions (2-3 questions)
  └─ transition: after behavioral questions → FINAL_FEEDBACK

FINAL_FEEDBACK
  └─ trigger report generation, close session
```

### LangGraph Node Definitions (`interview_graph.py`)
- `node_init`: load profile, set difficulty=medium, topic=focus_areas[0]
- `node_generate_question`: call QuestionGenerator, store Question
- `node_await_response`: wait for POST /response (graph paused at this node)
- `node_evaluate`: call EvaluationEngine (technical + audio + vision async)
- `node_adapt`: call DifficultyAdapter → update state, determine next_action
- `node_transition`: check FSM state transition conditions
- `node_generate_feedback`: call FeedbackAgent

### Difficulty Adaptation Rules
```python
def adapt(state, answer):
    if answer.correctness < 0.4:
        state.difficulty = lower(state.difficulty)
        state.consecutive_weak += 1
    elif answer.correctness > 0.8 and answer.depth > 0.7:
        state.difficulty = higher(state.difficulty)
        state.consecutive_weak = 0
    else:
        state.consecutive_weak = 0

    if state.consecutive_weak >= 2:
        state.current_topic = next_topic(state)
        state.consecutive_weak = 0

    if state.question_count_on_topic >= 3:
        state.current_topic = next_topic(state)
        state.question_count_on_topic = 0

    if answer.audio_scores.confidence < 0.4:
        state.supportive_mode = True  # prepend supportive message to next question
```

### Topic Switching
- Topic queue: `focus_areas` first, then fallback to `weak_areas`, then generic role topics
- `next_topic(state)`: pop from topic_queue, push current_topic to visited_topics
- Never revisit a topic unless topic_queue exhausted (then loop)

### Audio/Vision Signal Blending
- After each answer, update rolling session averages:
  - `session.confidence_score = 0.7 * session.confidence_score + 0.3 * answer.audio_scores.confidence`
  - `session.engagement_score = 0.7 * session.engagement_score + 0.3 * answer.vision_scores.engagement`
- Use rolling averages (not per-answer) for FSM transition decisions

### Feedback Generation Behavior
- FeedbackAgent receives: full Q&A transcript, per-question scores, rolling session scores, profile weak_areas
- Instruction to Groq GPT OSS 120B: generate 2-3 specific technical observations, 1-2 communication observations, 1-2 behavioral observations, and 3 concrete improvement actions
- Must reference specific questions/topics from the session (not generic advice)

---

## 10. Scoring System

### Dimensions and Weights
| Dimension | Weight | Source |
|---|---|---|
| Technical Correctness | 0.40 | `Answer.correctness` (LLM + keyword blend) |
| Depth of Knowledge | 0.20 | `Answer.depth` (LLM eval) |
| Communication | 0.15 | `Answer.audio_scores.clarity` |
| Confidence | 0.15 | `Answer.audio_scores.confidence` |
| Engagement | 0.10 | `Answer.vision_scores.engagement` |

### Score Computation
```python
# Per answer (all values 0.0-1.0):
answer.correctness = 0.6 * llm_correctness + 0.4 * keyword_score
answer.depth = llm_depth
answer.communication = audio.clarity_score
answer.confidence = audio.confidence_score
answer.engagement = vision.engagement_score

# Session aggregation (arithmetic mean across all answers):
technical_score = mean([a.correctness for a in answers])
depth_score = mean([a.depth for a in answers])
communication_score = mean([a.communication for a in answers])
confidence_score = mean([a.confidence for a in answers])
engagement_score = mean([a.engagement for a in answers])

# Final score:
final_score = (
    technical_score * 0.40 +
    depth_score * 0.20 +
    communication_score * 0.15 +
    confidence_score * 0.15 +
    engagement_score * 0.10
)

# Rating:
if final_score >= 0.80: rating = "Excellent"
elif final_score >= 0.65: rating = "Good"
elif final_score >= 0.50: rating = "Average"
else: rating = "Needs Improvement"
```

### Heuristics for Missing Data
- If audio unavailable: `confidence_score = correctness * 0.8` (proxy)
- If vision unavailable: `engagement_score = 0.65` (neutral default)
- If transcript empty: `correctness = 0.0`, `depth = 0.0`

---

## 11. Prompting Strategy

### 11.1 Resume Parse Prompt (`prompts/resume_parse.py`)
```
SYSTEM: You are a resume parser. Extract structured data from the resume text below.
Return ONLY valid JSON matching this schema exactly: {schema}
Do not add commentary. If a field is unknown, use null or [].

USER: <resume_text>
```

### 11.2 Role Inference Prompt (`prompts/role_infer.py`)
```
SYSTEM: You are a technical recruiter. Given a candidate's skills and projects, infer:
1. Top 3 most suitable job roles (ordered by fit)
2. Seniority level: fresher/junior/mid/senior
3. Top 3 strong focus areas
4. Top 3 weak/missing areas
Return ONLY JSON: {"possible_roles": [], "experience_level": "", "focus_areas": [], "weak_areas": []}

USER: Skills: {skills}
Projects: {projects_summary}
Years experience: {years}
```

### 11.3 Question Generation Prompt (`prompts/question_gen.py`)
```
SYSTEM: You are a technical interviewer. Generate ONE interview question.
Role: {role} | Topic: {current_topic} | Difficulty: {difficulty}
Previous questions asked: {question_history_titles}
Candidate weak areas: {weak_areas}
Context (use if relevant): {rag_seed_question}
Rules: Do not repeat previous questions. Match difficulty exactly.
Return ONLY JSON: {"question": "", "expected_keywords": [], "category": ""}

USER: Generate the next question.
```

### 11.4 Answer Evaluation Prompt (`prompts/answer_eval.py`)
```
SYSTEM: You are a technical interviewer evaluating an answer.
Question: {question}
Expected concepts: {expected_keywords}
Candidate answer transcript: {transcript}
Rate 0.0-1.0 for each. Return ONLY JSON:
{"correctness": 0.0, "depth": 0.0, "relevance": 0.0, "reasoning": ""}

USER: Evaluate this answer.
```

### 11.5 Feedback Generation Prompt (`prompts/feedback_gen.py`)
```
SYSTEM: You are an interview coach. Generate specific, actionable feedback.
Candidate profile: {profile_summary}
Interview transcript (Q&A pairs): {transcript}
Scores: technical={tech}, communication={comm}, confidence={conf}, engagement={eng}
Rules:
- Reference specific questions and topics from this interview
- Never give generic advice
- Be encouraging but honest
- improvement_plan must have exactly 3 actionable steps
Return ONLY JSON: {FeedbackOutput schema}

USER: Generate feedback report.
```

---

## 12. Job Recommendation Logic

### Input Signals
- `CandidateProfile.profile_embedding` (sentence-transformers vector)
- `CandidateProfile.possible_roles`
- `CandidateProfile.skills`
- `CandidateProfile.experience_level`

### Data Source
- **Primary:** `data/jobs_dataset.json` — static dataset of 500+ jobs with fields: `{job_id, job_title, company, location, required_skills, description, experience_level}`
- Seeded into ChromaDB on startup via `scripts/seed_jobs.py`
- Document text = `"{job_title} at {company}. Skills: {required_skills}. {description}"`

### Ranking Formula
```python
# Step 1: Semantic retrieval (ChromaDB)
chroma_results = collection.query(
    query_embeddings=[profile_embedding],
    n_results=20,
    where={"experience_level": candidate.experience_level}  # optional filter
)

# Step 2: Re-rank by skill overlap
for job in chroma_results:
    overlap = len(set(candidate.skills) & set(job.required_skills))
    coverage = overlap / max(len(job.required_skills), 1)
    job.match_score = 0.5 * semantic_similarity + 0.5 * coverage

# Step 3: Sort descending, take top 5
top_jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)[:5]
```

### Explanation Generation
```python
for job in top_jobs:
    job.why_matched = [s for s in candidate.skills if s in job.required_skills]
    job.missing_skills = [s for s in job.required_skills if s not in candidate.skills]
    # No LLM call needed for this — deterministic
```

### Fallback
- If ChromaDB fails → load `jobs_dataset.json` directly, compute skill overlap only, skip semantic similarity

---

## 13. Implementation Phases

### Phase 1 — Foundation
- [ ] Init monorepo: `frontend/` (Next.js), `backend/` (FastAPI), `docker-compose.yml`
- [ ] Configure PostgreSQL + Redis + ChromaDB via docker-compose
- [ ] Create all SQLAlchemy ORM models (`db_models.py`) + run Alembic migrations
- [ ] Create all Pydantic schemas (`schemas.py`)
- [ ] Implement Redis client util and ChromaDB client util
- [ ] Set up `.env` with: `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`
- [ ] Implement `config.py` (pydantic-settings); add `groq_api_key: str` setting
- [ ] Install `groq` Python SDK (`pip install groq langchain-groq`); configure `ChatGroq(model="gpt-oss-120b")` as default LLM in LangChain
- [ ] Add CORS, basic health endpoint `/api/health`

### Phase 2 — Resume Parser
- [ ] Implement `resume_parser.py`: PDF (pdfplumber + pytesseract fallback), DOCX (python-docx), TXT
- [ ] Build `skill_categories` taxonomy JSON (100+ skills mapped to categories)
- [ ] Implement `skill_extractor.py` using spaCy `en_core_web_sm` + taxonomy lookup
- [ ] Write `resume_parse` prompt in `prompts/resume_parse.py`
- [ ] Implement `resume_parser.py` Groq GPT OSS 120B call → returns `CandidateProfile`
- [ ] Implement `POST /api/resume/upload` endpoint
- [ ] Seed ChromaDB: `scripts/seed_jobs.py` (run once)
- [ ] Test with 3 sample resumes (PDF/DOCX/TXT)

### Phase 3 — Role Inference
- [ ] Implement `role_inferrer.py` with `role_infer` prompt + fallback rule table
- [ ] Generate profile embedding using `sentence-transformers` in `embed_utils.py`
- [ ] Store embedding in candidate record
- [ ] Add role inference call to resume upload flow (auto-runs after parse)
- [ ] Test role inference accuracy with 5 sample profiles

### Phase 4 — Interview Orchestrator
- [ ] Define LangGraph `StateGraph` in `interview_graph.py` with all nodes
- [ ] Implement FSM state machine in `orchestrator.py` with transition rules
- [ ] Implement `difficulty_adapter.py` with all adaptation rules (§9)
- [ ] Implement `question_generator.py`: RAG query ChromaDB + Groq GPT OSS 120B generation
- [ ] Seed question bank in ChromaDB: `scripts/seed_questions.py` (200+ questions across roles/difficulties)
- [ ] Implement `POST /api/interview/start` and `GET /api/interview/{id}/state`

### Phase 5 — Interview UI
- [ ] Build `ResumeUploader.tsx` component (drag-drop + progress)
- [ ] Build `InterviewRoom.tsx`: webcam preview, question display, record button
- [ ] Build `AudioRecorder.tsx`: MediaRecorder API → base64 audio blob
- [ ] Implement Zustand store: session_id, current_question, state, scores
- [ ] Implement `lib/api.ts`: typed wrappers for all backend endpoints
- [ ] Wire up: upload → infer → start → question loop
- [ ] Implement `POST /api/interview/question` and `POST /api/interview/response`

### Phase 6 — Evaluation Engine
- [ ] Implement `technical_evaluator.py`: keyword match + Groq GPT OSS 120B eval prompt
- [ ] Implement `score_aggregator.py`: rolling averages + final score formula
- [ ] Wire evaluation into response submission flow
- [ ] Implement `POST /api/interview/{id}/end`

### Phase 7 — Audio Analysis
- [ ] Implement `audio_analyzer.py`: Groq Whisper Large v3 Turbo API (STT) + librosa features + heuristics
- [ ] Define Celery task `process_audio` in `celery_tasks.py`
- [ ] Wire audio blob from frontend → base64 decode → temp WAV file → Groq STT API call → librosa analysis
- [ ] Update `Answer.audio_scores` after task completes
- [ ] Fallback: if Groq API fails, use neutral audio scores (0.65)

### Phase 8 — Vision Analysis
- [ ] Implement `vision_analyzer.py`: MediaPipe FaceMesh + DeepFace emotion + Groq Llama 4 Scout frame VQA
- [ ] Define Celery task `process_vision`
- [ ] Accept video frame (JPEG base64) per-response from frontend
- [ ] Implement gaze estimation heuristic from MediaPipe landmarks; blend with Llama 4 Scout VQA scores (0.5/0.5)
- [ ] Update `Answer.vision_scores` after task completes
- [ ] Fallback: if Llama 4 Scout / MediaPipe fails, use gaze-only heuristic; if all fails, use neutral scores (0.65)

### Phase 9 — Feedback Agent
- [ ] Implement `feedback_agent.py`: aggregate session data → Groq GPT OSS 120B feedback prompt
- [ ] Implement `GET /api/interview/{session_id}/feedback`
- [ ] Build `FeedbackReport.tsx`: score cards (Recharts radar chart), feedback text, improvement plan
- [ ] Build `ScoreCard.tsx`: per-dimension score display
- [ ] Add template-based fallback feedback for GPT failure

### Phase 10 — Job Matching
- [ ] Implement `job_recommender.py`: ChromaDB query + skill overlap re-ranking
- [ ] Implement `GET /api/jobs/recommendations`
- [ ] Show job recommendations on landing page after resume upload
- [ ] Add `missing_skills` display to each recommendation

### Phase 11 — Polish
- [ ] Add loading states, error boundaries in frontend
- [ ] Add supportive transition messages for low-confidence candidates
- [ ] Implement `POST /api/interview/{id}/end` auto-trigger after 10 questions or FSM reaches FINAL_FEEDBACK
- [ ] Add retry logic for Groq API calls (exponential backoff, max 3 retries)
- [ ] Run full end-to-end demo flow test
- [ ] Deploy: frontend to Vercel, backend to Railway, PostgreSQL/Redis on Railway

---

## 14. Testing Plan

### Unit Tests (`backend/tests/`)
- `test_resume.py`: PDF parse, DOCX parse, OCR fallback, skill extraction accuracy
- `test_role_infer.py`: rule-based fallback correctness, GPT output schema validation
- `test_evaluator.py`: keyword match logic, score formula, aggregation
- `test_difficulty_adapter.py`: all transition rules (weak/strong/consecutive/topic shift)
- `test_job_recommender.py`: skill overlap calculation, ranking order

### Integration Tests
- Full resume upload → role inference → job recommendations flow
- Interview start → 5 question loop → session state consistency
- Response submission → audio task → vision task → score update
- Interview end → feedback generation → report completeness

### Mocked AI/Service Tests
- Mock Groq client: return fixture JSON for all LLM calls (GPT OSS 120B + Llama 4 Scout)
- Mock Groq Whisper API: return fixture transcript
- Mock MediaPipe/DeepFace: return fixture scores
- Mock ChromaDB: return fixture question/job results

### Sample Fixtures (`tests/fixtures/`)
- `sample_resume.pdf` — frontend developer profile
- `sample_resume.docx` — data analyst profile
- `sample_audio.wav` — 30s spoken answer
- `expected_profile.json` — expected CandidateProfile output
- `expected_evaluation.json` — expected Answer scores
- `expected_feedback.json` — expected FeedbackOutput

### Acceptance Checks (Demo Readiness)
- [ ] Resume upload completes in < 10s
- [ ] Role inference correct for 3 sample resumes
- [ ] Questions generated are contextually relevant (manual check)
- [ ] Difficulty visibly changes after 2 weak answers (log output)
- [ ] Topic shifts after 3 questions on same topic
- [ ] Feedback report references actual session questions
- [ ] Job recommendations show `match_score > 0.5` for matching profile
- [ ] Full demo flow (upload → 8 questions → report) runs without errors

---

## 15. Risks and Fallbacks

| Risk | Fallback |
|---|---|
| PDF parsing fails (scanned/image PDF) | pytesseract OCR; if still fails, prompt user for text resume |
| LLM hallucination in evaluation | Keyword match score overrides LLM if gap > 0.4; validate output JSON schema |
| LLM returns invalid JSON | Use `response_format={"type": "json_object"}` in Groq API call; retry once |
| Webcam/mic unavailable | Accept text input for transcript; skip audio/vision, use neutral scores (0.65) |
| High latency (Groq calls) | Cache question generation results; run evaluation async; show skeleton loader |
| Celery task failure | Synchronous fallback: run audio/vision analysis in-request (slower but functional) |
| ChromaDB unavailable | Load from `jobs_dataset.json` directly; load questions from `seed_questions.json` |
| Audio file too large for Groq API | Limit recording to 90s; re-encode to 16kHz mono WAV before upload (reduces size ~4x) |
| DeepFace model download fails | Skip emotion detection; use gaze-only engagement score; Llama 4 Scout VQA as backup |
| Groq rate limit hit | Exponential backoff (1s, 2s, 4s); queue requests via Redis if needed |
| Noisy/inconsistent scoring | Rolling average smoothing (0.7/0.3 weights); floor scores at 0.1, cap at 1.0 |

---

## 16. MVP Definition

### Minimum viable demo (satisfies hackathon criteria):
**Must work:**
- Resume upload → parsed profile displayed on screen
- Role inference shown to user (e.g., "We detected: Frontend Developer")
- Interview starts with 6-8 dynamically generated questions
- Orchestrator visibly adapts: at least 1 topic shift and 1 difficulty change during demo
- Answers evaluated and scored (technical score shown per answer)
- Final feedback report with scores + 3 improvement suggestions
- Job recommendations shown (5 jobs with match scores)

**Simplify without hurting demo:**
- Audio scoring: call Groq Whisper Large v3 Turbo for STT but use simple word-count + pause heuristics only (skip librosa)
- Vision scoring: MediaPipe face detection + simple gaze heuristic; skip DeepFace if slow
- Job recommendations: static dataset only, no live crawling
- No user authentication — session by session_id URL param only
- Single concurrent session (no multi-user scaling needed)

**Can fake for demo:**
- Pre-record a video frame sequence for vision analysis (avoids webcam permission issues)
- Pre-populate a known resume so the demo is predictable

---

## 17. Build Instructions for the Coding Agent

1. **Clone and init:** Create monorepo with `frontend/`, `backend/`, `docker/` dirs; init git
2. **Start services:** Run `docker-compose up` — PostgreSQL on 5432, Redis on 6379, ChromaDB on 8000
3. **Backend setup:** `cd backend && pip install -r requirements.txt && python -m spacy download en_core_web_sm`
4. **Run migrations:** `alembic upgrade head`
5. **Seed data:** `python scripts/seed_jobs.py && python scripts/seed_questions.py`
6. **Start backend:** `uvicorn main:app --reload --port 8001`
7. **Start Celery:** `celery -A tasks.celery_tasks worker --loglevel=info`
8. **Frontend setup:** `cd frontend && npm install && npm run dev`
9. **Verify:** `curl http://localhost:8001/api/health` → `{"status": "ok"}`
10. **Build in phase order:** Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 (do not skip ahead)
11. **Test each phase** before starting next: run `pytest backend/tests/` after each phase
12. **Environment:** Set `GROQ_API_KEY` in `.env` before Phase 2; all other services are local
13. **Deploy:** `vercel deploy` from `frontend/`; push backend Docker image to Railway
14. **Naming convention:** Use exact names from §5 (file names) and §6 (field names) throughout — no aliases
