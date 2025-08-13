from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.types import Tool as McpTool, TextContent

from ..services.feature import FeatureResolver
from ..shared import DEFAULT_INSTALL_COMMAND, format_tool_output


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
        # Add grounding directive and require doc-backed citations via a follow-up search
        directive = (
            "Map the goal to Cedar-OS features strictly based on the docs index. "
            "For each suggested feature, include supporting citations by calling searchDocs "
            "with the feature name to verify presence. If none found, mark as 'not in docs'. "
            f"Use '{DEFAULT_INSTALL_COMMAND}' as the default install command unless the user specifies another."
        )
        full_payload = {"prompt": prompt, "directive": directive, "features": mapping}
        formatted = format_tool_output(full_payload, keep_fields=["features"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

    @staticmethod
    def _build_prompt(goal: str, context: Optional[str]) -> str:
        ctx = f" Context: {context}" if context else ""
        return (
            "Map the goal to Cedar-OS features and explain why each is relevant. Goal: '"
            + goal
            + "'."
            + ctx
        )


