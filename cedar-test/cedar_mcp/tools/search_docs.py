from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import DOCS_GUIDANCE, format_tool_output


class SearchDocsTool:
    name = "searchDocs"

    def __init__(self, cedar_docs_index: Optional[DocsIndex] = None, mastra_docs_index: Optional[DocsIndex] = None) -> None:
        self.cedar_docs_index = cedar_docs_index
        self.mastra_docs_index = mastra_docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="ONLY for general Cedar/Mastra queries. NEVER use for: Spells/RadialMenu/useSpell (→spellsSpecialist), Voice/audio/microphone (→voiceSpecialist), Mastra-specific (→mastraSpecialist)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "number", "default": 5},
                    "use_semantic": {"type": "boolean", "default": True, "description": "Use semantic search if available"},
                    "doc_type": {"type": "string", "enum": ["cedar", "mastra", "auto"], "default": "auto", "description": "Documentation type to search (auto will detect based on query)"},
                },
                "required": ["query"],
            },
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query: str = arguments.get("query", "")
        limit: int = int(arguments.get("limit", 5))
        use_semantic: bool = arguments.get("use_semantic", True)
        doc_type: str = arguments.get("doc_type", "auto")
        
        # Auto-detect doc type based on query keywords
        if doc_type == "auto":
            doc_type = self._detect_doc_type(query)
        
        # Select the appropriate index
        if doc_type == "mastra" and self.mastra_docs_index:
            docs_index = self.mastra_docs_index
            doc_name = "Mastra"
        elif doc_type == "cedar" and self.cedar_docs_index:
            docs_index = self.cedar_docs_index
            doc_name = "Cedar-OS"
        else:
            # Fallback to Cedar if no specific match
            docs_index = self.cedar_docs_index
            doc_name = "Cedar-OS"
        
        if not docs_index:
            return [TextContent(type="text", text=json.dumps({
                "error": f"No {doc_name} documentation index available"
            }, indent=2))]
        
        prompt = self._build_prompt(query, use_semantic, doc_name)
        results = await docs_index.search(query, limit=limit, use_semantic=use_semantic)
        
        # Enforce evidence-based response: if no results, explicitly say so
        if not results:
            full_payload = {
                "prompt": prompt,
                "results": [],
                "note": f"not in {doc_name} docs",
                "doc_type": doc_type
            }
            formatted = format_tool_output(full_payload, keep_fields=["results", "note", "doc_type"])
            return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

        # Choose appropriate guidance based on doc type
        guidance = self._get_guidance(doc_type)
        
        full_payload = {
            "prompt": prompt, 
            "guidance": guidance, 
            "results": results,
            "doc_type": doc_type
        }
        formatted = format_tool_output(full_payload, keep_fields=["results", "doc_type"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

    @staticmethod
    def _detect_doc_type(query: str) -> str:
        """Detect whether to search Cedar or Mastra docs based on query keywords."""
        query_lower = query.lower()
        
        # Mastra-specific keywords
        mastra_keywords = [
            "mastra", "agent", "workflow", "tool", "memory", "mcp", 
            "jwt", "auth", "runtime", "context", "di", "dependency injection",
            "libsql", "postgres", "semantic recall", "working memory"
        ]
        
        # Cedar-specific keywords
        cedar_keywords = [
            "cedar", "voice", "chat", "copilot", "mention", "floating",
            "chatinput", "voiceindicator", "voicebutton", "voicesettings",
            "agentic state", "spell", "ui", "frontend", "react", "component"
        ]
        
        # Count keyword matches
        mastra_score = sum(1 for kw in mastra_keywords if kw in query_lower)
        cedar_score = sum(1 for kw in cedar_keywords if kw in query_lower)
        
        # Return based on highest score, defaulting to Cedar if equal
        if mastra_score > cedar_score:
            return "mastra"
        return "cedar"
    
    @staticmethod
    def _get_guidance(doc_type: str) -> Dict[str, Any]:
        """Get appropriate guidance based on documentation type."""
        if doc_type == "mastra":
            return {
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
        else:
            return DOCS_GUIDANCE

    @staticmethod
    def _build_prompt(query: str, use_semantic: bool = True, doc_name: str = "Cedar-OS") -> str:
        search_type = "semantic similarity" if use_semantic else "keyword"
        return (
            f"Search the {doc_name} documentation using {search_type} search for the query and return the most relevant "
            f"sections with citations: '{query}'. "
            "If nothing matches, return no results so the caller can respond 'not in docs'."
        )


