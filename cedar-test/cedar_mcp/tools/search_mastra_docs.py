from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.mastra_docs import MastraDocsIndex


class SearchMastraDocsTool:
    name = "searchMastraDocs"

    def __init__(self, mastra_docs_index: MastraDocsIndex) -> None:
        self.mastra_docs_index = mastra_docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="Search Mastra documentation for backend integration, agents, workflows, tools, and memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for Mastra concepts"},
                    "limit": {"type": "number", "default": 5},
                },
                "required": ["query"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query: str = arguments.get("query", "")
        limit: int = int(arguments.get("limit", 5))
        
        prompt = self._build_prompt(query)
        results = await self.mastra_docs_index.search(query, limit=limit)
        
        # If no results found, return helpful message
        if not results:
            payload = {
                "prompt": prompt,
                "results": [],
                "note": "No matching Mastra documentation found",
                "suggestion": "Try searching for: agents, workflows, tools, memory, MCP, authentication, or specific Mastra features"
            }
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        # Add guidance for Mastra-specific responses
        guidance = {
            "context": "Mastra backend framework documentation",
            "focus_areas": [
                "Agent creation and configuration",
                "Workflow orchestration",
                "Tool development",
                "Memory systems",
                "MCP integration",
                "Authentication (JWT, etc.)",
                "Runtime context and dependency injection"
            ],
            "response_format": "Provide implementation examples and code snippets when relevant"
        }
        
        payload = {
            "prompt": prompt,
            "guidance": guidance,
            "results": results
        }
        
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    @staticmethod
    def _build_prompt(query: str) -> str:
        return (
            f"Search the Mastra backend documentation for information about: '{query}'. "
            "Return relevant sections about agents, workflows, tools, memory, MCP integration, "
            "authentication, or other Mastra backend features. "
            "Include code examples and implementation details when available."
        )