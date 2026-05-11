"""Tests for interview orchestrator and difficulty adapter."""

import pytest
from backend.agents.orchestrator import InterviewOrchestrator
from backend.agents.difficulty_adapter import adapt_difficulty


class TestOrchestrator:
    def test_introduction_transition(self):
        state = {"current_state": "INTRODUCTION", "question_count": 1}
        assert InterviewOrchestrator.should_transition(state) is True

    def test_introduction_no_transition(self):
        state = {"current_state": "INTRODUCTION", "question_count": 0}
        assert InterviewOrchestrator.should_transition(state) is False

    def test_resume_discussion_transition(self):
        state = {"current_state": "RESUME_DISCUSSION", "question_count": 3}
        assert InterviewOrchestrator.should_transition(state) is True

    def test_final_feedback_no_transition(self):
        state = {"current_state": "FINAL_FEEDBACK", "question_count": 20}
        assert InterviewOrchestrator.should_transition(state) is False

    def test_get_next_state(self):
        assert InterviewOrchestrator.get_next_state("INTRODUCTION") == "RESUME_DISCUSSION"
        assert InterviewOrchestrator.get_next_state("RESUME_DISCUSSION") == "TECHNICAL_ROUND"
        assert InterviewOrchestrator.get_next_state("TECHNICAL_ROUND") == "BEHAVIORAL_ROUND"
        assert InterviewOrchestrator.get_next_state("BEHAVIORAL_ROUND") == "FINAL_FEEDBACK"
        assert InterviewOrchestrator.get_next_state("FINAL_FEEDBACK") is None


class TestDifficultyAdapter:
    def test_lower_on_weak(self):
        state = {
            "difficulty": "medium", "consecutive_weak": 0,
            "question_count": 5, "current_state": "TECHNICAL_ROUND",
            "current_topic": "React", "topic_queue": ["Node.js"],
            "visited_topics": [], "question_count_on_topic": 1,
            "strong_topics": [], "weak_topics": [],
            "supportive_mode": False,
        }
        eval_result = {"correctness": 0.3, "depth": 0.2}
        audio_scores = {"confidence": 0.5}
        next_action, new_state = adapt_difficulty(state, eval_result, audio_scores)
        assert new_state["difficulty"] == "easy"

    def test_higher_on_strong(self):
        state = {
            "difficulty": "medium", "consecutive_weak": 0,
            "question_count": 5, "current_state": "TECHNICAL_ROUND",
            "current_topic": "React", "topic_queue": ["Node.js"],
            "visited_topics": [], "question_count_on_topic": 1,
            "strong_topics": [], "weak_topics": [],
            "supportive_mode": False,
        }
        eval_result = {"correctness": 0.9, "depth": 0.8}
        audio_scores = {"confidence": 0.8}
        next_action, new_state = adapt_difficulty(state, eval_result, audio_scores)
        assert new_state["difficulty"] == "hard"

    def test_topic_shift_on_consecutive_weak(self):
        state = {
            "difficulty": "easy", "consecutive_weak": 1,
            "question_count": 5, "current_state": "TECHNICAL_ROUND",
            "current_topic": "React", "topic_queue": ["Node.js", "SQL"],
            "visited_topics": [], "question_count_on_topic": 1,
            "strong_topics": [], "weak_topics": [],
            "supportive_mode": False,
        }
        eval_result = {"correctness": 0.2, "depth": 0.1}
        audio_scores = {"confidence": 0.5}
        next_action, new_state = adapt_difficulty(state, eval_result, audio_scores)
        assert next_action == "shift_topic"
        assert new_state["current_topic"] == "Node.js"

    def test_supportive_mode(self):
        state = {
            "difficulty": "medium", "consecutive_weak": 0,
            "question_count": 3, "current_state": "TECHNICAL_ROUND",
            "current_topic": "React", "topic_queue": [],
            "visited_topics": [], "question_count_on_topic": 1,
            "strong_topics": [], "weak_topics": [],
            "supportive_mode": False,
        }
        eval_result = {"correctness": 0.5, "depth": 0.5}
        audio_scores = {"confidence": 0.3}
        _, new_state = adapt_difficulty(state, eval_result, audio_scores)
        assert new_state["supportive_mode"] is True
