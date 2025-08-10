from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.types import Tool as McpTool, TextContent

from ..services.wizard import IntegrationWizard


class IntegrationWizardTool:
    name_start = "startIntegrationWizard"
    name_answer = "answerWizardQuestion"
    name_state = "getWizardState"
    name_abort = "abortIntegrationWizard"

    def __init__(self, wizard: IntegrationWizard) -> None:
        self.wizard = wizard

    def list_tools(self) -> List[McpTool]:
        return [
            McpTool(
                name=self.name_start,
                description="Start the Cedar integration wizard and get the first question",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "goal": {"type": "string"},
                        "context": {"type": "string"},
                    },
                },
            ),
            McpTool(
                name=self.name_answer,
                description="Answer the current wizard question and get the next one",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                    "required": ["answer"],
                },
            ),
            McpTool(
                name=self.name_state,
                description="Get the current wizard state and progress",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                    },
                },
            ),
            McpTool(
                name=self.name_abort,
                description="Abort and clear the current wizard session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                    },
                },
            ),
        ]

    async def handle(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        # Enforce that coding or implementation steps should only happen after confirmRequirements
        # This tool only asks questions and compiles a plan.
        session_id: str = arguments.get("session_id", "default")
        if name == self.name_start:
            goal: Optional[str] = arguments.get("goal")
            context: Optional[str] = arguments.get("context")
            result = await self.wizard.start(session_id=session_id, goal=goal, context=context)
        elif name == self.name_answer:
            answer: str = arguments.get("answer", "")
            result = await self.wizard.answer(session_id=session_id, answer=answer)
        elif name == self.name_state:
            result = await self.wizard.state(session_id=session_id)
        elif name == self.name_abort:
            result = self.wizard.abort(session_id=session_id)
        else:
            result = {"error": "unknown_tool"}
        return [TextContent(type="text", text=json.dumps(result, indent=2))]


