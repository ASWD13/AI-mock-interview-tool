"""Interview API endpoints — fully self-contained, no PostgreSQL required."""

from fastapi import APIRouter, HTTPException
from uuid import uuid4, UUID
from typing import Dict, Any, Optional
import asyncio

from backend.models.schemas import (
    InterviewStartRequest, InterviewStartResponse,
    InterviewQuestionResponse, InterviewResponseRequest,
    InterviewResponseResponse, InterviewEndResponse,
    InterviewSession, Question
)
from backend.utils.redis_client import redis_client
from backend.agents.question_generator import generate_question
from backend.agents.difficulty_adapter import adapt_difficulty
from backend.scoring.technical_evaluator import evaluate_answer
from backend.scoring.score_aggregator import update_session_scores

router = APIRouter()

# ── In-memory stores (primary, Redis as optional cache) ──────────────
_sessions: Dict[str, Dict[str, Any]] = {}
_profiles: Dict[str, Dict[str, Any]] = {}
_questions: Dict[str, Dict[str, Any]] = {}
_answers: Dict[str, list] = {}


def store_profile(candidate_id: str, profile: Dict[str, Any]):
    """Called from resume upload to share profile data with interview."""
    _profiles[candidate_id] = profile


async def _get_state(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        state = await redis_client.get_json(f"session:{session_id}:state")
        if state:
            _sessions[session_id] = state
            return state
    except Exception:
        pass
    return _sessions.get(session_id)


async def _set_state(session_id: str, state: Dict[str, Any]):
    _sessions[session_id] = state
    try:
        await redis_client.set_json(f"session:{session_id}:state", state, expire=7200)
    except Exception:
        pass


async def _get_profile(candidate_id: str) -> Optional[Dict[str, Any]]:
    if candidate_id in _profiles:
        return _profiles[candidate_id]
    try:
        data = await redis_client.get_json(f"candidate:{candidate_id}:profile")
        if data:
            _profiles[candidate_id] = data
            return data
    except Exception:
        pass
    return None


# ── Start Interview ──────────────────────────────────────────────────

@router.post("/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    """Start a new interview session."""
    candidate_id = str(request.candidate_id)
    profile_data = await _get_profile(candidate_id)

    if not profile_data:
        profile_data = {
            "candidate_id": candidate_id,
            "name": "Candidate",
            "skills": [],
            "possible_roles": ["Software Developer"],
            "focus_areas": [],
            "weak_areas": [],
            "experience_level": "junior",
        }

    role = request.role or (
        profile_data.get("possible_roles", ["Software Developer"])[0]
        if profile_data.get("possible_roles")
        else "Software Developer"
    )
    focus_areas = profile_data.get("focus_areas", [])
    skills = profile_data.get("skills", [])
    current_topic = focus_areas[0] if focus_areas else (skills[0] if skills else role)

    session_id = uuid4()

    # Generate first question (with 8s timeout)
    try:
        first_q = await asyncio.wait_for(
            generate_question(
                session_id=session_id, role=role, topic=current_topic,
                difficulty="easy", question_history=[], weak_areas=profile_data.get("weak_areas", []),
                profile_data=profile_data, category="fundamentals", is_intro=True,
            ),
            timeout=8.0,
        )
    except Exception as e:
        print(f"Question gen failed/timeout: {e}")
        first_q = {
            "question_id": uuid4(),
            "text": f"Tell me about yourself and your experience as a {role}.",
            "topic": current_topic, "category": "fundamentals",
            "expected_keywords": skills[:5] if skills else ["experience", "skills"],
        }

    q_id = first_q.get("question_id", uuid4())
    _questions[str(q_id)] = first_q

    name = profile_data.get("name", "")
    intro_message = f"Welcome{', ' + name if name else ''}! I'll be conducting your interview for the {role} position today. Let's start by discussing your background."

    session_state = {
        "session_id": str(session_id),
        "candidate_id": candidate_id,
        "role": role,
        "status": "active",
        "current_state": "INTRODUCTION",
        "difficulty": "medium",
        "current_topic": current_topic,
        "question_count": 1,
        "technical_score": 0.0,
        "communication_score": 0.0,
        "confidence_score": 0.0,
        "engagement_score": 0.0,
        "weak_topics": [],
        "strong_topics": [],
        "question_history": [str(q_id)],
        "topic_queue": (focus_areas[1:] if len(focus_areas) > 1 else skills[1:6] if len(skills) > 1 else []),
        "visited_topics": [],
        "consecutive_weak": 0,
        "question_count_on_topic": 1,
        "supportive_mode": False,
    }
    await _set_state(str(session_id), session_state)
    _answers[str(session_id)] = []

    return InterviewStartResponse(
        session_id=session_id,
        intro_message=intro_message,
        first_question=Question(
            question_id=q_id, session_id=session_id, text=first_q["text"],
            topic=first_q.get("topic", current_topic),
            category=first_q.get("category", "fundamentals"),
            difficulty="easy", expected_keywords=first_q.get("expected_keywords", []),
            is_followup=False, order=1,
        ),
    )


# ── Submit Response ──────────────────────────────────────────────────

@router.post("/interview/response", response_model=InterviewResponseResponse)
async def submit_response(request: InterviewResponseRequest):
    """Submit a response — fast path: keyword eval only, audio/vision in background."""
    session_id = str(request.session_id)
    question_id = str(request.question_id)

    state = await _get_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    question = _questions.get(question_id, {})
    expected_keywords = question.get("expected_keywords", [])
    question_text = question.get("text", "")

    # ── Fast path: use transcript directly if available ──────────
    transcript = request.transcript or ""
    audio_scores = {"confidence": 0.65, "clarity": 0.65, "hesitation": 0.0, "speaking_rate_wpm": 0.0}
    vision_scores = {"engagement": 0.65, "eye_contact": 0.65, "stress_indicator": 0.0}

    # If audio provided but no transcript, do quick STT with 5s timeout
    if request.audio_b64 and not transcript:
        try:
            from backend.services.audio_analyzer import analyze_audio
            from backend.utils.file_utils import decode_base64_to_file, cleanup_temp_file
            audio_path = decode_base64_to_file(request.audio_b64, suffix=".webm")
            audio_result = await asyncio.wait_for(analyze_audio(audio_path), timeout=5.0)
            transcript = audio_result.get("transcript", "") or ""
            audio_scores = audio_result.get("audio_scores", audio_scores)
            cleanup_temp_file(audio_path)
        except asyncio.TimeoutError:
            print("Audio analysis timed out — using defaults")
        except Exception as e:
            print(f"Audio analysis failed: {e}")

    # Skip vision analysis entirely (too slow for sync path)
    # Vision scores stay at neutral defaults

    # ── Fast evaluation: keyword-only (no LLM call) ─────────────
    if not transcript or len(transcript.strip()) < 5:
        eval_result = {"correctness": 0.0, "depth": 0.0, "relevance": 0.0,
                       "keyword_hits": [], "keyword_miss": expected_keywords}
    else:
        keyword_hits = [k for k in expected_keywords if k.lower() in transcript.lower()]
        keyword_miss = [k for k in expected_keywords if k.lower() not in transcript.lower()]
        keyword_score = len(keyword_hits) / max(len(expected_keywords), 1)

        # Heuristic depth/relevance from transcript length
        word_count = len(transcript.split())
        depth = min(1.0, word_count / 100)   # 100 words = full depth
        relevance = keyword_score * 0.7 + 0.3  # base relevance

        eval_result = {
            "correctness": keyword_score,
            "depth": depth,
            "relevance": relevance,
            "keyword_hits": keyword_hits,
            "keyword_miss": keyword_miss,
        }

        # Async LLM eval in background (fire-and-forget, updates state later)
        asyncio.create_task(_background_llm_eval(
            session_id, question_id, transcript, expected_keywords, question_text
        ))

    # Store answer
    answer_id = uuid4()
    if session_id not in _answers:
        _answers[session_id] = []
    _answers[session_id].append({
        "answer_id": str(answer_id), "question_id": question_id,
        "transcript": transcript, "correctness": eval_result["correctness"],
        "depth": eval_result["depth"], "audio_scores": audio_scores,
        "vision_scores": vision_scores,
    })

    # Update rolling scores
    state = update_session_scores(state, eval_result, audio_scores, vision_scores)

    # Adapt difficulty (includes FSM transition)
    next_action, state = adapt_difficulty(state, eval_result, audio_scores)

    await _set_state(session_id, state)

    return InterviewResponseResponse(answer_id=answer_id, next_action=next_action)


async def _background_llm_eval(session_id, question_id, transcript, keywords, question_text):
    """Background task: run LLM evaluation and update session scores."""
    try:
        result = await asyncio.wait_for(
            evaluate_answer(transcript, keywords, question_text),
            timeout=10.0,
        )
        state = await _get_state(session_id)
        if state:
            # Blend background eval into session scores
            state["technical_score"] = 0.5 * state.get("technical_score", 0.5) + 0.5 * result.get("correctness", 0.5)
            await _set_state(session_id, state)
    except Exception as e:
        print(f"Background LLM eval failed: {e}")


# ── Get Next Question ────────────────────────────────────────────────

@router.post("/interview/question", response_model=InterviewQuestionResponse)
async def get_next_question(request: dict):
    """Get the next interview question."""
    session_id = request.get("session_id", "")
    state = await _get_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    profile_data = await _get_profile(state["candidate_id"]) or {}

    try:
        q_data = await asyncio.wait_for(
            generate_question(
                session_id=UUID(session_id), role=state["role"],
                topic=state["current_topic"], difficulty=state["difficulty"],
                question_history=state.get("question_history", []),
                weak_areas=state.get("weak_topics", []), profile_data=profile_data,
            ),
            timeout=8.0,
        )
    except Exception as e:
        print(f"Question gen failed/timeout: {e}")
        q_data = {
            "question_id": uuid4(),
            "text": f"Can you explain your experience with {state['current_topic']}?",
            "topic": state["current_topic"], "category": "fundamentals",
            "expected_keywords": [],
        }

    q_id = q_data.get("question_id", uuid4())
    _questions[str(q_id)] = q_data

    state["question_count"] += 1
    state["question_count_on_topic"] = state.get("question_count_on_topic", 0) + 1
    state["question_history"].append(str(q_id))
    await _set_state(session_id, state)

    return InterviewQuestionResponse(
        question=Question(
            question_id=q_id, session_id=UUID(session_id), text=q_data["text"],
            topic=q_data.get("topic", state["current_topic"]),
            category=q_data.get("category", "fundamentals"),
            difficulty=state["difficulty"],
            expected_keywords=q_data.get("expected_keywords", []),
            is_followup=q_data.get("is_followup", False), order=state["question_count"],
        ),
        state_snapshot=InterviewSession(
            session_id=UUID(session_id), candidate_id=UUID(state["candidate_id"]),
            role=state["role"], status=state["status"],
            current_state=state["current_state"], difficulty=state["difficulty"],
            current_topic=state["current_topic"], question_count=state["question_count"],
            technical_score=state.get("technical_score", 0.0),
            communication_score=state.get("communication_score", 0.0),
            confidence_score=state.get("confidence_score", 0.0),
            engagement_score=state.get("engagement_score", 0.0),
        ),
    )


# ── Session State ────────────────────────────────────────────────────

@router.get("/interview/{session_id}/state")
async def get_session_state(session_id: UUID):
    state = await _get_state(str(session_id))
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


# ── End Interview ────────────────────────────────────────────────────

@router.post("/interview/{session_id}/end", response_model=InterviewEndResponse)
async def end_interview(session_id: UUID):
    sid = str(session_id)
    state = await _get_state(sid)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state["status"] = "completed"
    state["current_state"] = "FINAL_FEEDBACK"
    await _set_state(sid, state)

    return InterviewEndResponse(session_id=session_id, status="completed")
