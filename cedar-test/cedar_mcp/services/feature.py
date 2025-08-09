from typing import List, Dict, Any, Optional

from .docs import DocsIndex


CEDAR_FEATURES = [
    {
        "key": "agentic_state",
        "name": "Agentic State",
        "keywords": ["state", "agents", "workflow", "context", "persistence"],
        "docs_tags": ["agentic-state"],
    },
    {
        "key": "chat_system",
        "name": "Chat System",
        "keywords": ["chat", "streaming", "sse", "conversation", "messages"],
        "docs_tags": ["chat"],
    },
    {
        "key": "agent_backend",
        "name": "Agent Backend Connection",
        "keywords": ["backend", "mastra", "adapter", "tool calling", "integration"],
        "docs_tags": ["backend", "mastra"],
    },
    {
        "key": "voice_integration",
        "name": "Voice Integration",
        "keywords": ["voice", "speech", "tts", "stt", "audio"],
        "docs_tags": ["voice"],
    },
]


class FeatureResolver:
    def __init__(self, docs_index: DocsIndex) -> None:
        self.docs_index = docs_index

    async def map_goal_to_features(self, goal: str, context: Optional[str] = None) -> Dict[str, Any]:
        goal_l = (goal or "").lower()
        ctx_l = (context or "").lower()
        candidates: List[Dict[str, Any]] = []

        for feat in CEDAR_FEATURES:
            kw_hits = sum(kw in goal_l or kw in ctx_l for kw in feat["keywords"])  # type: ignore
            if kw_hits > 0:
                candidates.append({"feature": feat["key"], "name": feat["name"], "score": kw_hits})

        # If none matched, do a docs search to infer probable features by tag occurrences
        if not candidates and goal:
            docs_hits = await self.docs_index.search(goal, limit=8)
            tag_scores: Dict[str, int] = {f["key"]: 0 for f in CEDAR_FEATURES}
            for hit in docs_hits:
                content_l = (hit.get("content") or "").lower()
                for feat in CEDAR_FEATURES:
                    tag_scores[feat["key"]] += sum(tag in content_l for tag in feat["docs_tags"])  # type: ignore
            for feat in CEDAR_FEATURES:
                if tag_scores[feat["key"]] > 0:
                    candidates.append({
                        "feature": feat["key"],
                        "name": feat["name"],
                        "score": tag_scores[feat["key"]],
                    })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return {"goal": goal, "context": context, "candidates": candidates[:5]}


