"""Pydantic request/response schemas for iphipi API."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ─── Candidate Profile ─────────────────────────────────────────

class ProjectSchema(BaseModel):
    title: str
    tech_stack: List[str] = []
    description: str = ""


class EducationSchema(BaseModel):
    degree: str
    institution: str
    year: str = ""


class CandidateProfile(BaseModel):
    candidate_id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    experience_level: Optional[str] = None  # fresher|junior|mid|senior
    years_experience: Optional[int] = None
    skills: List[str] = []
    skill_categories: Dict[str, List[str]] = {}
    projects: List[ProjectSchema] = []
    education: List[EducationSchema] = []
    certifications: List[str] = []
    possible_roles: List[str] = []
    focus_areas: List[str] = []
    weak_areas: List[str] = []
    profile_embedding: Optional[List[float]] = Field(None, exclude=True)

    model_config = {"from_attributes": True}


# ─── Interview Session ─────────────────────────────────────────

class InterviewSession(BaseModel):
    session_id: UUID
    candidate_id: UUID
    role: Optional[str] = None
    status: str = "active"
    current_state: str = "INTRODUCTION"
    difficulty: str = "medium"
    current_topic: Optional[str] = None
    question_count: int = 0
    technical_score: float = 0.0
    communication_score: float = 0.0
    confidence_score: float = 0.0
    engagement_score: float = 0.0
    weak_topics: List[str] = []
    strong_topics: List[str] = []
    question_history: List[str] = []
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Question ──────────────────────────────────────────────────

class Question(BaseModel):
    question_id: UUID
    session_id: UUID
    text: str
    topic: Optional[str] = None
    category: Optional[str] = None  # fundamentals|architecture|behavioral|scenario
    difficulty: Optional[str] = None  # easy|medium|hard
    expected_keywords: List[str] = []
    is_followup: bool = False
    parent_question_id: Optional[UUID] = None
    order: int = 0

    model_config = {"from_attributes": True}


# ─── Answer ────────────────────────────────────────────────────

class AudioScores(BaseModel):
    confidence: float = 0.65
    clarity: float = 0.65
    hesitation: float = 0.0
    speaking_rate_wpm: float = 0.0


class VisionScores(BaseModel):
    engagement: float = 0.65
    eye_contact: float = 0.65
    stress_indicator: float = 0.0


class Answer(BaseModel):
    answer_id: UUID
    question_id: UUID
    session_id: UUID
    transcript: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    correctness: float = 0.0
    depth: float = 0.0
    relevance: float = 0.0
    keyword_hits: List[str] = []
    keyword_miss: List[str] = []
    audio_scores: AudioScores = AudioScores()
    vision_scores: VisionScores = VisionScores()

    model_config = {"from_attributes": True}


# ─── Scoring ───────────────────────────────────────────────────

class ScoringOutput(BaseModel):
    session_id: UUID
    technical_score: float = 0.0
    depth_score: float = 0.0
    communication_score: float = 0.0
    confidence_score: float = 0.0
    engagement_score: float = 0.0
    final_score: float = 0.0
    rating: Optional[str] = None  # Excellent|Good|Average|Needs Improvement

    model_config = {"from_attributes": True}


# ─── Feedback ──────────────────────────────────────────────────

class TechnicalFeedbackItem(BaseModel):
    topic: str
    observation: str
    suggestion: str


class ObservationItem(BaseModel):
    observation: str
    suggestion: str


class FeedbackOutput(BaseModel):
    session_id: UUID
    overall_rating: Optional[str] = None
    technical_feedback: List[TechnicalFeedbackItem] = []
    communication_feedback: List[ObservationItem] = []
    behavioral_feedback: List[ObservationItem] = []
    improvement_plan: List[str] = []
    strengths: List[str] = []
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Job Recommendation ───────────────────────────────────────

class JobRecommendation(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: str = ""
    required_skills: List[str] = []
    match_score: float = 0.0
    why_matched: List[str] = []
    missing_skills: List[str] = []


# ─── Request Schemas ───────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    candidate_id: UUID
    role: Optional[str] = None


class InterviewResponseRequest(BaseModel):
    session_id: UUID
    question_id: UUID
    audio_b64: Optional[str] = None
    transcript: Optional[str] = None
    video_frame_b64: Optional[str] = None


# ─── Response Schemas ──────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    candidate_id: UUID
    profile: CandidateProfile


class InterviewStartResponse(BaseModel):
    session_id: UUID
    intro_message: str
    first_question: Question


class InterviewQuestionResponse(BaseModel):
    question: Question
    state_snapshot: InterviewSession


class InterviewResponseResponse(BaseModel):
    answer_id: UUID
    next_action: str  # continue|followup|shift_topic|end


class InterviewEndResponse(BaseModel):
    session_id: UUID
    status: str


class FeedbackReportResponse(BaseModel):
    scoring: ScoringOutput
    feedback: FeedbackOutput


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
