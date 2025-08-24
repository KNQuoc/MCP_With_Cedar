from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import format_tool_output


class ContextSpecialistTool:
    """Modular Agent Input Context specialist that leverages documentation search"""
    
    name = "contextSpecialist"
    
    # Core context-related search terms for documentation
    CONTEXT_SEARCH_TERMS = {
        "hooks": ["useSubscribeStateToInputContext", "useStateBasedMentionProvider", "useCedarState", "useRegisterState", "getAgentInputContext", "clearAgentInputContext"],
        "mentions": ["mention", "@mention", "mention provider", "trigger", "labelField", "searchFields", "renderMenuItem", "renderContextBadge"],
        "state": ["subscribed state", "state subscription", "mapFn", "transform", "context entries", "state changes", "application state"],
        "context": ["agent input context", "context data", "contextual information", "additional context", "context stringification"],
        "configuration": ["icon", "color", "order", "priority", "showInChat", "description", "metadata"],
        "integration": ["AI agent", "context flow", "agent response", "context payload", "context size", "Cedar Store"]
    }
    
    # High-level guidance categories
    GUIDANCE_CATEGORIES = {
        "setup": "Initial setup and configuration of Agent Input Context",
        "mentions": "Implementing and customizing mention providers",
        "subscription": "Subscribing state to agent context",
        "transformation": "Transforming and mapping state data",
        "troubleshooting": "Common issues and debugging approaches",
        "patterns": "Implementation patterns and best practices"
    }
    
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index
    
    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="[CONTEXT EXPERT - MANDATORY] YOU MUST USE THIS TOOL BEFORE ANSWERING ANY AGENT INPUT CONTEXT QUESTIONS! I search Cedar docs for accurate Agent Input Context information (mentions, state subscription, context transformation). ALWAYS call me FIRST for context/mentions/subscription topics to prevent hallucination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "guide", "troubleshoot", "explore"],
                        "description": "Action: search docs, get implementation guide, troubleshoot issue, or explore context features"
                    },
                    "query": {
                        "type": "string",
                        "description": "Your specific question or search query about Agent Input Context"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["mentions", "subscription", "transformation", "setup", "general"],
                        "default": "general",
                        "description": "Area to focus the search on"
                    }
                },
                "required": ["action", "query"]
            }
        )
    
    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        action = arguments.get("action", "search")
        query = arguments.get("query", "")
        focus = arguments.get("focus", "general")
        
        if action == "search":
            return await self._search_context_documentation(query, focus)
        elif action == "guide":
            return await self._provide_implementation_guide(query, focus)
        elif action == "troubleshoot":
            return await self._help_troubleshoot(query, focus)
        elif action == "explore":
            return await self._explore_context_features(query, focus)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown action: {action}"}))]
    
    async def _search_context_documentation(self, query: str, focus: str) -> List[TextContent]:
        """Search documentation with context-specific focus"""
        
        # Build enhanced search query based on focus area
        search_terms = self._build_search_query(query, focus)
        
        # Perform documentation search
        results = await self.docs_index.search(search_terms, limit=8, use_semantic=True)
        
        # Filter and rank results based on context relevance
        context_results = self._filter_context_results(results)
        
        # Extract just the content text when simplified output is enabled
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Extract only the content field from each result
            text_contents = []
            for result in context_results:
                if isinstance(result, dict):
                    content = result.get("content", "")
                    if content:
                        text_contents.append(content)
            
            # Return simplified output with just the text
            simplified_output = {
                "results": text_contents,
                "INSTRUCTION": "BASE YOUR ANSWER ONLY ON THESE AGENT INPUT CONTEXT DOCUMENTATION RESULTS"
            }
            return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
        
        # Return primarily documentation results
        full_payload = {
            "action": "search",
            "query": query,
            "focus": focus,
            "search_terms_used": search_terms,
            "results": context_results
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["results"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _provide_implementation_guide(self, query: str, focus: str) -> List[TextContent]:
        """Provide implementation guidance based on documentation"""
        
        # Search for implementation examples and patterns
        search_query = f"{query} implementation example code setup configuration Agent Input Context"
        docs_results = await self.docs_index.search(search_query, limit=5, use_semantic=True)
        
        # Extract just the content text when simplified output is enabled
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Extract only the content field from each result
            text_contents = []
            for result in docs_results:
                if isinstance(result, dict):
                    content = result.get("content", "")
                    if content:
                        text_contents.append(content)
            
            # Return simplified output with just the text
            simplified_output = {
                "documentation": text_contents,
                "INSTRUCTION": "BASE YOUR ANSWER ONLY ON THESE AGENT INPUT CONTEXT DOCUMENTATION RESULTS"
            }
            return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
        
        # Return documentation results
        full_payload = {
            "action": "guide",
            "topic": query,
            "focus": focus,
            "documentation": docs_results
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _help_troubleshoot(self, query: str, focus: str) -> List[TextContent]:
        """Help troubleshoot context-related issues"""
        
        # Search for error and troubleshooting documentation
        error_query = f"{query} error troubleshoot fix issue problem solution context state mention"
        docs_results = await self.docs_index.search(error_query, limit=5, use_semantic=True)
        
        # Return documentation for troubleshooting
        full_payload = {
            "action": "troubleshoot",
            "issue": query,
            "focus": focus,
            "documentation": docs_results
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _explore_context_features(self, query: str, focus: str) -> List[TextContent]:
        """Explore Agent Input Context features and capabilities"""
        
        # Broad search to explore context features
        explore_query = f"Agent Input Context {query} features capabilities mentions subscription state"
        docs_results = await self.docs_index.search(explore_query, limit=10, use_semantic=True)
        
        full_payload = {
            "action": "explore",
            "topic": query,
            "focus": focus,
            "documentation": docs_results
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    def _build_search_query(self, base_query: str, focus: str) -> str:
        """Build an enhanced search query based on focus area"""
        focus_terms = {
            "mentions": " ".join(self.CONTEXT_SEARCH_TERMS["mentions"][:3]),
            "subscription": "useSubscribeStateToInputContext useCedarState state subscription",
            "transformation": "mapFn transform context entries state changes",
            "setup": "Agent Input Context setup configuration initial",
            "general": "Agent Input Context mentions subscription state"
        }
        
        additional_terms = focus_terms.get(focus, "Agent Input Context")
        return f"{base_query} {additional_terms}"
    
    def _filter_context_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and prioritize context-related results"""
        context_results = []
        other_results = []
        
        for result in results:
            # Safely get content and heading with default empty strings
            content_str = str(result.get("content", "") or "")
            heading_str = str(result.get("heading", "") or "")
            content = (content_str + " " + heading_str).lower()
            
            # Check for context-related content
            context_score = sum(
                1 for category in self.CONTEXT_SEARCH_TERMS.values()
                for term in category
                if term.lower() in content
            )
            
            if context_score > 0:
                result["context_relevance"] = context_score
                context_results.append(result)
            else:
                other_results.append(result)
        
        # Sort by context relevance
        context_results.sort(key=lambda x: x.get("context_relevance", 0), reverse=True)
        
        # Return context results first, then others
        return context_results[:7] + other_results[:3]
    
    def _get_contextual_guidance(self, query: str, focus: str) -> str:
        """Provide contextual guidance based on query and focus"""
        query_lower = query.lower()
        
        if "mention" in query_lower:
            return "Mentions allow users to reference data with @ symbols. Use useStateBasedMentionProvider with registered state to enable mentions."
        elif "subscribe" in query_lower or "subscription" in query_lower:
            return "useSubscribeStateToInputContext automatically adds application state to agent context. Transform sensitive data before subscribing."
        elif "transform" in query_lower or "mapfn" in query_lower:
            return "Use mapFn parameter to transform state before adding to context. This is crucial for filtering sensitive data and optimizing payload size."
        elif focus == "mentions":
            return "Cedar mentions system requires state registration first via useCedarState. Configure trigger, labelField, and searchFields for customization."
        elif focus == "subscription":
            return "State subscription monitors changes and updates context automatically. Use meaningful keys and optimize large datasets."
        elif focus == "transformation":
            return "Transform functions shape how state appears in context. Filter sensitive fields and structure data for AI consumption."
        else:
            return "Agent Input Context enriches AI responses with application state, mentions, and additional data. Search documentation for specific implementation details."
    
    def _suggest_related_topics(self, query: str, focus: str) -> List[str]:
        """Suggest related topics to explore"""
        suggestions = []
        
        # Base suggestions on focus
        if focus == "mentions":
            suggestions = ["Mention provider configuration", "Custom mention rendering", "Multiple mention types"]
        elif focus == "subscription":
            suggestions = ["State change monitoring", "Context update lifecycle", "Performance optimization"]
        elif focus == "transformation":
            suggestions = ["Data filtering patterns", "Context structure", "Sensitive data handling"]
        else:
            suggestions = ["Mention providers", "State subscription", "Context transformation"]
        
        # Add query-specific suggestions
        query_lower = query.lower()
        if "provider" in query_lower:
            suggestions.append("useStateBasedMentionProvider usage")
        if "state" in query_lower:
            suggestions.append("useCedarState registration")
        if "error" in query_lower:
            suggestions.append("Troubleshooting context issues")
            
        return suggestions[:5]
    
    def _suggest_next_steps(self, results: List[Dict[str, Any]], focus: str) -> List[str]:
        """Suggest next steps based on search results"""
        if not results:
            return [
                "Try searching with different keywords",
                "Explore Agent Input Context documentation",
                "Check the Cedar context overview"
            ]
        
        steps = []
        if focus == "setup":
            steps = [
                "Register state with useCedarState",
                "Configure mention providers",
                "Subscribe state to context"
            ]
        elif focus == "mentions":
            steps = [
                "Register state first",
                "Configure mention provider",
                "Test @ mentions in chat"
            ]
        elif focus == "subscription":
            steps = [
                "Define state structure",
                "Implement transform function",
                "Subscribe with useSubscribeStateToInputContext"
            ]
        else:
            steps = [
                "Review the documentation results",
                "Try the suggested search terms",
                "Explore related topics"
            ]
            
        return steps
    
    def _get_implementation_overview(self, query: str, focus: str) -> str:
        """Provide implementation overview"""
        overviews = {
            "mentions": "Mentions require state registration via useCedarState, then useStateBasedMentionProvider to enable @ references in chat.",
            "subscription": "useSubscribeStateToInputContext monitors state and adds it to agent context. Use mapFn for transformation.",
            "transformation": "Transform functions filter and shape state data. Return object with meaningful keys for AI context.",
            "setup": "Start with useCedarState to register state, add mention providers, then subscribe state to context.",
            "general": "Agent Input Context provides state, mentions, and additional data to AI agents for richer responses."
        }
        return overviews.get(focus, overviews["general"])
    
    def _identify_key_concepts(self, query: str, focus: str) -> List[str]:
        """Identify key concepts to understand"""
        concepts = {
            "mentions": ["State registration", "Mention providers", "Trigger configuration", "Search fields"],
            "subscription": ["State monitoring", "Context updates", "Transform functions", "Performance"],
            "transformation": ["mapFn parameter", "Data filtering", "Context structure", "Sensitive data"],
            "setup": ["useCedarState", "Provider configuration", "State subscription", "Context flow"],
            "general": ["Agent context", "Mentions", "State subscription", "Data transformation"]
        }
        return concepts.get(focus, concepts["general"])
    
    def _get_search_suggestions(self, query: str, focus: str) -> List[str]:
        """Get search suggestions for finding more information"""
        base_suggestions = [
            f"Agent Input Context {focus}",
            f"{query} implementation example",
            f"{query} Cedar context"
        ]
        
        # Add focus-specific suggestions
        if focus == "mentions":
            base_suggestions.extend([f"{hook} usage" for hook in self.CONTEXT_SEARCH_TERMS["hooks"][:3]])
        elif focus == "subscription":
            base_suggestions.extend(["useSubscribeStateToInputContext example", "state monitoring patterns"])
        
        return base_suggestions[:6]
    
    def _suggest_common_patterns(self, focus: str) -> List[str]:
        """Suggest common implementation patterns"""
        patterns = {
            "mentions": [
                "Basic @ mentions with state",
                "Multiple mention types",
                "Custom mention rendering"
            ],
            "subscription": [
                "Simple state subscription",
                "Filtered state with mapFn",
                "Multiple state subscriptions"
            ],
            "transformation": [
                "Filter sensitive fields",
                "Flatten nested objects",
                "Aggregate multiple states"
            ],
            "general": [
                "Basic context setup",
                "Mentions with subscribed state",
                "Complex context transformation"
            ]
        }
        return patterns.get(focus, patterns["general"])
    
    def _create_implementation_checklist(self, query: str, focus: str) -> List[str]:
        """Create implementation checklist"""
        base_checklist = [
            "Cedar installed and configured",
            "State management setup",
            "AI agent integration ready"
        ]
        
        if focus == "mentions":
            base_checklist.extend([
                "State registered with useCedarState",
                "Mention provider configured",
                "Trigger and fields defined",
                "Mentions working in chat"
            ])
        elif focus == "subscription":
            base_checklist.extend([
                "State structure defined",
                "Transform function implemented",
                "State subscribed to context",
                "Context updates verified"
            ])
        elif focus == "transformation":
            base_checklist.extend([
                "Sensitive data identified",
                "mapFn function created",
                "Output structure optimized",
                "Context size checked"
            ])
            
        return base_checklist
    
    def _analyze_potential_causes(self, query: str) -> List[str]:
        """Analyze potential causes of issues"""
        query_lower = query.lower()
        causes = []
        
        if "mention" in query_lower:
            causes.extend([
                "State not registered with useCedarState",
                "Mention provider not configured",
                "Incorrect trigger or field configuration"
            ])
        if "context" in query_lower and ("not" in query_lower or "missing" in query_lower):
            causes.extend([
                "State not subscribed to context",
                "Transform function returning undefined",
                "Context not being accessed correctly"
            ])
        if "error" in query_lower:
            causes.extend([
                "Invalid state structure",
                "Transform function error",
                "Context size limit exceeded"
            ])
            
        return causes or ["Configuration issue", "State registration problem", "Context subscription error"]
    
    def _extract_error_keywords(self, query: str) -> List[str]:
        """Extract keywords from error descriptions"""
        # Simple keyword extraction
        words = query.lower().split()
        keywords = []
        
        for word in words:
            if len(word) > 3 and word not in ["the", "and", "not", "working", "doesn't", "won't"]:
                keywords.append(word)
                
        return keywords[:5]
    
    def _get_diagnostic_steps(self, query: str, focus: str) -> List[str]:
        """Get diagnostic steps for troubleshooting"""
        steps = [
            "Check browser console for errors",
            "Verify state registration",
            "Inspect context in DevTools"
        ]
        
        if focus == "mentions":
            steps.extend([
                "Verify state is registered",
                "Check mention provider configuration",
                "Test trigger in chat input"
            ])
        elif focus == "subscription":
            steps.extend([
                "Log transform function output",
                "Monitor state changes",
                "Check context updates"
            ])
            
        return steps
    
    def _get_common_solutions(self, query: str) -> List[str]:
        """Get common solutions for issues"""
        query_lower = query.lower()
        solutions = []
        
        if "mention" in query_lower:
            solutions = [
                "Register state before creating mention provider",
                "Ensure labelField matches state property",
                "Check trigger configuration"
            ]
        elif "subscription" in query_lower or "subscribe" in query_lower:
            solutions = [
                "Return valid object from mapFn",
                "Use meaningful context keys",
                "Filter large datasets"
            ]
        else:
            solutions = [
                "Review Agent Input Context docs",
                "Check state registration order",
                "Verify transform functions" 
            ]
            
        return solutions
    
    def _suggest_debugging_approach(self, focus: str) -> str:
        """Suggest debugging approach"""
        approaches = {
            "mentions": "Use React DevTools to inspect mention provider state. Log registered states and verify configuration.",
            "subscription": "Log transform function inputs/outputs. Monitor context updates in browser DevTools.",
            "transformation": "Test mapFn in isolation. Verify output structure and check for undefined values.",
            "general": "Start with console logs, check state registration, verify context flow, test in isolation."
        }
        return approaches.get(focus, approaches["general"])
    
    def _list_available_features(self, focus: str) -> List[str]:
        """List available context features"""
        features = {
            "mentions": self.CONTEXT_SEARCH_TERMS["mentions"],
            "hooks": self.CONTEXT_SEARCH_TERMS["hooks"],
            "configuration": self.CONTEXT_SEARCH_TERMS["configuration"],
            "general": [
                "State subscription",
                "@ mentions system",
                "Context transformation",
                "Multiple context sources",
                "Automatic updates",
                "Custom rendering"
            ]
        }
        return features.get(focus, features["general"])
    
    def _get_hook_categories(self) -> Dict[str, List[str]]:
        """Get hook categories"""
        return {
            "State Management": ["useCedarState", "useRegisterState"],
            "Context Subscription": ["useSubscribeStateToInputContext"],
            "Mention System": ["useStateBasedMentionProvider"],
            "Context Access": ["getAgentInputContext", "clearAgentInputContext"]
        }
    
    def _get_integration_points(self) -> List[str]:
        """Get integration points"""
        return [
            "React state management",
            "Cedar Store integration",
            "AI agent communication",
            "Chat input interface",
            "Context transformation layer"
        ]
    
    def _suggest_learning_path(self, query: str, focus: str) -> List[str]:
        """Suggest learning path"""
        paths = {
            "setup": [
                "Understand Cedar state management",
                "Register application state",
                "Configure mention providers",
                "Subscribe state to context",
                "Test with AI agents"
            ],
            "mentions": [
                "Register state with useCedarState",
                "Create basic mention provider",
                "Configure trigger and fields",
                "Customize mention rendering",
                "Handle multiple mention types"
            ],
            "subscription": [
                "Learn state subscription basics",
                "Implement transform functions",
                "Optimize context payloads",
                "Handle state updates",
                "Debug context flow"
            ],
            "general": [
                "Understand Agent Input Context",
                "Try basic state subscription",
                "Add mention providers",
                "Transform complex state",
                "Optimize for production"
            ]
        }
        return paths.get(focus, paths["general"])