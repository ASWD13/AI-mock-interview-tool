"""Tests for technical evaluator and score aggregator."""

import pytest
from backend.scoring.score_aggregator import compute_final_scores


class TestScoreAggregator:
    def test_empty_answers(self):
        result = compute_final_scores([])
        assert result["final_score"] == 0.0
        assert result["rating"] == "Needs Improvement"

    def test_excellent_rating(self):
        class MockAnswer:
            correctness = 0.9
            depth = 0.85
            audio_scores = {"clarity": 0.9, "confidence": 0.85}
            vision_scores = {"engagement": 0.9}

        answers = [MockAnswer(), MockAnswer()]
        result = compute_final_scores(answers)
        assert result["rating"] == "Excellent"
        assert result["final_score"] >= 0.8

    def test_poor_rating(self):
        class MockAnswer:
            correctness = 0.2
            depth = 0.15
            audio_scores = {"clarity": 0.3, "confidence": 0.25}
            vision_scores = {"engagement": 0.2}

        answers = [MockAnswer(), MockAnswer()]
        result = compute_final_scores(answers)
        assert result["rating"] == "Needs Improvement"

    def test_weighted_formula(self):
        class MockAnswer:
            correctness = 1.0
            depth = 1.0
            audio_scores = {"clarity": 1.0, "confidence": 1.0}
            vision_scores = {"engagement": 1.0}

        result = compute_final_scores([MockAnswer()])
        assert abs(result["final_score"] - 1.0) < 0.01

    def test_score_clamping(self):
        class MockAnswer:
            correctness = 0.05
            depth = 0.02
            audio_scores = {"clarity": 0.01, "confidence": 0.01}
            vision_scores = {"engagement": 0.01}

        result = compute_final_scores([MockAnswer()])
        assert result["technical_score"] >= 0.1
        assert result["depth_score"] >= 0.1


class TestKeywordMatch:
    def test_keyword_hits(self):
        transcript = "The virtual DOM is used for diffing and reconciliation in React"
        expected = ["virtual DOM", "diffing", "fiber"]
        hits = [k for k in expected if k.lower() in transcript.lower()]
        miss = [k for k in expected if k.lower() not in transcript.lower()]
        assert "virtual DOM" in hits
        assert "diffing" in hits
        assert "fiber" in miss
        assert len(hits) / len(expected) == pytest.approx(2/3)
