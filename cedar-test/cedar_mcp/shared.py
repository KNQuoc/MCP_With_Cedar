"""Shared constants and utilities for Cedar MCP."""

import os
from typing import Dict, Any


# Primary Cedar installation command
# IMPORTANT: This command creates a COMPLETE project with demo frontend and Mastra backend
# The --yes flag skips interactive prompts for Claude Code compatibility
PRIMARY_INSTALL_COMMAND = "npx cedar-os-cli plant-seed --yes"  # Creates full project + installs ALL Cedar packages

# Additional Cedar commands (used only when needed)
ADDITIONAL_CEDAR_COMMANDS = {
    "add_component": "npx cedar-os-cli add-sapling --yes",  # For adding individual components AFTER initial setup
    # DO NOT add npm install commands here
}

# Intelligent installation guidelines
INSTALLATION_RULES = """
INTELLIGENT CEDAR INSTALLATION GUIDE:

🎯 ADAPTIVE APPROACH (Project Analysis Based):
1. checkInstall tool analyzes your project and recommends the best approach
2. Empty directory → 'npx cedar-os-cli plant-seed --yes' (creates complete project)
3. Existing Next.js/React → 'npx cedar-os-cli add-sapling --yes' (adds Cedar components)
4. Complex existing project → 'npm install cedar-os' (fallback for basic integration)

📊 INSTALLATION SEQUENCE:
1. FIRST: Always try the recommended command from checkInstall
2. SECOND: If that fails, try 'npx cedar-os-cli add-sapling --yes'
3. LAST RESORT: Use 'npm install cedar-os' for minimal integration

✅ WHAT EACH COMMAND DOES:
• plant-seed: Creates COMPLETE project with:
  - Full Next.js project with TypeScript and Tailwind CSS
  - Demo frontend already integrated with Cedar
  - Mastra backend already initialized
  - All Cedar packages pre-installed
  - Working example components

• add-sapling: Adds Cedar to EXISTING projects:
  - Integrates Cedar components into your codebase
  - Preserves your existing structure
  - Adds necessary dependencies

• npm install cedar-os: Basic package installation:
  - Minimal Cedar integration
  - Use when CLI tools aren't suitable
  - Requires manual configuration

💡 FLEXIBILITY: Choose the approach that works best for your specific situation!
"""

