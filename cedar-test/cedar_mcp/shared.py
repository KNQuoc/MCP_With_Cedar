"""Shared constants and utilities for Cedar MCP."""

from typing import Dict, Any


# Primary Cedar installation command
PRIMARY_INSTALL_COMMAND = "npx cedar-os-cli plant-seed"  # This installs ALL Cedar packages

# Additional Cedar commands (used only when needed)
ADDITIONAL_CEDAR_COMMANDS = {
    "add_component": "npx cedar-os-cli add-sapling",  # For adding individual components AFTER initial setup
    # DO NOT add npm install commands here
}

# Installation rules that MUST be enforced
INSTALLATION_RULES = """
CRITICAL INSTALLATION RULES:
1. ALWAYS call checkInstall tool BEFORE any npm/yarn/pnpm install command
2. NEVER run 'npm install cedar-os' or any variant
3. NEVER run 'npm install @cedar-os/anything'  
4. NEVER run 'npm install cedar-os-components'
5. ONLY use 'npx cedar-os-cli plant-seed' for initial Cedar installation
6. The plant-seed command installs EVERYTHING needed initially
7. Use 'npx cedar-os-cli add-sapling' ONLY when explicitly adding individual components later
8. Ignore ALL import statements in documentation - they're handled by plant-seed
9. If checkInstall returns approved=false, USE THE PROVIDED correct_command
10. DO NOT combine plant-seed and add-sapling - use plant-seed first, add-sapling only if needed later
"""

# Packages that should NEVER be installed directly via npm
BLOCKED_PACKAGES = [
    "cedar-os",
    "cedar-os-components",
    "@cedar-os/core",
    "@cedar-os/components",
    # ALL Cedar packages are installed via plant-seed, NOT npm
]

# Default install command (just plant-seed, not add-sapling)
DEFAULT_INSTALL_COMMAND = PRIMARY_INSTALL_COMMAND

# Cedar-specific error patterns that require searchDocs
CEDAR_ERROR_PATTERNS = [
    "Cannot find module '@cedar-os",
    "CedarCopilot",
    "useCedarStore",
    "CedarProvider",
    "handleEventStream",
    "StreamHandler",
    "ProviderImplementation",
    "cedar is not defined",
    "Cedar configuration error",
    "plant-seed",
    "add-sapling",
]

# Error handling rules for Cedar-related issues
ERROR_HANDLING_RULES = f"""
ERROR HANDLING PROTOCOL:
0. ALWAYS call checkInstall FIRST when starting ANY Cedar work
1. When encountering ANY Cedar/Cedar-OS/CedarCopilot error, IMMEDIATELY call searchDocs
2. Search for: error message, component name, or feature causing the issue
3. If import errors: search for the correct import syntax in docs
4. If component errors: search for component usage examples
5. If configuration errors: search for configuration requirements
6. NEVER guess solutions - ALWAYS verify with searchDocs first
7. Common error patterns to watch for: {', '.join(CEDAR_ERROR_PATTERNS[:5])}
8. For ANY error containing 'cedar', 'Cedar', or 'CEDAR': use searchDocs FIRST
"""

# Shared grounding configuration
GROUNDING_CONFIG = {
    "rule": "Only answer using cedar-test/docs/cedar_llms_full.txt; include a citation to exact lines. If not found, say 'not in docs'.",
    "decoding": {"temperature": 0.1, "top_p": 0.9, "allow_dont_know": True},
    "tool_forcing": "ALWAYS call checkInstall FIRST when starting Cedar work. Before ANY npm install, call checkInstall.",
    "prompt_structure": "Ask for corrections to a checklist with doc-backed diffs instead of freeform steps.",
    "no_code_edits_until_confirmed": True,
    "install_policy": INSTALLATION_RULES,
    "error_handling": ERROR_HANDLING_RULES,
    "blocked_commands": [f"npm install {pkg}" for pkg in BLOCKED_PACKAGES],
    "only_allowed_install": DEFAULT_INSTALL_COMMAND,
    "pre_install_check": "MANDATORY: Call checkInstall tool FIRST when starting Cedar work AND before ANY package installation",
    "cedar_init_rule": "When starting Cedar integration, ALWAYS call checkInstall with context='starting Cedar integration' to get CLI installation command",
}

