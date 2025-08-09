from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex


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
        payload = {"prompt": prompt, "results": results}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    @staticmethod
    def _build_prompt(query: str) -> str:
        return (
            "Search the Cedar-OS documentation for the query and return the most relevant"
            f" sections with citations: '{query}'."
        )


