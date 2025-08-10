from typing import List, Dict, Any, Optional

from .docs import DocsIndex
from ..shared import DEFAULT_INSTALL_COMMAND


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
    def __init__(self, docs_index: Optional[DocsIndex] = None) -> None:
        # Optional docs index (used to derive checklist presence/coverage)
        self.docs_index = docs_index

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

    def get_checklist(self) -> List[Dict[str, Any]]:
        """Return a minimal Cedar-OS setup checklist inferred from docs.

        This is intentionally lightweight and focuses on core requirements
        commonly referenced in cedar_llms_full.txt:
        - Provider configuration (OpenAI/AI SDK/Mastra)
        - Backend routes for chat/stream (if using a backend)
        - SSE headers for streaming
        - Structured outputs usage
        - Mentions/context wiring (if applicable)
        - Docs availability
        """
        checklist: List[Dict[str, Any]] = [
            {
                "id": "provider_config",
                "label": "LLM provider configured (openai/ai-sdk/mastra)",
                "required": True,
            },
            {
                "id": "install_policy",
                "label": f"Install command decided (default: {DEFAULT_INSTALL_COMMAND})",
                "required": True,
            },
            {
                "id": "backend_routes",
                "label": "Backend endpoints /chat and /chat/stream registered (if using backend)",
                "required": False,
            },
            {
                "id": "sse_headers",
                "label": "SSE headers set for streaming (Content-Type, Cache-Control, data: lines)",
                "required": False,
            },
            {
                "id": "structured_outputs",
                "label": "Structured outputs (object field) planned/validated for key steps",
                "required": True,
            },
            {
                "id": "mentions_context",
                "label": "Mentions/context providers wired if attaching brand docs/past posts",
                "required": False,
            },
            {
                "id": "docs_loaded",
                "label": "cedar_llms_full.txt indexed (DocsIndex)",
                "required": True,
                "detected": self._docs_present(),
            },
        ]
        return checklist

    def validate_confirmations(self, confirmations: Dict[str, bool]) -> Dict[str, Any]:
        """Validate a map of confirmations against the checklist.

        Returns { satisfied: bool, missing: [ids], details: [...] }
        """
        checklist = self.get_checklist()
        missing: List[str] = []
        details: List[Dict[str, Any]] = []

        for item in checklist:
            item_id = item["id"]
            required = bool(item.get("required", False))
            is_confirmed = bool(confirmations.get(item_id, False))

            # If docs detection exists for docs_loaded, combine with confirmation
            if item_id == "docs_loaded" and item.get("detected") is not None:
                is_confirmed = is_confirmed and bool(item.get("detected"))

            details.append({
                "id": item_id,
                "required": required,
                "confirmed": is_confirmed,
                "label": item.get("label"),
            })

            if required and not is_confirmed:
                missing.append(item_id)

        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "details": details,
        }

    def _docs_present(self) -> bool:
        try:
            if not self.docs_index:
                return False
            meta = self.docs_index.describe()
            sources = meta.get("sources", [])
            # Accept either an absolute path filename match or direct URL string
            return any("cedar_llms_full.txt" in str(s) for s in sources)
        except Exception:
            return False