# Shared guidance text for tools
DOCS_GUIDANCE = (
    f"{INSTALLATION_RULES}\n\n"
    f"{ERROR_HANDLING_RULES}\n\n"
    f"Only answer using cedar-test/docs/cedar_llms_full.txt; include citations "
    f"with line spans from the 'citations' field where available. If information "
    f"is not found in the search results, reply exactly: 'not in docs'. "
    f"BLOCKED: {', '.join(BLOCKED_PACKAGES)}. ONLY ALLOWED: {DEFAULT_INSTALL_COMMAND}"
)

CLARIFY_GUIDANCE = (
    f"{INSTALLATION_RULES}\n\n"
    f"{ERROR_HANDLING_RULES}\n\n"
    f"When answering implementation questions later, only use cedar-test/docs/cedar_llms_full.txt. "
    f"Include citations (line spans) or reply 'not in docs'. "
    f"BLOCKED PACKAGES: {', '.join(BLOCKED_PACKAGES)}. ONLY ALLOWED: {DEFAULT_INSTALL_COMMAND}"
)


def get_cedar_command(command_type: str = "install") -> str:
    """Get the appropriate Cedar command based on the type needed."""
    if command_type == "install":
        return PRIMARY_INSTALL_COMMAND
    elif command_type == "add_component":
        return ADDITIONAL_CEDAR_COMMANDS.get("add_component", "")
    else:
        return PRIMARY_INSTALL_COMMAND


def is_blocked_install_command(command: str) -> bool:
    """Check if a command contains blocked Cedar package installations."""
    if not command:
        return False
    cmd_lower = command.lower()
    # Check for npm install of blocked packages
    for pkg in BLOCKED_PACKAGES:
        if f"npm install {pkg}" in cmd_lower or f"npm i {pkg}" in cmd_lower:
            return True
    # Also check for npm install with @cedar-os prefix
    if "npm install @cedar-os" in cmd_lower or "npm i @cedar-os" in cmd_lower:
        return True
    return False

def resolve_install_command(user_input: str = None) -> str:
    """Resolve install command based on user input."""
    if not user_input:
        return DEFAULT_INSTALL_COMMAND
    
    # Check if user is trying to use a blocked command
    if is_blocked_install_command(user_input):
        # Force the correct command instead
        return DEFAULT_INSTALL_COMMAND
    
    normalized = user_input.strip().lower()
    if normalized in {"default", "", "yes"}:
        return DEFAULT_INSTALL_COMMAND
    
    # Only allow user override if it's not a blocked command
    return DEFAULT_INSTALL_COMMAND  # Always use default for Cedar


# Structured requirement questions for comprehensive clarification
SETUP_QUESTIONS = [
    {
        "id": "provider",
        "text": "Which LLM provider do you want to use (OpenAI, Anthropic, AI SDK, custom)?",
        "category": "provider_config"
    },
    {
        "id": "keys_available", 
        "text": "Do you already have API keys configured as environment variables?",
        "category": "provider_config"
    },
    {
        "id": "streaming",
        "text": "Do you want streaming responses enabled?", 
        "category": "provider_config"
    },
    {
        "id": "ui_cedar",
        "text": "Should we add <CedarCopilot> with default settings to your app shell?",
        "category": "ui_setup"
    },
    {
        "id": "install_cmd_pref",
        "text": f"Installation command: default is '{DEFAULT_INSTALL_COMMAND}' (just plant-seed, not add-sapling). If you prefer another, paste it; otherwise reply 'default'.",
        "category": "setup"
    },
]

FEATURE_QUESTIONS = [
    {
        "id": "features",
        "text": "Which features should we implement now? (chat, voice). State calling will be added by default.",
        "category": "features"
    },
]

def build_implementation_plan(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Build implementation plan from clarification answers."""
    features_raw = (answers.get("features", "")).lower()
    wants_chat = "chat" in features_raw
    wants_voice = "voice" in features_raw
    
    return {
        "provider_config": {
            "provider": answers.get("provider"),
            "keys_available": answers.get("keys_available"),
            "streaming": answers.get("streaming"),
            "ui_cedar": answers.get("ui_cedar"),
        },
        "implement": {
            "chat": wants_chat,
            "voice": wants_voice,
            "state_calling": True,
        },
        "installCommand": resolve_install_command(answers.get("install_cmd_pref")),
        "grounding": GROUNDING_CONFIG,
    }

def build_grounding_payload(additional_fields: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build a standardized grounding payload."""
    payload = {"grounding": GROUNDING_CONFIG.copy()}
    if additional_fields:
        payload.update(additional_fields)
    return payload
