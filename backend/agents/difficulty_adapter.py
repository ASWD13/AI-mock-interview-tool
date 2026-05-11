"""Difficulty adapter — adaptive follow-up logic (§8.10, §9)."""

from typing import Dict, Any, Tuple, List


def adapt_difficulty(
    state: Dict[str, Any],
    eval_result: Dict[str, Any],
    audio_scores: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """Adapt difficulty and determine next action based on answer scores.

    Implements the exact adaptation rules from §9:
    - correctness < 0.4 → easier follow-up (difficulty - 1)
    - correctness > 0.8 AND depth > 0.7 → increase difficulty + deeper follow-up
    - consecutive_weak >= 2 → shift_topic
    - confidence < 0.4 → supportive mode
    - question_count_on_topic >= 3 → shift topic

    Args:
        state: Current session state dict
        eval_result: Answer evaluation scores
        audio_scores: Audio analysis scores

    Returns:
        Tuple of (next_action, updated_state)
    """
    correctness = eval_result.get("correctness", 0.5)
    depth = eval_result.get("depth", 0.5)
    confidence = audio_scores.get("confidence", 0.65)

    # Difficulty adjustment
    if correctness < 0.4:
        state["difficulty"] = _lower_difficulty(state.get("difficulty", "medium"))
        state["consecutive_weak"] = state.get("consecutive_weak", 0) + 1
    elif correctness > 0.8 and depth > 0.7:
        state["difficulty"] = _higher_difficulty(state.get("difficulty", "medium"))
        state["consecutive_weak"] = 0
    else:
        state["consecutive_weak"] = 0

    # Topic shifting on consecutive weak
    if state.get("consecutive_weak", 0) >= 2:
        state = _shift_topic(state)
        state["consecutive_weak"] = 0
        next_action = "shift_topic"
    # Topic shifting on max questions per topic
    elif state.get("question_count_on_topic", 0) >= 3:
        state = _shift_topic(state)
        state["question_count_on_topic"] = 0
        next_action = "shift_topic"
    # Follow-up logic
    elif correctness < 0.4:
        next_action = "followup"
    elif correctness > 0.8 and depth > 0.7:
        next_action = "followup"
    else:
        next_action = "continue"

    # Supportive mode
    if confidence < 0.4:
        state["supportive_mode"] = True
    else:
        state["supportive_mode"] = False

    # Check if we should end
    total_questions = state.get("question_count", 0)
    if total_questions >= 10:
        next_action = "end"
        state["current_state"] = "FINAL_FEEDBACK"

    # FSM transitions
    from backend.agents.orchestrator import InterviewOrchestrator
    state = InterviewOrchestrator.transition(state)

    if state.get("current_state") == "FINAL_FEEDBACK":
        next_action = "end"

    # Track weak/strong topics
    current_topic = state.get("current_topic", "")
    if correctness >= 0.7 and current_topic:
        strong = state.get("strong_topics", [])
        if current_topic not in strong:
            strong.append(current_topic)
        state["strong_topics"] = strong
    elif correctness < 0.4 and current_topic:
        weak = state.get("weak_topics", [])
        if current_topic not in weak:
            weak.append(current_topic)
        state["weak_topics"] = weak

    return next_action, state


def _lower_difficulty(current: str) -> str:
    """Decrease difficulty by one level."""
    levels = ["easy", "medium", "hard"]
    idx = levels.index(current) if current in levels else 1
    return levels[max(0, idx - 1)]


def _higher_difficulty(current: str) -> str:
    """Increase difficulty by one level."""
    levels = ["easy", "medium", "hard"]
    idx = levels.index(current) if current in levels else 1
    return levels[min(2, idx + 1)]


def _shift_topic(state: Dict[str, Any]) -> Dict[str, Any]:
    """Switch to next topic from the topic queue.

    Topic queue: focus_areas first, then weak_areas, then generic role topics.
    Never revisit unless queue exhausted.
    """
    current_topic = state.get("current_topic", "")
    topic_queue = state.get("topic_queue", [])
    visited_topics = state.get("visited_topics", [])

    # Push current to visited
    if current_topic and current_topic not in visited_topics:
        visited_topics.append(current_topic)

    # Pop next from queue
    if topic_queue:
        state["current_topic"] = topic_queue.pop(0)
    else:
        # Fallback to generic topics
        generic_topics = ["Problem Solving", "System Design", "Data Structures", "Algorithms"]
        for t in generic_topics:
            if t not in visited_topics:
                state["current_topic"] = t
                break
        else:
            # Loop back if everything visited
            if visited_topics:
                state["current_topic"] = visited_topics[0]

    state["topic_queue"] = topic_queue
    state["visited_topics"] = visited_topics
    state["question_count_on_topic"] = 0

    return state
