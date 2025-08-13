from __future__ import annotations

import json
from typing import Any, Dict, List

from mcp.types import Tool as McpTool, TextContent

from ..services.docs import DocsIndex
from ..shared import format_tool_output


class SpellsSpecialistTool:
    """Modular spells development assistant that leverages documentation search"""
    
    name = "spellsSpecialist"
    
    # Core spells-related search terms for documentation
    SPELLS_SEARCH_TERMS = {
        "core_concepts": ["spell", "spells", "useSpell", "spell architecture", "spell system", "magic", "interactions"],
        "components": ["QuestioningSpell", "RadialMenu", "RadialMenuItem", "SpellProvider", "useSpell hook"],
        "activation": ["activation conditions", "ActivationMode", "Hotkey", "MouseEvent", "SelectionEvent", "gesture", "trigger"],
        "modes": ["TOGGLE", "HOLD", "TRIGGER", "activation mode", "spell lifecycle"],
        "events": ["keyboard events", "mouse events", "text selection", "right click", "hotkeys", "shortcuts"],
        "features": ["radial menu", "context menu", "command palette", "interactive cursor", "tooltip", "visual feedback"],
        "lifecycle": ["onActivate", "onDeactivate", "activate", "deactivate", "toggle", "isActive"],
        "integration": ["useCedarStore", "sendMessage", "AI integration", "state access", "Cedar store"]
    }
    
    # High-level guidance categories
    GUIDANCE_CATEGORIES = {
        "setup": "Installation and initial configuration of spells",
        "creating": "Creating custom spells and interactions",
        "components": "Pre-built spell components and their usage",
        "activation": "Activation conditions and event handling",
        "lifecycle": "Spell lifecycle and state management",
        "patterns": "Implementation patterns and best practices",
        "troubleshooting": "Common issues and debugging approaches"
    }
    
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index
    
    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="REQUIRED for ANY query containing: Spell(s), RadialMenu, useSpell, QuestioningSpell, gesture, activation, hotkey, HOLD, TOGGLE, TRIGGER, onActivate, onDeactivate. DO NOT use searchDocs for these topics",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "guide", "troubleshoot", "explore"],
                        "description": "Action: search docs, get implementation guide, troubleshoot issue, or explore spell features"
                    },
                    "query": {
                        "type": "string",
                        "description": "Your specific question or search query about spells"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["creating", "activation", "components", "lifecycle", "patterns", "general"],
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
            return await self._search_spells_documentation(query, focus)
        elif action == "guide":
            return await self._provide_implementation_guide(query, focus)
        elif action == "troubleshoot":
            return await self._help_troubleshoot(query, focus)
        elif action == "explore":
            return await self._explore_spell_features(query, focus)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown action: {action}"}))]
    
    async def _search_spells_documentation(self, query: str, focus: str) -> List[TextContent]:
        """Search documentation with spells-specific context"""
        
        # Build enhanced search query based on focus area
        search_terms = self._build_search_query(query, focus)
        
        # Perform documentation search
        results = await self.docs_index.search(search_terms, limit=8, use_semantic=True)
        
        # Filter and rank results based on spells relevance
        spells_results = self._filter_spells_results(results)
        
        # Build response with guidance
        full_payload = {
            "action": "search",
            "query": query,
            "focus": focus,
            "search_terms_used": search_terms,
            "results": spells_results,
            "guidance": self._get_contextual_guidance(query, focus),
            "related_topics": self._suggest_related_topics(query, focus),
            "next_steps": self._suggest_next_steps(spells_results, focus),
            "code_examples": self._extract_code_from_results(spells_results)
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["results", "code_examples", "related_topics"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _provide_implementation_guide(self, query: str, focus: str) -> List[TextContent]:
        """Provide implementation guidance based on documentation"""
        
        # Search for implementation examples and patterns
        search_query = f"{query} spell implementation example code useSpell hook activation"
        docs_results = await self.docs_index.search(search_query, limit=5, use_semantic=True)
        
        # Build implementation guidance
        full_payload = {
            "action": "guide",
            "topic": query,
            "focus": focus,
            "overview": self._get_implementation_overview(query, focus),
            "documentation": docs_results,
            "key_concepts": self._identify_key_concepts(query, focus),
            "search_suggestions": self._get_search_suggestions(query, focus),
            "common_patterns": self._suggest_common_patterns(focus),
            "implementation_steps": self._create_implementation_steps(query, focus),
            "code_examples": self._extract_code_from_results(docs_results)
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation", "implementation_steps", "code_examples"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _help_troubleshoot(self, query: str, focus: str) -> List[TextContent]:
        """Help troubleshoot spells-related issues"""
        
        # Search for error and troubleshooting documentation
        error_query = f"{query} spell error troubleshoot fix issue problem solution activation"
        docs_results = await self.docs_index.search(error_query, limit=5, use_semantic=True)
        
        # Analyze the issue and provide troubleshooting guidance
        full_payload = {
            "action": "troubleshoot",
            "issue": query,
            "focus": focus,
            "potential_causes": self._analyze_potential_causes(query),
            "documentation": docs_results,
            "diagnostic_steps": self._get_diagnostic_steps(query, focus),
            "common_solutions": self._get_common_solutions(query),
            "search_suggestions": [
                f"spell {term}" for term in self._extract_error_keywords(query)
            ],
            "debugging_tips": self._suggest_debugging_tips(focus)
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation", "common_solutions", "diagnostic_steps"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    async def _explore_spell_features(self, query: str, focus: str) -> List[TextContent]:
        """Explore spell features and capabilities"""
        
        # Broad search to explore spell features
        explore_query = f"spell {query} features capabilities radial menu activation useSpell"
        docs_results = await self.docs_index.search(explore_query, limit=10, use_semantic=True)
        
        full_payload = {
            "action": "explore",
            "topic": query,
            "focus": focus,
            "available_features": self._list_available_features(focus),
            "documentation": docs_results,
            "spell_types": self._get_spell_types(),
            "activation_methods": self._get_activation_methods(),
            "use_cases": self._suggest_use_cases(query, focus),
            "learning_path": self._suggest_learning_path(query, focus)
        }
        
        formatted = format_tool_output(full_payload, keep_fields=["documentation", "available_features", "use_cases"])
        return [TextContent(type="text", text=json.dumps(formatted, indent=2))]
    
    def _build_search_query(self, base_query: str, focus: str) -> str:
        """Build an enhanced search query based on focus area"""
        focus_terms = {
            "creating": "useSpell hook custom spell implementation lifecycle",
            "activation": "ActivationMode Hotkey MouseEvent trigger conditions",
            "components": "QuestioningSpell RadialMenu spell components",
            "lifecycle": "onActivate onDeactivate isActive toggle activate",
            "patterns": "spell patterns best practices examples",
            "general": "spell useSpell activation radial menu"
        }
        
        additional_terms = focus_terms.get(focus, "spell")
        return f"{base_query} {additional_terms}"
    
    def _filter_spells_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and prioritize spells-related results"""
        spells_results = []
        other_results = []
        
        for result in results:
            # Safely get content and heading with default empty strings
            content_str = str(result.get("content", "") or "")
            heading_str = str(result.get("heading", "") or "")
            content = (content_str + " " + heading_str).lower()
            
            # Check for spells-related content
            spells_score = sum(
                1 for category in self.SPELLS_SEARCH_TERMS.values()
                for term in category
                if term.lower() in content
            )
            
            if spells_score > 0:
                result["spells_relevance"] = spells_score
                spells_results.append(result)
            else:
                other_results.append(result)
        
        # Sort by spells relevance
        spells_results.sort(key=lambda x: x.get("spells_relevance", 0), reverse=True)
        
        # Return spells results first, then others
        return spells_results[:7] + other_results[:3]
    
    def _get_contextual_guidance(self, query: str, focus: str) -> str:
        """Provide contextual guidance based on query and focus"""
        query_lower = query.lower()
        
        if "radial" in query_lower or "menu" in query_lower:
            return "RadialMenu creates circular menus activated by gestures. Use useSpell hook with HOLD mode for best UX. Components auto-position to stay on screen."
        elif "activation" in query_lower or "trigger" in query_lower:
            return "Spells support keyboard (Hotkey), mouse (MouseEvent), and selection (SelectionEvent) triggers. Use ActivationMode to control lifecycle: TOGGLE, HOLD, or TRIGGER."
        elif "custom" in query_lower or "create" in query_lower:
            return "Create custom spells with useSpell hook. Define unique ID, activation conditions, and lifecycle callbacks. Components receive isActive state."
        elif "not working" in query_lower or "error" in query_lower:
            return "Check spell ID uniqueness, verify activation conditions syntax, ensure preventDefaultEvents for browser shortcuts, and check ignoreInputElements setting."
        elif focus == "components":
            return "Cedar provides QuestioningSpell for interactive tooltips and RadialMenu for gesture-based menus. Both use useSpell hook internally."
        elif focus == "lifecycle":
            return "Spells have three states: inactive, activating, and active. Use onActivate/onDeactivate callbacks and isActive state for UI updates."
        else:
            return "Cedar spells enable gesture-based interactions, radial menus, and keyboard shortcuts. Use useSpell hook to create custom magical interactions."
    
    def _suggest_related_topics(self, query: str, focus: str) -> List[str]:
        """Suggest related topics to explore"""
        suggestions = []
        
        # Base suggestions on focus
        if focus == "creating":
            suggestions = ["useSpell hook usage", "Custom spell examples", "Activation conditions"]
        elif focus == "activation":
            suggestions = ["Hotkey combinations", "Mouse events", "Activation modes"]
        elif focus == "components":
            suggestions = ["RadialMenu setup", "QuestioningSpell usage", "Custom spell components"]
        elif focus == "lifecycle":
            suggestions = ["Spell state management", "Lifecycle callbacks", "Programmatic control"]
        else:
            suggestions = ["Creating spells", "Radial menus", "Keyboard shortcuts"]
        
        # Add query-specific suggestions
        query_lower = query.lower()
        if "radial" in query_lower:
            suggestions.append("RadialMenuItem configuration")
        if "keyboard" in query_lower or "hotkey" in query_lower:
            suggestions.append("Keyboard event handling")
        if "mouse" in query_lower:
            suggestions.append("Mouse gesture support")
            
        return suggestions[:5]
    
    def _suggest_next_steps(self, results: List[Dict[str, Any]], focus: str) -> List[str]:
        """Suggest next steps based on search results"""
        if not results:
            return [
                "Try searching with different keywords",
                "Explore spell components documentation",
                "Check the Cedar Spells overview"
            ]
        
        steps = []
        if focus == "creating":
            steps = [
                "Import useSpell hook from 'cedar-os'",
                "Define activation conditions",
                "Implement lifecycle callbacks",
                "Test spell activation"
            ]
        elif focus == "components":
            steps = [
                "Review component documentation",
                "Check implementation examples",
                "Add data attributes for QuestioningSpell",
                "Configure RadialMenu items"
            ]
        else:
            steps = [
                "Review the documentation results",
                "Try the example code",
                "Explore related spell features"
            ]
            
        return steps
    
    def _extract_code_from_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract code examples from search results"""
        code_examples = []
        
        for result in results:
            content = result.get("content", "")
            if not content:
                continue
            
            # Look for code blocks in markdown (```...```)
            import re
            code_pattern = r'```(\w+)?\n(.*?)```'
            matches = re.findall(code_pattern, content, re.DOTALL)
            
            for lang, code in matches:
                if code.strip():  # Only add non-empty code blocks
                    code_examples.append({
                        "language": lang or "typescript",
                        "code": code.strip(),
                        "source": result.get("heading", "Documentation"),
                        "context": result.get("url", "")
                    })
        
        # Also look for inline code patterns that might be useful
        if len(code_examples) < 3:
            # Extract any JSX/TSX patterns or spell-specific patterns
            inline_pattern = r'(useSpell\([^)]+\)|ActivationMode\.\w+|Hotkey\.\w+|<\w+Spell[^>]*/>)'
            for result in results:
                content = result.get("content", "")
                inline_matches = re.findall(inline_pattern, content)
                if inline_matches and len(inline_matches) > 2:
                    code_examples.append({
                        "language": "typescript",
                        "code": "\n".join(set(inline_matches[:5])),  # Unique examples
                        "source": result.get("heading", "Inline examples"),
                        "context": "Pattern examples from documentation"
                    })
        
        return code_examples[:5]  # Return up to 5 code examples
    
    def _get_implementation_overview(self, query: str, focus: str) -> str:
        """Provide implementation overview"""
        overviews = {
            "creating": "Create spells with useSpell hook. Define unique ID, activation conditions (events + mode), and lifecycle callbacks. Hook returns isActive state and control methods.",
            "activation": "Activation uses events (keyboard, mouse, selection) and modes (TOGGLE, HOLD, TRIGGER). Support multiple triggers and combine modifiers for complex gestures.",
            "components": "Pre-built spell components include QuestioningSpell (interactive tooltips) and RadialMenu (circular menus). Both handle activation internally.",
            "lifecycle": "Spells have onActivate and onDeactivate callbacks. Access trigger data in onActivate. Use isActive state for conditional rendering.",
            "patterns": "Common patterns: command palettes (TOGGLE mode), context menus (right-click), tooltips (hover/HOLD), and AI assistants (text selection).",
            "general": "Cedar spells enable magical interactions through gestures, shortcuts, and visual feedback. Built on useSpell hook with pre-built components."
        }
        return overviews.get(focus, overviews["general"])
    
    def _identify_key_concepts(self, query: str, focus: str) -> List[str]:
        """Identify key concepts to understand"""
        concepts = {
            "creating": ["useSpell hook", "Spell ID uniqueness", "Activation conditions", "Lifecycle callbacks", "State management"],
            "activation": ["Event types", "Activation modes", "Keyboard modifiers", "Mouse events", "Prevent defaults"],
            "components": ["RadialMenu", "QuestioningSpell", "Data attributes", "Component props", "Visual feedback"],
            "lifecycle": ["onActivate callback", "onDeactivate callback", "Trigger data", "isActive state", "Programmatic control"],
            "patterns": ["Command palettes", "Context menus", "Gesture recognition", "Keyboard shortcuts", "AI integration"],
            "general": ["Spell architecture", "useSpell hook", "Activation system", "Pre-built components"]
        }
        return concepts.get(focus, concepts["general"])
    
    def _get_search_suggestions(self, query: str, focus: str) -> List[str]:
        """Get search suggestions for finding more information"""
        base_suggestions = [
            f"Cedar spell {focus}",
            f"useSpell {query}",
            f"{query} activation example"
        ]
        
        # Add focus-specific suggestions
        if focus == "creating":
            base_suggestions.extend(["custom spell implementation", "useSpell hook examples"])
        elif focus == "activation":
            base_suggestions.extend(["ActivationMode types", "Hotkey combinations"])
        elif focus == "components":
            base_suggestions.extend(["RadialMenu usage", "QuestioningSpell setup"])
        
        return base_suggestions[:6]
    
    def _suggest_common_patterns(self, focus: str) -> List[str]:
        """Suggest common implementation patterns"""
        patterns = {
            "creating": [
                "Command palette with search",
                "Context menu on right-click",
                "Keyboard shortcut handler",
                "AI assistant on text selection"
            ],
            "activation": [
                "Multi-key combinations",
                "Hold-to-activate menus",
                "Toggle overlays",
                "Trigger with cooldown"
            ],
            "components": [
                "RadialMenu with dynamic items",
                "QuestioningSpell for help system",
                "Custom spell components",
                "Nested spell activation"
            ],
            "lifecycle": [
                "State cleanup on deactivate",
                "Trigger data processing",
                "Conditional activation",
                "Programmatic control"
            ],
            "general": [
                "Basic spell setup",
                "Radial menu integration",
                "Keyboard shortcut system",
                "Interactive tooltips"
            ]
        }
        return patterns.get(focus, patterns["general"])
    
    def _create_implementation_steps(self, query: str, focus: str) -> List[str]:
        """Create implementation steps"""
        base_steps = [
            "Import useSpell and required types from 'cedar-os'",
            "Define unique spell ID",
            "Configure activation conditions",
            "Implement lifecycle callbacks",
            "Add conditional UI rendering",
            "Test spell activation"
        ]
        
        if focus == "components":
            base_steps.extend([
                "Import spell component",
                "Add to component tree",
                "Configure props",
                "Add data attributes (if QuestioningSpell)"
            ])
        elif focus == "activation":
            base_steps.extend([
                "Choose activation events",
                "Select activation mode",
                "Handle prevent defaults",
                "Test all triggers"
            ])
            
        return base_steps
    
    
    def _analyze_potential_causes(self, query: str) -> List[str]:
        """Analyze potential causes of issues"""
        query_lower = query.lower()
        causes = []
        
        if "not activating" in query_lower or "not working" in query_lower:
            causes.extend([
                "Duplicate spell ID causing conflicts",
                "Incorrect event syntax in activation conditions",
                "Browser preventing default for shortcut",
                "Spell activated in input element (check ignoreInputElements)"
            ])
        if "radial" in query_lower:
            causes.extend([
                "RadialMenu items not configured properly",
                "Position calculation issues",
                "Missing required props"
            ])
        if "lifecycle" in query_lower:
            causes.extend([
                "Callbacks not properly defined",
                "State not updating on activation",
                "Cleanup not happening on deactivate"
            ])
            
        return causes or ["Configuration issue", "Activation problem", "Component error"]
    
    def _extract_error_keywords(self, query: str) -> List[str]:
        """Extract keywords from error descriptions"""
        words = query.lower().split()
        keywords = []
        
        for word in words:
            if len(word) > 3 and word not in ["the", "and", "not", "working", "doesn't", "won't", "spell"]:
                keywords.append(word)
                
        return keywords[:5]
    
    def _get_diagnostic_steps(self, query: str, focus: str) -> List[str]:
        """Get diagnostic steps for troubleshooting"""
        steps = [
            "Check browser console for errors",
            "Verify spell ID is unique",
            "Test activation conditions separately",
            "Check React DevTools for component state"
        ]
        
        if focus == "activation":
            steps.extend([
                "Log activation events to console",
                "Test with different browsers",
                "Check for conflicting shortcuts"
            ])
        elif focus == "components":
            steps.extend([
                "Verify component imports",
                "Check required props",
                "Inspect DOM for rendered elements"
            ])
            
        return steps
    
    def _get_common_solutions(self, query: str) -> List[str]:
        """Get common solutions for issues"""
        query_lower = query.lower()
        solutions = []
        
        if "activation" in query_lower:
            solutions = [
                "Use unique spell IDs",
                "Add preventDefaultEvents: true for browser shortcuts",
                "Check activation mode matches use case"
            ]
        elif "radial" in query_lower:
            solutions = [
                "Ensure RadialMenu has items prop",
                "Check item action callbacks",
                "Verify positioning logic"
            ]
        else:
            solutions = [
                "Review useSpell hook usage",
                "Check activation conditions syntax",
                "Verify lifecycle callbacks"
            ]
            
        return solutions
    
    def _suggest_debugging_tips(self, focus: str) -> str:
        """Suggest debugging approach"""
        tips = {
            "creating": "Add console.logs in lifecycle callbacks. Check spell ID uniqueness. Verify activation conditions.",
            "activation": "Log all keyboard/mouse events. Test activation modes separately. Check browser compatibility.",
            "components": "Inspect component props. Check data attributes for QuestioningSpell. Verify RadialMenu items.",
            "lifecycle": "Log state changes. Track activation/deactivation. Monitor trigger data.",
            "general": "Use React DevTools to inspect spell state. Add logging to callbacks. Test incrementally."
        }
        return tips.get(focus, tips["general"])
    
    def _list_available_features(self, focus: str) -> List[str]:
        """List available spell features"""
        features = {
            "creating": [
                "useSpell hook",
                "Custom spell components",
                "Lifecycle management",
                "State integration",
                "AI agent connection"
            ],
            "activation": self.SPELLS_SEARCH_TERMS["events"] + self.SPELLS_SEARCH_TERMS["modes"],
            "components": self.SPELLS_SEARCH_TERMS["components"],
            "general": [
                "Gesture-based activation",
                "Radial menus",
                "Interactive tooltips",
                "Keyboard shortcuts",
                "Context menus",
                "Command palettes"
            ]
        }
        return features.get(focus, features["general"])
    
    def _get_spell_types(self) -> Dict[str, List[str]]:
        """Get spell type categories"""
        return {
            "UI Spells": ["RadialMenu", "QuestioningSpell", "Command Palette"],
            "Gesture Spells": ["Mouse gestures", "Keyboard shortcuts", "Touch gestures"],
            "Context Spells": ["Right-click menus", "Selection actions", "Hover tooltips"],
            "AI Spells": ["AI assistant triggers", "Voice commands", "Smart suggestions"]
        }
    
    def _get_activation_methods(self) -> List[str]:
        """Get activation methods"""
        return [
            "Keyboard shortcuts (single keys, combinations)",
            "Mouse events (click, right-click, double-click)",
            "Text selection events",
            "Hold gestures (space to activate)",
            "Toggle switches (press to activate/deactivate)",
            "Trigger actions (one-time with cooldown)"
        ]
    
    def _suggest_use_cases(self, query: str, focus: str) -> List[str]:
        """Suggest use cases for spells"""
        use_cases = {
            "creating": [
                "Command palette for quick actions",
                "Context menu for selected text",
                "Keyboard navigation system",
                "Quick AI assistant trigger"
            ],
            "components": [
                "Help system with QuestioningSpell",
                "Tool palette with RadialMenu",
                "Settings menu with gestures",
                "Quick actions wheel"
            ],
            "general": [
                "Enhanced user interactions",
                "Accessibility shortcuts",
                "Power user features",
                "AI-powered assistance",
                "Visual feedback systems"
            ]
        }
        return use_cases.get(focus, use_cases["general"])
    
    def _suggest_learning_path(self, query: str, focus: str) -> List[str]:
        """Suggest learning path"""
        paths = {
            "creating": [
                "Understand useSpell hook",
                "Create basic toggle spell",
                "Add lifecycle callbacks",
                "Integrate with Cedar store",
                "Build complex interactions"
            ],
            "components": [
                "Try QuestioningSpell",
                "Implement RadialMenu",
                "Customize components",
                "Create custom spell components"
            ],
            "general": [
                "Learn spell concepts",
                "Try pre-built components",
                "Create custom spell",
                "Add activation conditions",
                "Build advanced interactions"
            ]
        }
        return paths.get(focus, paths["general"])