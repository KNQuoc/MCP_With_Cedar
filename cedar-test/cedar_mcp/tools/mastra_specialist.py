from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import format_tool_output


class MastraSpecialistTool:
    name = "mastraSpecialist"

    def __init__(self, mastra_docs_index: DocsIndex) -> None:
        self.mastra_docs_index = mastra_docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="[MASTRA EXPERT - MANDATORY] YOU MUST USE THIS TOOL BEFORE ANSWERING ANY MASTRA QUESTIONS! I search Mastra docs for accurate backend information (agents, workflows, tools, memory). ALWAYS call me FIRST for Mastra topics to prevent hallucination.",
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
        
        # Enhance query with Mastra-specific terms
        enhanced_query = self._enhance_mastra_query(query)
        prompt = self._build_prompt(enhanced_query)
        results = await self.mastra_docs_index.search(enhanced_query, limit=limit, use_semantic=True)
        
        # If no results found, return helpful message
        if not results:
            # Check if simplified output is enabled
            import os
            simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
            if simplified_env.lower() == "true":
                # Don't include prompt in simplified mode
                simplified_output = {
                    "results": [],
                    "note": "No matching Mastra documentation found - try different search terms like 'agent', 'workflow', 'voice', 'memory', or 'tool'",
                    "suggestions": ["Mastra agent setup", "voice integration", "workflow configuration", "memory management", "tool creation"]
                }
                return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
            else:
                # Include prompt only in full mode
                full_payload = {
                    "prompt": prompt,
                    "results": [],
                    "note": "No matching Mastra documentation found - try different search terms like 'agent', 'workflow', 'voice', 'memory', or 'tool'",
                    "suggestions": ["Mastra agent setup", "voice integration", "workflow configuration", "memory management", "tool creation"]
                }
                formatted = format_tool_output(full_payload, keep_fields=["results", "note"])
                return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

        # Extract just the content text when simplified output is enabled
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Extract only the content field from each result
            text_contents = []
            for result in results:
                if isinstance(result, dict):
                    content = result.get("content", "")
                    if content:
                        text_contents.append(content)
            
            # Return simplified output with just the text
            simplified_output = {
                "results": text_contents,
                "INSTRUCTION": "BASE YOUR ANSWER ONLY ON THESE MASTRA DOCUMENTATION RESULTS"
            }
            return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
        
        # Original full output when not simplified
        # Only include prompt in full mode
        full_payload = {
            "results": results
        }
        # Add prompt only if not simplified
        if simplified_env.lower() != "true":
            full_payload["prompt"] = prompt
        
        formatted = format_tool_output(full_payload, keep_fields=["results"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

    def _enhance_mastra_query(self, query: str) -> str:
        """Enhance queries to find Mastra implementation details better."""
        query_lower = query.lower()
        
        # Common Mastra implementation patterns to enhance
        mastra_patterns = {
            "agent": "Agent new Agent model instructions voice tools workflow",
            "voice": "OpenAIVoice PlayAIVoice CompositeVoice speak listen audio stream transcription",
            "workflow": "workflow step node execution context memory tools",
            "tool": "tool function call parameter description schema validation",
            "memory": "memory semantic recall working memory context storage retrieval",
            "authentication": "jwt auth token user session login middleware",
            "setup": "Mastra installation configuration environment setup initialization",
            "api": "API endpoint route handler middleware request response",
            "database": "libsql postgres connection query schema migration",
            "integration": "MCP integration provider configuration connection setup"
        }
        
        # Enhance query if it matches patterns
        for pattern, enhancement in mastra_patterns.items():
            if pattern in query_lower:
                return f"{query} {enhancement}"
        
        # Add general Mastra context if not present
        if "mastra" not in query_lower:
            query += " mastra framework backend"
            
        return query

    @staticmethod
    def _build_prompt(query: str) -> str:
        return (
            f"Search the Mastra backend documentation for information about: '{query}'. "
            "Return relevant sections about agents, workflows, tools, memory, voice integration, MCP integration, "
            "authentication, database configuration, or other Mastra backend features. "
            "Include code examples and implementation details when available."
        )