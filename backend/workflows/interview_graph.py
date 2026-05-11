"""LangGraph interview workflow definition (§9)."""

from typing import TypedDict, Optional, List, Dict, Any


class InterviewState(TypedDict):
    """State schema for the LangGraph interview workflow."""
    session_id: str
    candidate_id: str
    role: str
    status: str
    current_state: str  # FSM state
    difficulty: str
    current_topic: str
    question_count: int
    question_count_on_topic: int
    technical_score: float
    communication_score: float
    confidence_score: float
    engagement_score: float
    weak_topics: List[str]
    strong_topics: List[str]
    question_history: List[str]
    topic_queue: List[str]
    visited_topics: List[str]
    consecutive_weak: int
    supportive_mode: bool
    current_question: Optional[Dict[str, Any]]
    current_answer: Optional[Dict[str, Any]]
    next_action: Optional[str]


# LangGraph node definitions per §9
def node_init(state: InterviewState) -> InterviewState:
    """Initialize interview: load profile, set difficulty=medium, topic=focus_areas[0]."""
    state["difficulty"] = "medium"
    state["current_state"] = "INTRODUCTION"
    state["question_count"] = 0
    state["consecutive_weak"] = 0
    state["supportive_mode"] = False
    return state


def node_generate_question(state: InterviewState) -> InterviewState:
    """Generate next question based on current state."""
    # Actual generation delegated to question_generator.py
    state["question_count"] += 1
    state["question_count_on_topic"] = state.get("question_count_on_topic", 0) + 1
    return state


def node_await_response(state: InterviewState) -> InterviewState:
    """Wait for candidate response (graph paused at this node)."""
    return state


def node_evaluate(state: InterviewState) -> InterviewState:
    """Evaluate the candidate's answer (technical + audio + vision)."""
    # Actual evaluation delegated to services
    return state


def node_adapt(state: InterviewState) -> InterviewState:
    """Adapt difficulty and determine next action."""
    # Delegated to difficulty_adapter.py
    return state


def node_transition(state: InterviewState) -> InterviewState:
    """Check and execute FSM state transitions."""
    from backend.agents.orchestrator import InterviewOrchestrator
    return InterviewOrchestrator.transition(state)


def node_generate_feedback(state: InterviewState) -> InterviewState:
    """Generate final feedback report."""
    state["status"] = "completed"
    state["current_state"] = "FINAL_FEEDBACK"
    return state


def should_continue(state: InterviewState) -> str:
    """Determine next edge in the graph."""
    if state.get("next_action") == "end" or state.get("current_state") == "FINAL_FEEDBACK":
        return "generate_feedback"
    return "generate_question"


# Graph construction (would use LangGraph StateGraph in production)
def build_interview_graph():
    """Build the LangGraph StateGraph for interview orchestration.

    Nodes:
    - node_init
    - node_generate_question
    - node_await_response
    - node_evaluate
    - node_adapt
    - node_transition
    - node_generate_feedback

    Edges follow the flow defined in §9.
    """
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(InterviewState)

        graph.add_node("init", node_init)
        graph.add_node("generate_question", node_generate_question)
        graph.add_node("await_response", node_await_response)
        graph.add_node("evaluate", node_evaluate)
        graph.add_node("adapt", node_adapt)
        graph.add_node("transition", node_transition)
        graph.add_node("generate_feedback", node_generate_feedback)

        graph.set_entry_point("init")
        graph.add_edge("init", "generate_question")
        graph.add_edge("generate_question", "await_response")
        graph.add_edge("await_response", "evaluate")
        graph.add_edge("evaluate", "adapt")
        graph.add_edge("adapt", "transition")
        graph.add_conditional_edges("transition", should_continue)
        graph.add_edge("generate_feedback", END)

        return graph.compile()

    except ImportError:
        print("LangGraph not available, using FSM-only orchestration")
        return None
