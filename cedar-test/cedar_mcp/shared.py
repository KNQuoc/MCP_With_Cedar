"""Shared constants and utilities for Cedar MCP."""

from typing import Dict, Any


# Default install command
DEFAULT_INSTALL_COMMAND = "npx cedar-os-cli plant-seed"

# Shared grounding configuration
GROUNDING_CONFIG = {
    "rule": "Only answer using cedar-test/docs/cedar_llms_full.txt; include a citation to exact lines. If not found, say 'not in docs'.",
    "decoding": {"temperature": 0.1, "top_p": 0.9, "allow_dont_know": True},
    "tool_forcing": "Before answering, call searchDocs and verify matches exist.",
    "prompt_structure": "Ask for corrections to a checklist with doc-backed diffs instead of freeform steps.",
    "no_code_edits_until_confirmed": True,
    "install_policy": f"Default install command: {DEFAULT_INSTALL_COMMAND} unless user specifies otherwise.",
}

# Shared guidance text for tools
DOCS_GUIDANCE = (
    f"Only answer using cedar-test/docs/cedar_llms_full.txt; include citations "
    f"with line spans from the 'citations' field where available. If information "
    f"is not found in the search results, reply exactly: 'not in docs'. Default install command is "
    f"'{DEFAULT_INSTALL_COMMAND}' unless otherwise specified by the user."
)

CLARIFY_GUIDANCE = (
    f"When answering implementation questions later, only use cedar-test/docs/cedar_llms_full.txt. "
    f"Include citations (line spans) or reply 'not in docs'. Default install command is '{DEFAULT_INSTALL_COMMAND}' "
    f"unless the user explicitly specifies another."
)


def resolve_install_command(user_input: str = None) -> str:
    """Resolve install command based on user input."""
    if not user_input:
        return DEFAULT_INSTALL_COMMAND
    normalized = user_input.strip().lower()
    if normalized in {"default", "", "yes"}:
        return DEFAULT_INSTALL_COMMAND
    # Use user's explicit command
    return user_input.strip()


def build_grounding_payload(additional_fields: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build a standardized grounding payload."""
    payload = {"grounding": GROUNDING_CONFIG.copy()}
    if additional_fields:
        payload.update(additional_fields)
    return payload
