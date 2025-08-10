from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import DOCS_GUIDANCE


class SearchDocsTool:
    name = "searchDocs"

    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="Search Cedar-OS documentation for relevant content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "number", "default": 5},
                },
                "required": ["query"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query: str = arguments.get("query", "")
        limit: int = int(arguments.get("limit", 5))
        prompt = self._build_prompt(query)
        results = await self.docs_index.search(query, limit=limit)
        # Enforce evidence-based response: if no results, explicitly say so
        if not results:
            payload = {
                "prompt": prompt,
                "results": [],
                "note": "not in docs",
            }
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        payload = {"prompt": prompt, "guidance": DOCS_GUIDANCE, "results": results}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    @staticmethod
    def _build_prompt(query: str) -> str:
        return (
            "Search the Cedar-OS documentation for the query and return the most relevant "
            f"sections from cedar-test/docs/cedar_llms_full.txt with citations: '{query}'. "
            "If nothing matches, return no results so the caller can respond 'not in docs'."
        )


