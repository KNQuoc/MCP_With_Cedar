from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import format_tool_output


class VoiceSpecialistTool:
    """Modular voice development assistant that leverages documentation search"""
    
    name = "voiceSpecialist"
    
    # Core voice-related search terms for documentation
    VOICE_SEARCH_TERMS = {
        "components": ["VoiceIndicator", "VoiceButton", "VoiceSettings", "VoiceStatusPanel", "VoiceWaveform", "ChatInput"],
        "features": ["voice", "microphone", "audio", "recording", "transcription", "speech", "whisper", "realtime"],
        "states": ["isListening", "isSpeaking", "voicePermissionStatus", "voiceError", "transcription"],
        "methods": ["toggleVoice", "startListening", "stopListening", "requestMicrophonePermission", "updateVoiceSettings"],
        "permissions": ["granted", "denied", "not-supported", "prompt"],
        "integration": ["WebRTC", "OpenAI", "TTS", "STT", "WebSocket", "voice endpoint"]
    }
    
    # High-level guidance categories
    GUIDANCE_CATEGORIES = {
        "setup": "Installation and initial configuration of voice features",
        "components": "Voice UI components and their usage",
        "permissions": "Microphone permissions and browser compatibility",
        "integration": "Backend integration and API configuration",
        "troubleshooting": "Common issues and debugging approaches",
        "patterns": "Implementation patterns and best practices"
    }
    
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index
    
    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="[VOICE EXPERT - MANDATORY] YOU MUST USE THIS TOOL BEFORE ANSWERING ANY VOICE QUESTIONS! I search Cedar docs for accurate Voice information (audio, microphone, transcription). ALWAYS call me FIRST for voice/audio/VoiceIndicator topics to prevent hallucination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "guide", "troubleshoot", "explore"],
                        "description": "Action: search docs, get implementation guide, troubleshoot issue, or explore voice features"
                    },
                    "query": {
                        "type": "string",
                        "description": "Your specific question or search query about voice features"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["components", "permissions", "integration", "setup", "general"],
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
            return await self._search_voice_documentation(query, focus)
        elif action == "guide":
            return await self._provide_implementation_guide(query, focus)
        elif action == "troubleshoot":
            return await self._help_troubleshoot(query, focus)
        elif action == "explore":
            return await self._explore_voice_features(query, focus)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown action: {action}"}))]
    
    async def _search_voice_documentation(self, query: str, focus: str) -> List[TextContent]:
        """Search documentation with voice-specific context"""
        
        # Build enhanced search query based on focus area
        search_terms = self._build_search_query(query, focus)
        
        # Perform documentation search
        results = await self.docs_index.search(search_terms, limit=8, use_semantic=True)
        
        # Filter and rank results based on voice relevance
        voice_results = self._filter_voice_results(results)
        
        # Extract just the content text when simplified output is enabled
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Extract only the content field from each result
            text_contents = []
            for result in voice_results:
                if isinstance(result, dict):
                    content = result.get("content", "")
                    if content:
                        text_contents.append(content)
            
            # Return simplified output with just the text
            simplified_output = {
                "results": text_contents,
                "INSTRUCTION": "BASE YOUR ANSWER ONLY ON THESE VOICE DOCUMENTATION RESULTS"
            }
            return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
        
        # Return primarily documentation results
        # Only include internal fields in debug mode
        if simplified_env.lower() == "true":
            # Simplified mode - only essential fields
            full_payload = {
                "results": voice_results
            }
        else:
            # Debug mode - include all fields
            full_payload = {
                "action": "search",
                "query": query,
                "focus": focus,
                "search_terms_used": search_terms,
                "results": voice_results
            }
        
        formatted = format_tool_output(full_payload, keep_fields=["results"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _provide_implementation_guide(self, query: str, focus: str) -> List[TextContent]:
        """Provide implementation guidance based on documentation"""
        
        # Search for implementation examples and patterns
        search_query = f"{query} implementation example code setup configuration"
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
                "INSTRUCTION": "BASE YOUR ANSWER ONLY ON THESE VOICE DOCUMENTATION RESULTS"
            }
            return [TextContent(type="text", text=json.dumps(simplified_output, indent=2))]
        
        # Return documentation results
        # Only include internal fields in debug mode
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Simplified mode - only essential fields
            full_payload = {
                "documentation": docs_results
            }
        else:
            # Debug mode - include all fields
            full_payload = {
                "action": "guide",
                "topic": query,
                "focus": focus,
                "documentation": docs_results
            }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _help_troubleshoot(self, query: str, focus: str) -> List[TextContent]:
        """Help troubleshoot voice-related issues"""
        
        # Search for error and troubleshooting documentation
        error_query = f"{query} error troubleshoot fix issue problem solution"
        docs_results = await self.docs_index.search(error_query, limit=5, use_semantic=True)
        
        # Return documentation for troubleshooting
        # Only include internal fields in debug mode
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Simplified mode - only essential fields
            full_payload = {
                "documentation": docs_results
            }
        else:
            # Debug mode - include all fields
            full_payload = {
                "action": "troubleshoot",
                "issue": query,
                "focus": focus,
                "documentation": docs_results
            }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _explore_voice_features(self, query: str, focus: str) -> List[TextContent]:
        """Explore voice features and capabilities"""
        
        # Broad search to explore voice features
        explore_query = f"voice {query} features capabilities components"
        docs_results = await self.docs_index.search(explore_query, limit=10, use_semantic=True)
        
        # Only include internal fields in debug mode
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        if simplified_env.lower() == "true":
            # Simplified mode - only essential fields
            full_payload = {
                "documentation": docs_results
            }
        else:
            # Debug mode - include all fields
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
            "components": " ".join(self.VOICE_SEARCH_TERMS["components"][:3]),
            "permissions": "microphone permission getUserMedia browser",
            "integration": "WebSocket API endpoint OpenAI configuration",
            "setup": "install cedar plant-seed voice configuration",
            "general": "voice audio microphone"
        }
        
        additional_terms = focus_terms.get(focus, "voice")
        return f"{base_query} {additional_terms}"
    
    def _filter_voice_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and prioritize voice-related results"""
        voice_results = []
        other_results = []
        
        for result in results:
            # Safely get content and heading with default empty strings
            content_str = str(result.get("content", "") or "")
            heading_str = str(result.get("heading", "") or "")
            content = (content_str + " " + heading_str).lower()
            
            # Check for voice-related content
            voice_score = sum(
                1 for category in self.VOICE_SEARCH_TERMS.values()
                for term in category
                if term.lower() in content
            )
            
            if voice_score > 0:
                result["voice_relevance"] = voice_score
                voice_results.append(result)
            else:
                other_results.append(result)
        
        # Sort by voice relevance
        voice_results.sort(key=lambda x: x.get("voice_relevance", 0), reverse=True)
        
        # Return voice results first, then others
        return voice_results[:7] + other_results[:3]
    
    def _get_contextual_guidance(self, query: str, focus: str) -> str:
        """Provide contextual guidance based on query and focus"""
        query_lower = query.lower()
        
        if "permission" in query_lower:
            return "Voice features require microphone permissions. Cedar handles this automatically in ChatInput, but you can also manage permissions manually with requestMicrophonePermission()."
        elif "not working" in query_lower or "error" in query_lower:
            return "Check browser console for errors, verify HTTPS is used, ensure OpenAI API key is configured, and confirm microphone permissions are granted."
        elif "setup" in query_lower or "install" in query_lower:
            return "Use 'npx cedar-os-cli plant-seed' to set up Cedar with voice features. Voice works automatically in ChatInput component."
        elif focus == "components":
            return "Cedar provides VoiceIndicator for visual feedback, VoiceButton for controls, and ChatInput with built-in voice. Search docs for specific component examples."
        elif focus == "integration":
            return "Voice requires OpenAI API key for transcription (Whisper) and TTS. Configure endpoint for real-time WebRTC voice if needed."
        else:
            return "Cedar's voice features include automatic transcription, TTS, visual indicators, and keyboard shortcuts. Search documentation for specific implementation details."
    
    def _suggest_related_topics(self, query: str, focus: str) -> List[str]:
        """Suggest related topics to explore"""
        suggestions = []
        
        # Base suggestions on focus
        if focus == "components":
            suggestions = ["VoiceIndicator usage", "ChatInput voice integration", "Custom voice buttons"]
        elif focus == "permissions":
            suggestions = ["Browser compatibility", "HTTPS requirements", "Permission handling"]
        elif focus == "integration":
            suggestions = ["OpenAI configuration", "WebSocket setup", "Voice endpoints"]
        else:
            suggestions = ["Voice components", "Permission handling", "Backend setup"]
        
        # Add query-specific suggestions
        query_lower = query.lower()
        if "indicator" in query_lower:
            suggestions.append("VoiceIndicator animations")
        if "button" in query_lower:
            suggestions.append("Voice button states")
        if "error" in query_lower:
            suggestions.append("Troubleshooting voice issues")
            
        return suggestions[:5]
    
    def _suggest_next_steps(self, results: List[Dict[str, Any]], focus: str) -> List[str]:
        """Suggest next steps based on search results"""
        if not results:
            return [
                "Try searching with different keywords",
                "Explore voice components documentation",
                "Check the Cedar Voice overview"
            ]
        
        steps = []
        if focus == "setup":
            steps = [
                "Run 'npx cedar-os-cli plant-seed' to install Cedar",
                "Configure OpenAI API key",
                "Test voice in ChatInput component"
            ]
        elif focus == "components":
            steps = [
                "Review component documentation",
                "Check implementation examples",
                "Test component in your application"
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
            "components": "Cedar voice components are React components that integrate with the Cedar store. Import from '@cedar/voice' and use with useCedarStore hook.",
            "permissions": "Microphone permissions are handled automatically by ChatInput. For custom implementations, use voice.requestMicrophonePermission().",
            "integration": "Voice requires OpenAI API key. Configure in environment variables. Optional WebSocket endpoint for real-time voice.",
            "setup": "Install Cedar with 'npx cedar-os-cli plant-seed'. Voice features work out-of-the-box in ChatInput component.",
            "general": "Cedar provides complete voice solution with UI components, state management, and backend integration."
        }
        return overviews.get(focus, overviews["general"])
    
    def _identify_key_concepts(self, query: str, focus: str) -> List[str]:
        """Identify key concepts to understand"""
        concepts = {
            "components": ["Voice state management", "Component props", "Event handling", "Visual feedback"],
            "permissions": ["getUserMedia API", "Browser compatibility", "HTTPS requirement", "Permission states"],
            "integration": ["OpenAI Whisper", "Text-to-speech", "WebSocket connections", "API configuration"],
            "setup": ["Cedar CLI", "Environment variables", "Package installation", "Initial configuration"],
            "general": ["Voice state", "Transcription", "TTS", "UI components"]
        }
        return concepts.get(focus, concepts["general"])
    
    def _get_search_suggestions(self, query: str, focus: str) -> List[str]:
        """Get search suggestions for finding more information"""
        base_suggestions = [
            f"Cedar voice {focus}",
            f"voice {query} implementation",
            f"{query} example code"
        ]
        
        # Add focus-specific suggestions
        if focus == "components":
            base_suggestions.extend([f"{comp} usage" for comp in self.VOICE_SEARCH_TERMS["components"][:3]])
        elif focus == "permissions":
            base_suggestions.extend(["microphone permission handling", "browser voice support"])
        
        return base_suggestions[:6]
    
    def _suggest_common_patterns(self, focus: str) -> List[str]:
        """Suggest common implementation patterns"""
        patterns = {
            "components": [
                "ChatInput with built-in voice",
                "VoiceIndicator with custom positioning",
                "Custom voice button implementation"
            ],
            "permissions": [
                "Automatic permission handling",
                "Manual permission request",
                "Permission denial fallback"
            ],
            "integration": [
                "OpenAI API configuration",
                "WebSocket voice streaming",
                "Error handling patterns"
            ],
            "general": [
                "Basic voice setup",
                "Voice with chat interface",
                "Custom voice controls"
            ]
        }
        return patterns.get(focus, patterns["general"])
    
    def _create_implementation_checklist(self, query: str, focus: str) -> List[str]:
        """Create implementation checklist"""
        base_checklist = [
            "Cedar installed via plant-seed",
            "OpenAI API key configured",
            "HTTPS enabled (for production)",
            "Voice components imported"
        ]
        
        if focus == "components":
            base_checklist.extend([
                "Component rendered in UI",
                "Voice state connected",
                "Event handlers configured"
            ])
        elif focus == "permissions":
            base_checklist.extend([
                "Permission request handled",
                "Permission status displayed",
                "Fallback for denied permissions"
            ])
            
        return base_checklist
    
    def _analyze_potential_causes(self, query: str) -> List[str]:
        """Analyze potential causes of issues"""
        query_lower = query.lower()
        causes = []
        
        if "permission" in query_lower or "mic" in query_lower:
            causes.extend([
                "Microphone permissions not granted",
                "Browser blocking microphone access",
                "Not using HTTPS"
            ])
        if "not working" in query_lower or "doesn't work" in query_lower:
            causes.extend([
                "Missing API configuration",
                "Component not properly imported",
                "State not connected"
            ])
        if "error" in query_lower:
            causes.extend([
                "API key invalid or missing",
                "Network connectivity issues",
                "Browser compatibility problems"
            ])
            
        return causes or ["Configuration issue", "Integration problem", "Component error"]
    
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
            "Verify Cedar is properly installed",
            "Confirm API keys are configured"
        ]
        
        if focus == "permissions":
            steps.extend([
                "Check browser microphone settings",
                "Verify HTTPS is being used",
                "Test in different browser"
            ])
        elif focus == "components":
            steps.extend([
                "Verify component is imported",
                "Check voice state in Redux DevTools",
                "Confirm component props"
            ])
            
        return steps
    
    def _get_common_solutions(self, query: str) -> List[str]:
        """Get common solutions for issues"""
        query_lower = query.lower()
        solutions = []
        
        if "permission" in query_lower:
            solutions = [
                "Ensure HTTPS is used",
                "Clear browser permissions and retry",
                "Add permission request UI"
            ]
        elif "api" in query_lower or "key" in query_lower:
            solutions = [
                "Verify OpenAI API key is valid",
                "Check environment variable configuration",
                "Ensure API key has proper permissions"
            ]
        else:
            solutions = [
                "Reinstall Cedar with plant-seed",
                "Check documentation for examples",
                "Verify all dependencies are installed"
            ]
            
        return solutions
    
    def _suggest_debugging_approach(self, focus: str) -> str:
        """Suggest debugging approach"""
        approaches = {
            "components": "Use React DevTools to inspect component props and state. Check voice state in Redux DevTools.",
            "permissions": "Check browser console for permission errors. Test in different browsers. Verify HTTPS.",
            "integration": "Monitor Network tab for API calls. Check WebSocket connections. Verify API responses.",
            "general": "Start with browser console, check voice state, verify configuration, test in isolation."
        }
        return approaches.get(focus, approaches["general"])
    
    def _list_available_features(self, focus: str) -> List[str]:
        """List available voice features"""
        features = {
            "components": self.VOICE_SEARCH_TERMS["components"],
            "features": self.VOICE_SEARCH_TERMS["features"],
            "methods": self.VOICE_SEARCH_TERMS["methods"],
            "general": [
                "Voice transcription (STT)",
                "Text-to-speech (TTS)",
                "Visual indicators",
                "Permission handling",
                "Keyboard shortcuts",
                "State management"
            ]
        }
        return features.get(focus, features["general"])
    
    def _get_component_categories(self) -> Dict[str, List[str]]:
        """Get component categories"""
        return {
            "UI Components": ["VoiceIndicator", "VoiceButton", "VoiceWaveform"],
            "Settings": ["VoiceSettings", "VoiceStatusPanel"],
            "Integrated": ["ChatInput (with voice)", "FloatingCedarChat"],
            "State": ["useCedarStore", "voice state object"]
        }
    
    def _get_integration_points(self) -> List[str]:
        """Get integration points"""
        return [
            "OpenAI Whisper API (transcription)",
            "OpenAI TTS API (text-to-speech)",
            "WebRTC for real-time voice",
            "Browser MediaDevices API",
            "Cedar state management"
        ]
    
    def _suggest_learning_path(self, query: str, focus: str) -> List[str]:
        """Suggest learning path"""
        paths = {
            "setup": [
                "Install Cedar with plant-seed",
                "Configure API keys",
                "Test basic voice in ChatInput",
                "Explore voice components"
            ],
            "components": [
                "Start with ChatInput",
                "Add VoiceIndicator",
                "Customize voice button",
                "Implement voice settings"
            ],
            "general": [
                "Understand voice state",
                "Try ChatInput voice",
                "Add visual indicators",
                "Handle permissions",
                "Customize behavior"
            ]
        }
        return paths.get(focus, paths["general"])