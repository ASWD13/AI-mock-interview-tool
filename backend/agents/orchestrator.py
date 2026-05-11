"""Interview orchestrator — FSM + LangGraph based state management (§9)."""

from typing import Dict, Any, Optional
from uuid import UUID


class InterviewOrchestrator:
    """Orchestrates interview flow with FSM state transitions.

    FSM States:
        INTRODUCTION → RESUME_DISCUSSION → TECHNICAL_ROUND → BEHAVIORAL_ROUND → FINAL_FEEDBACK
    """

    # FSM transition rules
    TRANSITIONS = {
        "INTRODUCTION": {
            "condition": "after greeting + 1 warmup question",
            "next": "RESUME_DISCUSSION",
            "max_questions": 1,
        },
        "RESUME_DISCUSSION": {
            "condition": "after 2 questions",
            "next": "TECHNICAL_ROUND",
            "max_questions": 2,
        },
        "TECHNICAL_ROUND": {
            "condition": "total_questions >= 8 OR all focus_areas exhausted",
            "next": "BEHAVIORAL_ROUND",
            "max_questions": 8,
        },
        "BEHAVIORAL_ROUND": {
            "condition": "after 2-3 behavioral questions",
            "next": "FINAL_FEEDBACK",
            "max_questions": 3,
        },
        "FINAL_FEEDBACK": {
            "condition": "terminal",
            "next": None,
            "max_questions": 0,
        },
    }

    @staticmethod
    def should_transition(state: Dict[str, Any]) -> bool:
        """Check if the FSM should transition to next state."""
        current = state.get("current_state", "INTRODUCTION")
        transition = InterviewOrchestrator.TRANSITIONS.get(current)

        if not transition or not transition["next"]:
            return False

        question_count = state.get("question_count", 0)
        question_count_on_topic = state.get("question_count_on_topic", 0)

        if current == "INTRODUCTION":
            return question_count >= 1

        elif current == "RESUME_DISCUSSION":
            return question_count >= 3  # 1 intro + 2 resume

        elif current == "TECHNICAL_ROUND":
            # Transition after 8 total questions or all focus areas exhausted
            tech_questions = question_count - 3  # subtract intro + resume questions
            topic_queue = state.get("topic_queue", [])
            visited = state.get("visited_topics", [])
            all_exhausted = len(topic_queue) == 0 and len(visited) > 0

            return tech_questions >= 8 or all_exhausted

        elif current == "BEHAVIORAL_ROUND":
            behavioral_questions = state.get("behavioral_question_count", 0)
            return behavioral_questions >= 3

        return False

    @staticmethod
    def get_next_state(current_state: str) -> Optional[str]:
        """Get the next FSM state."""
        transition = InterviewOrchestrator.TRANSITIONS.get(current_state)
        if transition:
            return transition["next"]
        return None

    @staticmethod
    def transition(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FSM state transition."""
        if InterviewOrchestrator.should_transition(state):
            current = state["current_state"]
            next_state = InterviewOrchestrator.get_next_state(current)
            if next_state:
                state["current_state"] = next_state
                state["question_count_on_topic"] = 0

                if next_state == "BEHAVIORAL_ROUND":
                    state["behavioral_question_count"] = 0
                    state["current_topic"] = "behavioral"
                    state["difficulty"] = "medium"

                elif next_state == "FINAL_FEEDBACK":
                    state["status"] = "completed"

        return state
