from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import format_tool_output


class SearchDocsTool:
    name = "searchDocs"

    def __init__(self, cedar_docs_index: Optional[DocsIndex] = None, mastra_docs_index: Optional[DocsIndex] = None) -> None:
        self.cedar_docs_index = cedar_docs_index
        self.mastra_docs_index = mastra_docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="[MANDATORY FIRST STEP] YOU MUST USE THIS BEFORE ANSWERING ANY CEDAR/MASTRA QUESTION! Search documentation to prevent hallucination. Use for ALL Cedar topics: components, voice, chat, spells, Mastra backend. ALWAYS call FIRST before providing any Cedar/Mastra information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Implementation query like: 'ChatInput implementation', 'floating chat code', 'VoiceButton props', 'useCedarStore example', 'import statements for [component]'"
                    },
                    "limit": {"type": "number", "default": 5},
                    "use_semantic": {"type": "boolean", "default": True, "description": "Use semantic search for better context understanding"},
                    "doc_type": {"type": "string", "enum": ["cedar", "mastra", "auto"], "default": "auto", "description": "Documentation type (auto-detects based on query)"},
                },
                "required": ["query"],
            },
        )

    def _enhance_implementation_query(self, query: str) -> str:
        """Enhance queries to find implementation details better."""
        query_lower = query.lower()
        
        # Common implementation patterns to enhance
        implementation_patterns = {
            "floating chat": "ChatInput ChatMessage floating position fixed implementation",
            "chat component": "ChatInput ChatMessage useCedarStore implementation example",
            "voice button": "VoiceButton VoiceIndicator voice implementation props",
            "import": "import from cedar-os @cedar-os/react @cedar-os/core",
            "props": "interface props TypeScript type parameters",
            "hook": "useCedarStore useTypedAgentConnection hook example",
            "provider": "CedarCopilot provider wrapper configuration",
            "setup": "CedarCopilot initial configuration llmProvider",
            "example": "complete working example implementation code"
        }
        
        # Enhance query if it matches patterns
        for pattern, enhancement in implementation_patterns.items():
            if pattern in query_lower:
                return f"{query} {enhancement}"
        
        # Add "implementation" or "example" if not present
        if "implementation" not in query_lower and "example" not in query_lower:
            query += " implementation example code"
            
        return query
    
    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        query: str = arguments.get("query", "")
        limit: int = int(arguments.get("limit", 5))
        use_semantic: bool = arguments.get("use_semantic", True)
        doc_type: str = arguments.get("doc_type", "auto")
        
        # Enhance query for better implementation results
        enhanced_query = self._enhance_implementation_query(query)
        
        # Auto-detect doc type based on query keywords
        if doc_type == "auto":
            doc_type = self._detect_doc_type(enhanced_query)
        
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
        
        prompt = self._build_prompt(enhanced_query, use_semantic, doc_name)
        results = await docs_index.search(enhanced_query, limit=limit, use_semantic=use_semantic)
        
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

        full_payload = {
            "prompt": prompt, 
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
    def _build_prompt(query: str, use_semantic: bool = True, doc_name: str = "Cedar-OS") -> str:
        search_type = "semantic similarity" if use_semantic else "keyword"
        return (
            f"Search the {doc_name} documentation using {search_type} search for the query and return the most relevant "
            f"sections with citations: '{query}'. "
            "If nothing matches, return no results so the caller can respond 'not in docs'."
        )


