"""SQLAlchemy ORM models for iphipi."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    Text, JSON, ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class CandidateProfileDB(Base):
    """Candidate profile parsed from resume."""
    __tablename__ = "candidate_profiles"

    candidate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    experience_level = Column(String(50), nullable=True)  # fresher|junior|mid|senior
    years_experience = Column(Integer, nullable=True)
    skills = Column(JSON, default=list)
    skill_categories = Column(JSON, default=dict)
    projects = Column(JSON, default=list)
    education = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    possible_roles = Column(JSON, default=list)
    focus_areas = Column(JSON, default=list)
    weak_areas = Column(JSON, default=list)
    profile_embedding = Column(JSON, nullable=True)  # stored as list of floats
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSessionDB", back_populates="candidate")


class InterviewSessionDB(Base):
    """Interview session state."""
    __tablename__ = "interview_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.candidate_id"), nullable=False)
    role = Column(String(255), nullable=True)
    status = Column(String(50), default="active")  # active|completed
    current_state = Column(String(50), default="INTRODUCTION")
    difficulty = Column(String(50), default="medium")  # easy|medium|hard
    current_topic = Column(String(255), nullable=True)
    question_count = Column(Integer, default=0)
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    weak_topics = Column(JSON, default=list)
    strong_topics = Column(JSON, default=list)
    question_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    candidate = relationship("CandidateProfileDB", back_populates="sessions")
    questions = relationship("QuestionDB", back_populates="session")
    answers = relationship("AnswerDB", back_populates="session")
    feedback = relationship("FeedbackOutputDB", back_populates="session", uselist=False)
    scoring = relationship("ScoringOutputDB", back_populates="session", uselist=False)


class QuestionDB(Base):
    """Generated interview question."""
    __tablename__ = "questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.session_id"), nullable=False)
    text = Column(Text, nullable=False)
    topic = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)  # fundamentals|architecture|behavioral|scenario
    difficulty = Column(String(50), nullable=True)  # easy|medium|hard
    expected_keywords = Column(JSON, default=list)
    is_followup = Column(Boolean, default=False)
    parent_question_id = Column(UUID(as_uuid=True), nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSessionDB", back_populates="questions")
    answer = relationship("AnswerDB", back_populates="question", uselist=False)


class AnswerDB(Base):
    """Candidate answer with evaluation scores."""
    __tablename__ = "answers"

    answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.session_id"), nullable=False)
    transcript = Column(Text, nullable=True)
    audio_duration_sec = Column(Float, nullable=True)
    correctness = Column(Float, default=0.0)
    depth = Column(Float, default=0.0)
    relevance = Column(Float, default=0.0)
    keyword_hits = Column(JSON, default=list)
    keyword_miss = Column(JSON, default=list)
    audio_scores = Column(JSON, default=dict)
    vision_scores = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("QuestionDB", back_populates="answer")
    session = relationship("InterviewSessionDB", back_populates="answers")


class ScoringOutputDB(Base):
    """Final scoring output for a session."""
    __tablename__ = "scoring_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.session_id"), unique=True, nullable=False)
    technical_score = Column(Float, default=0.0)
    depth_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    rating = Column(String(50), nullable=True)  # Excellent|Good|Average|Needs Improvement
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSessionDB", back_populates="scoring")


class FeedbackOutputDB(Base):
    """Generated feedback report."""
    __tablename__ = "feedback_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.session_id"), unique=True, nullable=False)
    overall_rating = Column(String(50), nullable=True)
    technical_feedback = Column(JSON, default=list)
    communication_feedback = Column(JSON, default=list)
    behavioral_feedback = Column(JSON, default=list)
    improvement_plan = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSessionDB", back_populates="feedback")