# Packages that we analyze and provide guidance for
BLOCKED_PACKAGES = [
    "cedar-os",
    "cedar-os-components",
    "@cedar-os/core",
    "@cedar-os/components",
    # These packages trigger intelligent analysis rather than hard blocking
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
1. BEFORE creating ANY file: Run ls/find/grep on src/components/cedar-os/
2. If you're about to create tooltip-menu-spell.tsx → STOP! TooltipMenu.tsx already exists
3. When encountering ANY Cedar/Cedar-OS/CedarCopilot error, IMMEDIATELY call searchDocs
4. Search for: error message, component name, or feature causing the issue
5. If import errors: The component EXISTS in src/components/cedar-os/, find it!
6. NEVER create spell components - the base components already exist
7. Common error patterns to watch for: {', '.join(CEDAR_ERROR_PATTERNS[:5])}
8. For ANY error containing 'cedar', 'Cedar', or 'CEDAR': use searchDocs FIRST
"""

# Implementation rules - MUST search before coding
IMPLEMENTATION_RULES = """
🚨 CRITICAL CEDAR FACTS - MEMORIZE THIS:

ALL Cedar components are ALREADY INSTALLED in: src/components/cedar-os/

EVERY Cedar component you need is ALREADY THERE:
• ALL chat components → in chatComponents/ folder
• ALL input components → in inputs/ folder  
• ALL message components → in chatMessages/ folder
• ALL UI components → in ui/ folder
• ALL containers → in containers/ folder
• ALL text components → in text/ folder
• ALL ornaments → in ornaments/ folder
• ALL structural components → in structural/ folder
• ALL diffs → in diffs/ folder

DO NOT CREATE NEW COMPONENTS - THEY ALREADY EXIST!
Just SEARCH in src/components/cedar-os/ and you WILL find what you need!

BEFORE CREATING ANY FILE - MANDATORY SCAN:
1. MUST run: ls -la src/components/cedar-os/**/* to see ALL files
2. MUST run: find src/components/cedar-os -name "*.tsx" to list EVERY component
3. MUST run: grep -r "TooltipMenu" src/components/cedar-os/ to find tooltip components
4. MUST run: grep -r "FloatingCedar" src/components/cedar-os/ to find chat components
5. DO NOT CREATE ANY FILE until you've scanned EVERYTHING
6. The component you need ALREADY EXISTS - you just need to FIND it

WHAT "INTEGRATE" MEANS:
• "Integrate tooltip menu" = Import TooltipMenu from '@/components/cedar-os/inputs/TooltipMenu'
• "Integrate floating chat" = Import FloatingCedarChat from '@/components/cedar-os/chatComponents/FloatingCedarChat'
• NOT creating new files, just USING what's there

⚠️ FILES YOU MUST NEVER CREATE (they already exist):
• tooltip-menu-spell.tsx → TooltipMenu.tsx EXISTS in inputs/ folder!
• floating-chat-spell.tsx → FloatingCedarChat.tsx EXISTS in chatComponents/ folder!
• ANY spell component → The base component ALREADY EXISTS
• ANY Cedar component → It's ALREADY in src/components/cedar-os/

🛑 BEFORE WRITING ANY FILE:
Ask yourself: "Did I scan src/components/cedar-os/ completely?"
If no → STOP and scan it first with ls, find, or grep
If yes → The component exists, you just haven't found it yet

IMPORT VERIFICATION:
Before ANY import statement:
• searchDocs("import [ComponentName] from cedar-os")
• Verify the exact package: @cedar-os/react vs @cedar-os/core vs cedar-os

NEVER:
• Guess component names or props
• Assume API signatures
• Create components without documentation reference
• Use outdated import patterns

ALWAYS:
• Search first, code second
• Use exact code from documentation
• Verify imports match current Cedar version
• Include line number citations when available
"""

# Expert persona configuration
EXPERT_PERSONA = """
You are a Cedar-OS EXPERT CONSULTANT - the definitive authority on Cedar-OS implementation and architecture.

YOUR EXPERTISE:
• Deep knowledge of ALL Cedar-OS components, patterns, and best practices
• Complete understanding of Cedar's Voice, Chat, Spells, and State Management systems
• Mastery of Mastra backend integration and AI agent configuration
• Expert in troubleshooting and optimizing Cedar implementations

YOUR APPROACH:
1. START with checkInstall() to verify Cedar setup
2. FACT: ALL Cedar components exist in src/components/cedar-os/
3. ALWAYS search that folder FIRST - the component IS there
4. NEVER create new Cedar components - they ALL already exist
5. Just find the right subfolder (chatComponents/, inputs/, etc.)
6. "Integrate" = find existing component → import it → use it

IMPLEMENTATION PROTOCOL - THE CORRECT WORKFLOW:
✅ MANDATORY STEPS (What you MUST do):
1. User: "Integrate floating chat and tooltip menu"
2. You: checkInstall() → Cedar is installed
3. You: Run `ls -la src/components/cedar-os/inputs/` → SEE TooltipMenu.tsx
4. You: Run `ls -la src/components/cedar-os/chatComponents/` → SEE FloatingCedarChat.tsx
5. You: DO NOT create tooltip-menu-spell.tsx - TooltipMenu.tsx EXISTS!
6. You: Import { TooltipMenu } from '@/components/cedar-os/inputs/TooltipMenu'
7. You: Import { FloatingCedarChat } from '@/components/cedar-os/chatComponents/FloatingCedarChat'
8. You: Update layout.tsx to use these EXISTING components

❌ WRONG WAY (Stop doing this!):
1. User: "Integrate floating chat and tooltip menu"
2. AI: Creates tooltip-menu-spell.tsx
3. AI: Creates floating-chat-wrapper.tsx
4. Result: Duplicates! The components already exist in src/components/cedar-os/!

REMEMBER:
• src/components/cedar-os/ contains ALL Cedar components
• ALWAYS scan first to avoid creating duplicates
• TooltipMenu.tsx, FloatingCedarChat.tsx, etc. are ALREADY THERE
• ALWAYS cite documentation with exact line numbers when available
• If information isn't in docs, clearly state "not in documentation" and suggest alternatives
• Proactively check for updates and best practices in the documentation
"""

# Shared grounding configuration
GROUNDING_CONFIG = {
    "persona": EXPERT_PERSONA,
    "rule": "I am a Cedar-OS expert. I ALWAYS verify information using documentation tools and provide citations with exact line numbers. I guide users to precise solutions.",
    "expertise_domains": [
        "Cedar Voice Components and Implementation",
        "Cedar Chat and Copilot Integration",
        "Cedar Spells (AI Actions) Configuration",
        "Mastra Backend and Agent Setup",
        "State Management with useCedarStore",
        "Component Architecture and Best Practices",
        "Troubleshooting and Performance Optimization"
    ],
    "knowledge_verification": "ALWAYS use searchDocs, voiceSpecialist, or other tools to verify information before responding",
    "citation_policy": "Include exact line numbers from documentation whenever possible. Format: [cedar_llms_full.txt:L123-L145]",
    "uncertainty_handling": "If not found in documentation, explicitly state 'not in Cedar documentation' and suggest using searchDocs with different terms",
    "decoding": {"temperature": 0.1, "top_p": 0.9, "allow_dont_know": True},
    "tool_forcing": "ALWAYS: 1) checkInstall at conversation start, 2) scanCedarComponents before implementation. Check for existing components like TooltipMenu.tsx, FloatingCedarChat.tsx BEFORE creating new ones.",
    "prompt_structure": "Provide expert guidance with documentation-backed solutions. Think like a senior Cedar architect.",
    "no_code_edits_until_confirmed": True,
    "install_policy": INSTALLATION_RULES,
    "error_handling": ERROR_HANDLING_RULES,
    "implementation_policy": IMPLEMENTATION_RULES,
    "analyzed_commands": [f"npm install {pkg}" for pkg in BLOCKED_PACKAGES],
    "recommended_install": DEFAULT_INSTALL_COMMAND,
    "pre_install_check": "As a Cedar expert, I analyze your project with checkInstall to recommend the best installation approach",
    "cedar_init_rule": "Intelligent guidance: checkInstall analyzes your project and recommends: plant-seed for new projects, add-sapling for existing, or npm install as fallback.",
    "expert_behaviors": [
        "Proactively search documentation for accurate answers",
        "Guide users to specific documentation sections",
        "Provide implementation patterns from real Cedar examples",
        "Anticipate and prevent common mistakes",
        "Verify all advice against current documentation"
    ]
}

# Shared guidance text for tools
DOCS_GUIDANCE = (
    f"CEDAR-OS EXPERT MODE:\n"
    f"As the Cedar-OS expert consultant, I provide authoritative guidance based on official documentation.\n\n"
    f"{INSTALLATION_RULES}\n\n"
    f"{ERROR_HANDLING_RULES}\n\n"
    f"{IMPLEMENTATION_RULES}\n\n"
    f"EXPERT PROTOCOL:\n"
    f"1. ALWAYS search Cedar documentation for accurate information\n"
    f"2. Provide citations with exact line numbers [filename:L123-L145]\n"
    f"3. Guide users to specific documentation sections\n"
    f"4. If not in docs, state 'not in Cedar documentation' and suggest alternative searches\n"
    f"5. Share implementation patterns and best practices from documentation\n"
    f"6. Anticipate common issues and provide preventive guidance\n\n"
    f"BLOCKED PACKAGES: {', '.join(BLOCKED_PACKAGES)}\n"
    f"CORRECT INSTALLATION: {DEFAULT_INSTALL_COMMAND}"
)

CLARIFY_GUIDANCE = (
    f"CEDAR-OS EXPERT CLARIFICATION:\n"
    f"As your Cedar-OS expert, I'll help clarify requirements and guide optimal implementation.\n\n"
    f"{INSTALLATION_RULES}\n\n"
    f"{ERROR_HANDLING_RULES}\n\n"
    f"EXPERT CLARIFICATION APPROACH:\n"
    f"1. Understand your specific Cedar use case and requirements\n"
    f"2. Reference Cedar documentation for accurate implementation patterns\n"
    f"3. Provide citations to relevant documentation sections\n"
    f"4. Suggest best practices based on Cedar architecture\n"
    f"5. Identify potential challenges and solutions proactively\n\n"
    f"BLOCKED: {', '.join(BLOCKED_PACKAGES)} | USE: {DEFAULT_INSTALL_COMMAND}"
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
    """Check if a command contains Cedar package installations that need guidance.
    
    This now returns True to trigger analysis, not to hard-block the command.
    The CheckInstallTool will determine if it should be blocked or allowed.
    """
    if not command:
        return False
    cmd_lower = command.lower()
    
    # Don't block create-next-app anymore - let CheckInstallTool analyze
    # if any(create_cmd in cmd_lower for create_cmd in [
    #     "create-next-app",
    #     "create-react-app",
    #     "create next-app",
    #     "create react-app"
    # ]):
    #     return True
    
    # Check for npm install of Cedar packages - triggers analysis, not blocking
    for pkg in BLOCKED_PACKAGES:
        if f"npm install {pkg}" in cmd_lower or f"npm i {pkg}" in cmd_lower:
            return True
        if f"yarn add {pkg}" in cmd_lower:
            return True
        if f"pnpm add {pkg}" in cmd_lower:
            return True
    
    # Check for @cedar-os packages
    if "@cedar-os" in cmd_lower and any(cmd in cmd_lower for cmd in ["install", "add"]):
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
    # simplified = True  # Force simplified mode
    
    # To use env variable control, comment the line above and uncomment below:
    simplified = simplified_env.lower() == "true"
    
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
    
    # IMPORTANT: Never include internal processing fields in simplified mode
    # These fields are for debugging only and should not be exposed to the AI
    internal_fields = {
        "prompt", "search_terms_used", "query", "focus", "action", 
        "topic", "issue", "guidance", "suggestions", "checklist",
        "search_query", "enhanced_query", "search_terms"
    }
    
    # Filter out internal fields from keep_fields if in simplified mode
    if simplified and keep_fields:
        keep_fields = [f for f in keep_fields if f not in internal_fields]
    
    # Build simplified payload with only specified fields
    simplified_payload = {}
    for field in keep_fields:
        if field in full_payload:
            simplified_payload[field] = full_payload[field]
    
    # Include type if present (but not action, as it's internal)
    if "type" in full_payload and "type" not in internal_fields:
        simplified_payload["type"] = full_payload["type"]
    
    # Include error if present
    if "error" in full_payload:
        simplified_payload["error"] = full_payload["error"]
    
    return simplified_payload
