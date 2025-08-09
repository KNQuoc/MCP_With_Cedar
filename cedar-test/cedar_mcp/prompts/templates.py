from typing import List, Optional


def build_search_docs_prompt(query: str) -> str:
    return (
        "Search the Cedar-OS documentation for the query and return the most relevant"
        " sections with citations: '" + query + "'."
    )


def build_get_relevant_feature_prompt(goal: str, context: Optional[str]) -> str:
    ctx = f" Context: {context}" if context else ""
    return (
        "Map the goal to Cedar-OS features and explain why each is relevant. Goal: '"
        + goal
        + "'."
        + ctx
    )


def build_clarify_requirements_prompt(goal: str, known_constraints: List[str]) -> str:
    constraints_text = ", ".join(known_constraints) if known_constraints else "none"
    return (
        "Ask concise, high-signal questions to clarify requirements, covering scope,"
        " constraints, integration, and UI/UX. Goal: '"
        + goal
        + "'. Known constraints: "
        + constraints_text
        + "."
    )


