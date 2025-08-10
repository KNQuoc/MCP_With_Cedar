from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .docs import DocsIndex
from .clarify import RequirementsClarifier
from ..shared import resolve_install_command, GROUNDING_CONFIG


@dataclass
class WizardQuestion:
    id: str
    text: str


@dataclass
class WizardState:
    stage: str
    question_index: int
    answers: Dict[str, Any] = field(default_factory=dict)
    goal: Optional[str] = None
    context: Optional[str] = None


class IntegrationWizard:
    """Guided, one-by-one question flow with stateful context.

    Stages:
    1. understand_app
    2. initial_setup
    3. feature_impl
    """

    def __init__(self, docs_index: Optional[DocsIndex] = None, clarifier: Optional[RequirementsClarifier] = None) -> None:
        self.docs_index = docs_index
        self.clarifier = clarifier or RequirementsClarifier(docs_index)
        self._sessions: Dict[str, WizardState] = {}

    async def _stage_questions(self, state: WizardState) -> List[WizardQuestion]:
        if state.stage == "understand_app":
            # Use clarify service for requirement gathering questions
            goal = state.goal or ""
            known_constraints = []
            try:
                clarify_questions = await self.clarifier.suggest_questions(goal, known_constraints)
                wizard_questions = []
                # Convert clarify questions to wizard format, limiting to most relevant ones
                for i, q in enumerate(clarify_questions[:4]):  # Take first 4 questions
                    question_id = f"clarify_{i}"
                    wizard_questions.append(WizardQuestion(question_id, q))
                return wizard_questions
            except Exception:
                # Fallback to minimal questions if clarify service fails
                return [
                    WizardQuestion("goal_confirm", f"To confirm, is this your goal: '{goal}'?"),
                    WizardQuestion("constraints", "Any technical constraints or requirements?"),
                ]
        if state.stage == "initial_setup":
            return [
                WizardQuestion("provider", "Which LLM provider do you want to use (OpenAI, Anthropic, AI SDK, custom)?"),
                WizardQuestion("keys_available", "Do you already have API keys configured as env vars?"),
                WizardQuestion("streaming", "Do you want streaming responses enabled?"),
                WizardQuestion("ui_cedar", "Should we add <CedarCopilot> with default settings to your app shell?"),
                WizardQuestion(
                    "install_cmd_pref",
                    f"Installation command: default is '{resolve_install_command()}'. If you prefer another, paste it; otherwise reply 'default'.",
                ),
            ]
        if state.stage == "feature_impl":
            return [
                WizardQuestion("features", "Which features should we implement now? (chat, voice). State calling will be added by default."),
            ]
        return []

    async def _advance_stage_if_complete(self, session_id: str) -> None:
        state = self._sessions[session_id]
        questions = await self._stage_questions(state)
        if state.question_index >= len(questions):
            if state.stage == "understand_app":
                state.stage = "initial_setup"
                state.question_index = 0
            elif state.stage == "initial_setup":
                state.stage = "feature_impl"
                state.question_index = 0
            elif state.stage == "feature_impl":
                # Done; stay at end
                pass

    async def start(self, session_id: str = "default", goal: Optional[str] = None, context: Optional[str] = None) -> Dict[str, Any]:
        self._sessions[session_id] = WizardState(stage="understand_app", question_index=0, goal=goal, context=context)
        return await self.get_next_question(session_id)

    async def get_next_question(self, session_id: str = "default") -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if not state:
            return {"error": "no_session", "message": "Start the wizard first."}
        questions = await self._stage_questions(state)
        if state.question_index >= len(questions):
            await self._advance_stage_if_complete(session_id)
            questions = await self._stage_questions(state)
        if state.question_index < len(questions):
            q = questions[state.question_index]
            return {
                "stage": state.stage,
                "question": {"id": q.id, "text": q.text},
                "progress": await self._progress(state),
                "guidance": self._guidance(),
            }
        # All stages complete -> return plan
        return {
            "stage": state.stage,
            "complete": True,
            "plan": await self._derive_plan(state),
            "guidance": self._guidance(),
        }

    async def answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if not state:
            return {"error": "no_session", "message": "Start the wizard first."}
        questions = await self._stage_questions(state)
        if state.question_index >= len(questions):
            await self._advance_stage_if_complete(session_id)
            questions = await self._stage_questions(state)
        if state.question_index < len(questions):
            q = questions[state.question_index]
            state.answers[q.id] = answer
            state.question_index += 1
            # auto-advance stage if finished
            await self._advance_stage_if_complete(session_id)
            return await self.get_next_question(session_id)
        return {"message": "Wizard completed.", "plan": await self._derive_plan(state)}

    async def state(self, session_id: str = "default") -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if not state:
            return {"error": "no_session"}
        return {
            "stage": state.stage,
            "question_index": state.question_index,
            "answers": state.answers,
            "goal": state.goal,
            "context": state.context,
            "progress": await self._progress(state),
        }

    def abort(self, session_id: str = "default") -> Dict[str, Any]:
        if session_id in self._sessions:
            del self._sessions[session_id]
        return {"aborted": True}

    async def _progress(self, state: WizardState) -> Dict[str, Any]:
        stages = ["understand_app", "initial_setup", "feature_impl"]
        stage_index = stages.index(state.stage)
        # For progress calculation, use simplified approach due to async complexity
        current_stage_questions = await self._stage_questions(state)
        return {
            "stage": state.stage,
            "done": state.question_index,
            "total": len(current_stage_questions),
            "stage_index": stage_index,
            "total_stages": len(stages),
        }

    def _guidance(self) -> Dict[str, Any]:
        return GROUNDING_CONFIG

    async def _derive_plan(self, state: WizardState) -> Dict[str, Any]:
        features_raw = (state.answers.get("features") or "").lower()
        wants_chat = "chat" in features_raw
        wants_voice = "voice" in features_raw
        plan: Dict[str, Any] = {
            "provider_config": {
                "provider": state.answers.get("provider"),
                "keys_available": state.answers.get("keys_available"),
                "streaming": state.answers.get("streaming"),
                "ui_cedar": state.answers.get("ui_cedar"),
            },
            "implement": {
                "chat": wants_chat,
                "voice": wants_voice,
                "state_calling": True,
            },
            "installCommand": resolve_install_command(state.answers.get("install_cmd_pref")),
        }
        # Attach doc evidence snippets when available
        evidence_queries: List[str] = []
        evidence_queries.append("Streaming")
        if wants_chat:
            evidence_queries.append("chat/stream")
        if wants_voice:
            evidence_queries.append("voice")
        if self.docs_index:
            evidences: List[Dict[str, Any]] = []
            for q in evidence_queries:
                try:
                    # Small number of top hits with citations
                    res = self.docs_index.search.__wrapped__(self.docs_index, q, limit=3) if hasattr(self.docs_index.search, "__wrapped__") else None
                except Exception:
                    res = None
                if not res:
                    # Fallback to async path executed synchronously not possible; leave empty
                    continue
                evidences.extend(res or [])
            if evidences:
                plan["evidence"] = evidences
        return plan


