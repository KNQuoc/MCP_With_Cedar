from typing import List


CLARIFY_DIMENSIONS = [
    ("scope", [
        "What is the primary user goal?",
        "Which user journeys must be supported in v1?",
    ]),
    ("constraints", [
        "Do you have framework/version constraints (Next.js, React, Node.js)?",
        "Any security/compliance requirements?",
    ]),
    ("integration", [
        "How will this connect to your backend or AI provider?",
        "Do you need streaming or tool calling?",
    ]),
    ("ui_ux", [
        "Any UI patterns or components required (floating chat, inline, modal)?",
        "Accessibility or localization needs?",
    ]),
]


class RequirementsClarifier:
    async def suggest_questions(self, goal: str, known_constraints: List[str]) -> List[str]:
        goal_hint = goal.strip().lower()
        questions: List[str] = []

        # Include a goal echo for context
        if goal_hint:
            questions.append(f"To confirm, is this your goal: '{goal.strip()}'?")

        # Add generic coverage across dimensions
        for _dim, qs in CLARIFY_DIMENSIONS:
            questions.extend(qs)

        # Avoid asking about constraints the user already provided
        if known_constraints:
            lowered = [c.lower() for c in known_constraints]
            questions = [q for q in questions if not any(k in q.lower() for k in lowered)]

        # De-duplicate while preserving order
        seen = set()
        deduped = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                deduped.append(q)
        return deduped[:10]


