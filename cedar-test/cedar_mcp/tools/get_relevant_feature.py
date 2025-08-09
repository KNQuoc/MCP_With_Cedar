from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.types import Tool as McpTool, TextContent

from ..services.feature import FeatureResolver


class GetRelevantFeatureTool:
    name = "getRelevantFeature"

    def __init__(self, feature_resolver: FeatureResolver) -> None:
        self.feature_resolver = feature_resolver

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="Identify relevant Cedar-OS feature(s) for a described goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "What the user wants to achieve"},
                    "context": {"type": "string", "description": "Optional project/context details"},
                },
                "required": ["goal"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        goal: str = arguments.get("goal", "")
        context: Optional[str] = arguments.get("context")
        prompt = self._build_prompt(goal, context)
        mapping = await self.feature_resolver.map_goal_to_features(goal, context)
        payload = {"prompt": prompt, "features": mapping}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    @staticmethod
    def _build_prompt(goal: str, context: Optional[str]) -> str:
        ctx = f" Context: {context}" if context else ""
        return (
            "Map the goal to Cedar-OS features and explain why each is relevant. Goal: '"
            + goal
            + "'."
            + ctx
        )


