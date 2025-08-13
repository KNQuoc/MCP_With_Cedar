"""Shared constants and utilities for Cedar MCP."""

import os
from typing import Dict, Any


# Primary Cedar installation command
# IMPORTANT: This command creates a COMPLETE project with demo frontend and Mastra backend
PRIMARY_INSTALL_COMMAND = "npx cedar-os-cli plant-seed"  # Creates full project + installs ALL Cedar packages

# Additional Cedar commands (used only when needed)
ADDITIONAL_CEDAR_COMMANDS = {
    "add_component": "npx cedar-os-cli add-sapling",  # For adding individual components AFTER initial setup
    # DO NOT add npm install commands here
}

# Installation rules that MUST be enforced
INSTALLATION_RULES = """
CRITICAL INSTALLATION RULES:
1. ALWAYS call checkInstall tool BEFORE any npm/yarn/pnpm command (including create-next-app)
2. NEVER run 'create-next-app' when setting up Cedar - plant-seed creates the project
3. NEVER run 'npm install cedar-os' or any variant
4. NEVER run 'npm install @cedar-os/anything'  
5. NEVER run 'npm install cedar-os-components'
6. ONLY use 'npx cedar-os-cli plant-seed' for initial Cedar installation
7. The plant-seed command creates a COMPLETE PROJECT with:
   - Full Next.js project with TypeScript and Tailwind CSS
   - Demo frontend already integrated with Cedar
   - Mastra backend already initialized with Cedar-OS
   - All Cedar packages and dependencies pre-installed
   - Working example components and configuration
8. DO NOT create a Next.js project first - plant-seed creates EVERYTHING
9. Use 'npx cedar-os-cli add-sapling' ONLY when explicitly adding individual components later
10. Ignore ALL import statements in documentation - they're handled by plant-seed
11. If checkInstall returns approved=false, USE THE PROVIDED correct_command
12. DO NOT combine plant-seed and add-sapling - use plant-seed first, add-sapling only if needed later
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
    "blocked_commands": [f"npm install {pkg}" for pkg in BLOCKED_PACKAGES] + [
        "create-next-app",
        "npx create-next-app",
        "npm create next-app",
        "yarn create next-app",
        "pnpm create next-app",
        "create-react-app",
        "npx create-react-app"
    ],
    "only_allowed_install": DEFAULT_INSTALL_COMMAND,
    "pre_install_check": "MANDATORY: Call checkInstall tool FIRST when starting Cedar work, before ANY npm command including create-next-app",
    "cedar_init_rule": "When starting Cedar/Cedar-OS in ANY folder (empty or existing), ALWAYS call checkInstall FIRST with context='starting Cedar integration'. NEVER use create-next-app - plant-seed creates the complete project with TypeScript, Tailwind, and everything configured.",
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
    """Check if a command contains blocked Cedar package installations or project creation."""
    if not command:
        return False
    cmd_lower = command.lower()
    
    # Block create-next-app and similar commands
    if any(create_cmd in cmd_lower for create_cmd in [
        "create-next-app",
        "create-react-app",
        "create next-app",
        "create react-app"
    ]):
        return True
    
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


def format_tool_output(full_payload: Dict[str, Any], keep_fields: list = None) -> Dict[str, Any]:
    """Format tool output based on CEDAR_MCP_SIMPLIFIED_OUTPUT environment variable.
    
    Args:
        full_payload: The complete payload with all fields
        keep_fields: List of field names to keep when simplified (default: ['results'])
    
    Returns:
        Either the full payload or a simplified version with only specified fields
    """
    # Check if simplified output is enabled
    simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")  # Default to true
    
    # HARDCODED OVERRIDE FOR CLAUDE CODE COMPATIBILITY
    # Always use simplified mode for cleaner output
    # Comment out this line to respect the env variable
    simplified = True  # Force simplified mode
    
    # To use env variable control, comment the line above and uncomment below:
    # simplified = simplified_env.lower() == "true"
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"CEDAR_MCP_SIMPLIFIED_OUTPUT env var: {simplified_env}, simplified: {simplified}")
    
    if not simplified:
        # Return full payload with all prompts, guidance, etc.
        return full_payload
    
    # Default fields to keep when simplified
    if keep_fields is None:
        keep_fields = ["results"]
    
    # Build simplified payload with only specified fields
    simplified_payload = {}
    for field in keep_fields:
        if field in full_payload:
            simplified_payload[field] = full_payload[field]
    
    # Always include action/type if present (for context)
    if "action" in full_payload:
        simplified_payload["action"] = full_payload["action"]
    if "type" in full_payload:
        simplified_payload["type"] = full_payload["type"]
    
    # Include error if present
    if "error" in full_payload:
        simplified_payload["error"] = full_payload["error"]
    
    return simplified_payload
