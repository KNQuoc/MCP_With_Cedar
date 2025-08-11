from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.clarify import RequirementsClarifier
from ..shared import GROUNDING_CONFIG, build_implementation_plan


class ConfirmRequirementsTool:
    name = "confirmRequirements"

    def __init__(self, clarifier: RequirementsClarifier) -> None:
        self.clarifier = clarifier

    def list_tool(self) -> McpTool:
        # Accept a map of checklist item id -> boolean
        return McpTool(
            name=self.name,
            description="Confirm that required Cedar setup requirements are satisfied",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmations": {
                        "type": "object",
                        "default": {},
                        "additionalProperties": {"type": "boolean"},
                        "description": "Map of checklist item id to confirmation boolean",
                    }
                },
                # Make confirmations optional; if omitted, we'll return the checklist template
                "required": [],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        confirmations: Dict[str, bool] = arguments.get("confirmations", {})
        if not confirmations:
            # Keep this tool as a minimal gate switch; do not return checklist here.
            payload = {
                "satisfied": False,
                "missing": ["confirmations"],
                "message": "Provide confirmations (from clarifyRequirements validation) to confirm and enable coding.",
                "grounding": GROUNDING_CONFIG,
            }
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        validation = self.clarifier.validate_confirmations(confirmations)
        
        # If requirements are satisfied, generate implementation plan
        if validation.get("satisfied"):
            plan = build_implementation_plan(confirmations)
            payload = {
                **validation,
                "plan": plan,
                "grounding": GROUNDING_CONFIG,
            }
        else:
            payload = {
                **validation,
                "grounding": GROUNDING_CONFIG,
            }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]


