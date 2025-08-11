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
            description="Search Cedar-OS documentation using semantic search (if available) or keyword search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "number", "default": 5},
                    "use_semantic": {"type": "boolean", "default": True, "description": "Use semantic search if available"},
                },
                "required": ["query"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query: str = arguments.get("query", "")
        limit: int = int(arguments.get("limit", 5))
        use_semantic: bool = arguments.get("use_semantic", True)
        prompt = self._build_prompt(query, use_semantic)
        results = await self.docs_index.search(query, limit=limit, use_semantic=use_semantic)
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
    def _build_prompt(query: str, use_semantic: bool = True) -> str:
        search_type = "semantic similarity" if use_semantic else "keyword"
        return (
            f"Search the Cedar-OS documentation using {search_type} search for the query and return the most relevant "
            f"sections with citations: '{query}'. "
            "If nothing matches, return no results so the caller can respond 'not in docs'."
        )


