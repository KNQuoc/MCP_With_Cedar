from typing import List, Dict, Any, Optional

from .docs import DocsIndex


CEDAR_FEATURES = [
    {
        "key": "chat_system",
        "name": "AI Chat System",
        "keywords": ["chat", "streaming", "sse", "conversation", "messages", "ai", "assistant", 
                    "interactive", "copilot", "chatbot", "support", "help", "q&a", "question",
                    "enhance", "improvement", "feature", "capability"],
        "docs_tags": ["chat"],
        "use_cases": ["Add AI chat to website", "Interactive support", "Q&A system", "Blog enhancement"]
    },
    {
        "key": "voice_integration",
        "name": "Voice Interaction",
        "keywords": ["voice", "speech", "tts", "stt", "audio", "microphone", "speaking",
                    "transcription", "dictation", "accessibility", "hands-free", "interactive"],
        "docs_tags": ["voice"],
        "use_cases": ["Voice commands", "Audio feedback", "Accessibility features", "Hands-free interaction"]
    },
    {
        "key": "floating_chat",
        "name": "Floating Chat Widget",
        "keywords": ["floating", "widget", "chat", "popup", "bubble", "corner", "support",
                    "interactive", "help", "assistant", "enhance", "blog", "website"],
        "docs_tags": ["chat", "ui"],
        "use_cases": ["Blog enhancement", "Customer support", "Interactive help", "Website improvement"]
    },
    {
        "key": "ai_content_assistant",
        "name": "AI Content Assistant",
        "keywords": ["content", "writing", "blog", "article", "generate", "edit", "improve",
                    "ai", "assistant", "enhance", "creative", "suggestions", "recommendations"],
        "docs_tags": ["chat", "spells"],
        "use_cases": ["Blog content generation", "Writing assistance", "Content improvement", "AI suggestions"]
    },
    {
        "key": "spells_actions",
        "name": "AI Actions (Spells)",
        "keywords": ["spells", "actions", "commands", "tools", "functions", "automation",
                    "execute", "capability", "feature", "interactive", "dynamic"],
        "docs_tags": ["spells"],
        "use_cases": ["Custom actions", "Tool integration", "Automation", "Dynamic features"]
    },
    {
        "key": "contextual_ai",
        "name": "Contextual AI Assistance",
        "keywords": ["context", "contextual", "aware", "smart", "intelligent", "relevant",
                    "personalized", "adaptive", "blog", "content", "page", "section"],
        "docs_tags": ["context", "chat"],
        "use_cases": ["Page-aware assistance", "Contextual help", "Smart suggestions", "Personalized experience"]
    },
    {
        "key": "agent_backend",
        "name": "AI Agent Backend",
        "keywords": ["backend", "mastra", "adapter", "tool", "integration", "api",
                    "server", "persistent", "memory", "database", "history"],
        "docs_tags": ["backend", "mastra"],
        "use_cases": ["Persistent chat", "User memory", "Backend integration", "API connectivity"]
    },
    {
        "key": "agentic_state",
        "name": "Agentic State Management",
        "keywords": ["state", "agents", "workflow", "context", "persistence", "memory",
                    "session", "history", "data", "store"],
        "docs_tags": ["agentic-state"],
        "use_cases": ["State persistence", "Session management", "Workflow tracking", "Data storage"]
    },
    {
        "key": "interactive_ui",
        "name": "Interactive UI Components",
        "keywords": ["interactive", "ui", "component", "interface", "user", "experience",
                    "ux", "design", "enhance", "improve", "modern", "dynamic"],
        "docs_tags": ["ui", "components"],
        "use_cases": ["UI enhancement", "Interactive features", "Modern interface", "User experience"]
    },
    {
        "key": "search_qa",
        "name": "Search & Q&A System",
        "keywords": ["search", "find", "query", "question", "answer", "q&a", "faq",
                    "knowledge", "information", "help", "support", "documentation"],
        "docs_tags": ["chat", "search"],
        "use_cases": ["Blog search", "FAQ system", "Documentation assistant", "Knowledge base"]
    }
]


class FeatureResolver:
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index

    async def map_goal_to_features(self, goal: str, context: Optional[str] = None) -> Dict[str, Any]:
        goal_l = (goal or "").lower()
        ctx_l = (context or "").lower()
        combined_text = f"{goal_l} {ctx_l}"
        candidates: List[Dict[str, Any]] = []

        for feat in CEDAR_FEATURES:
            score = 0
            
            # Check keywords
            kw_hits = sum(kw in combined_text for kw in feat["keywords"])  # type: ignore
            score += kw_hits * 2  # Weight keyword matches
            
            # Check use cases
            if "use_cases" in feat:
                for use_case in feat["use_cases"]:
                    use_case_l = use_case.lower()
                    # Check if use case words appear in goal/context
                    use_case_words = use_case_l.split()
                    matches = sum(word in combined_text for word in use_case_words if len(word) > 3)
                    if matches > 0:
                        score += matches
            
            # Add feature if it has any relevance
            if score > 0:
                candidates.append({
                    "feature": feat["key"], 
                    "name": feat["name"], 
                    "score": score,
                    "matched_keywords": [kw for kw in feat["keywords"] if kw in combined_text][:5],
                    "relevant_use_cases": [uc for uc in feat.get("use_cases", []) 
                                          if any(word in combined_text for word in uc.lower().split() if len(word) > 3)]
                })

        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # If we have candidates, return them with additional guidance
        if candidates:
            return {
                "goal": goal, 
                "context": context, 
                "candidates": candidates[:5],
                "recommendation": f"Based on your goal, Cedar-OS can help with: {', '.join([c['name'] for c in candidates[:3]])}",
                "next_step": "Use searchDocs to find specific implementation details for each feature."
            }
        else:
            # Return with suggestions even if no exact matches
            return {
                "goal": goal,
                "context": context,
                "candidates": [],
                "suggestion": "Your goal might benefit from Cedar's AI chat, voice, or interactive features. Try searchDocs with specific feature names.",
                "available_features": ["AI Chat System", "Voice Integration", "Floating Chat Widget", "AI Actions (Spells)", "Contextual AI"]
            }


