from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.clarify import RequirementsClarifier


class ClarifyRequirementsTool:
    name = "clarifyRequirements"

    def __init__(self, clarifier: RequirementsClarifier) -> None:
        self.clarifier = clarifier

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="Suggest clarifying questions to better understand requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "known_constraints": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["goal"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        goal: str = arguments.get("goal", "")
        known_constraints: List[str] = arguments.get("known_constraints", [])
        prompt = self._build_prompt(goal, known_constraints)
        questions = await self.clarifier.suggest_questions(goal, known_constraints)
        payload = {"prompt": prompt, "questions": questions}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    @staticmethod
    def _build_prompt(goal: str, known_constraints: List[str]) -> str:
        constraints_text = ", ".join(known_constraints) if known_constraints else "none"
        return (
            "Ask concise, high-signal questions to clarify requirements, covering scope,"
            " constraints, integration, and UI/UX. Goal: '"
            + goal
            + "'. Known constraints: "
            + constraints_text
            + "."
        )


