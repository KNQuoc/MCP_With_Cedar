"""Tool to intercept and validate package installation commands."""

import json
from typing import Dict, Any, List
import mcp.types as types
from ..shared import (
    is_blocked_install_command,
    BLOCKED_PACKAGES,
    DEFAULT_INSTALL_COMMAND,
    INSTALLATION_RULES,
    format_tool_output
)


class CheckInstallTool:
    """Tool that MUST be called before any npm/yarn/pnpm install commands.
    
    This tool validates installation commands and returns the correct
    Cedar-OS installation approach when blocked packages are detected.
    """
    
    name = "checkInstall"
    
    def list_tool(self) -> types.Tool:
        return types.Tool(
            name=self.name,
            description=(
                "CRITICAL: MUST be called FIRST before ANY command when working with Cedar-OS. "
                "Blocks create-next-app and ensures proper Cedar CLI usage. "
                "Cedar CLI creates COMPLETE projects - NOT just package installation! "
                "plant-seed command creates: Next.js app + TypeScript + Tailwind + Cedar components + Mastra backend. "
                "ALWAYS call this: 1) IMMEDIATELY when Cedar is mentioned 2) Before ANY npm command 3) Before create-next-app 4) In empty folders."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command you want to run (e.g., 'npm install', 'create-next-app', etc.). Use 'init' or leave empty to initialize Cedar."
                    },
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of package names to install (optional, extracted from command if not provided)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context about what you're trying to do (e.g., 'starting Cedar integration', 'installing dependencies')"
                    }
                },
                "required": []
            }
        )
    
    async def handle(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        command = arguments.get("command", "")
        packages = arguments.get("packages", [])
        context = arguments.get("context", "")
        
        # BLOCK create-next-app or any project creation when Cedar is involved
        if ("create-next-app" in command.lower() or 
            "create-react-app" in command.lower() or
            "npm create" in command.lower() or
            "npx create" in command.lower() or
            "yarn create" in command.lower() or
            "pnpm create" in command.lower()):
            # If this is for Cedar, block it
            if "cedar" in context.lower() or "cedar" in command.lower() or not context:
                full_payload = {
                    "approved": False,
                    "reason": "DO NOT create a Next.js/React project first! Cedar CLI creates the entire project.",
                    "correct_command": DEFAULT_INSTALL_COMMAND,
                    "action": "BLOCKED_USE_CEDAR_CLI",
                    "severity": "ERROR",
                    "blocked_command": command,
                    "message": (
                        "STOP! You're trying to create a Next.js/React project.\n"
                        "Cedar CLI creates the ENTIRE project for you!\n\n"
                        "Use this command instead:\n"
                        f"{DEFAULT_INSTALL_COMMAND}\n\n"
                        "This command will:\n"
                        "1. Create a complete Next.js project\n"
                        "2. Set up TypeScript, Tailwind, and all configurations\n"
                        "3. Add Cedar components with demo UI\n"
                        "4. Initialize Mastra backend\n"
                        "5. Install all dependencies\n\n"
                        "You get a COMPLETE, WORKING application!\n"
                        "DO NOT run create-next-app first!"
                    ),
                    "next_steps": [
                        f"1. Run: {DEFAULT_INSTALL_COMMAND}",
                        "2. Choose the Mastra template (recommended)",
                        "3. Enter your project name when prompted",
                        "4. Wait for complete project creation",
                        "5. Your project is ready to run with npm run dev"
                    ],
                    "important_note": "The Cedar CLI creates a better, more complete project than create-next-app + manual Cedar setup."
                }
                formatted = format_tool_output(full_payload, keep_fields=["approved", "correct_command", "message", "next_steps"])
                return [types.TextContent(
                    type="text",
                    text=json.dumps(formatted, indent=2)
                )]
        
        # ALWAYS trigger for Cedar setup - be very aggressive
        # Check for ANY Cedar-related context or empty/init scenarios
        if (command.lower() in ["init", "initialize", "start", ""] or 
            "cedar" in context.lower() or 
            "cedar" in command.lower() or
            "integration" in context.lower() or
            "setup" in context.lower() or
            "create" in context.lower() or
            "new project" in context.lower() or
            "empty folder" in context.lower() or
            not command):
            full_payload = {
                "approved": False,
                "reason": "Cedar CLI must be installed first",
                "correct_command": DEFAULT_INSTALL_COMMAND,
                "instructions": INSTALLATION_RULES,
                "action": "INSTALL_CEDAR_CLI_FIRST",
                "message": (
                    "Starting Cedar integration. Install the Cedar CLI FIRST:\n"
                    f"{DEFAULT_INSTALL_COMMAND}\n\n"
                    "IMPORTANT: This command will:\n"
                    "1. Create a COMPLETE project (if in empty folder)\n"
                    "2. Provide demo frontend with Cedar already integrated\n"
                    "3. Initialize Mastra backend with Cedar-OS\n"
                    "4. Install ALL Cedar packages and dependencies\n\n"
                    "DO NOT create a Next.js project first - plant-seed creates everything!\n"
                    "Run this BEFORE any other work.\n"
                    "Note: Use 'add-sapling' later ONLY if you need specific additional components."
                ),
                "next_steps": [
                    f"1. Run: {DEFAULT_INSTALL_COMMAND}",
                    "2. Choose template when prompted (recommended: Mastra template)",
                    "3. Wait for project creation and installation to complete",
                    "4. You'll have a complete working project with frontend and backend",
                    "5. All Cedar packages will be pre-installed and configured",
                    "6. No npm install needed for any Cedar packages",
                    "7. If specific components are needed later, use: npx cedar-os-cli add-sapling"
                ],
                "important_note": "DO NOT run add-sapling now. Only use it when explicitly adding individual components after initial setup."
            }
            formatted = format_tool_output(full_payload, keep_fields=["approved", "correct_command", "message", "next_steps"])
            return [types.TextContent(
                type="text",
                text=json.dumps(formatted, indent=2)
            )]
        
        # Extract packages from command if not provided
        if not packages and command:
            cmd_lower = command.lower()
            for pkg in BLOCKED_PACKAGES:
                if pkg.lower() in cmd_lower:
                    packages.append(pkg)
        
        # Check if this is a blocked Cedar installation
        if is_blocked_install_command(command):
            full_payload = {
                "approved": False,
                "reason": "Cedar packages must be installed using plant-seed CLI",
                "blocked_packages": [p for p in packages if p in BLOCKED_PACKAGES or p.startswith("@cedar-os")],
                "correct_command": DEFAULT_INSTALL_COMMAND,
                "instructions": INSTALLATION_RULES,
                "action": "USE_CORRECT_COMMAND",
                "message": (
                    "STOP! You tried to use npm install for Cedar packages. "
                    "This is WRONG. Use this command instead:\n"
                    f"{DEFAULT_INSTALL_COMMAND}\n\n"
                    "This command installs the Cedar CLI and ALL base packages correctly.\n"
                    "DO NOT use add-sapling unless specifically adding individual components later."
                )
            }
            formatted = format_tool_output(full_payload, keep_fields=["approved", "correct_command"])
            return [types.TextContent(
                type="text",
                text=json.dumps(formatted, indent=2)
            )]
        
        # Check if any packages are Cedar-related
        cedar_related = any(
            "cedar" in p.lower() for p in packages
        )
        
        if cedar_related:
            full_payload = {
                "approved": False,
                "reason": "Detected Cedar-related packages",
                "correct_command": DEFAULT_INSTALL_COMMAND,
                "instructions": INSTALLATION_RULES,
                "action": "USE_PLANT_SEED",
                "message": (
                    "Cedar-related packages detected. Use plant-seed instead:\n"
                    f"{DEFAULT_INSTALL_COMMAND}\n"
                    "This installs everything you need. Only use add-sapling for specific components later."
                )
            }
            formatted = format_tool_output(full_payload, keep_fields=["approved", "correct_command", "message"])
            return [types.TextContent(
                type="text", 
                text=json.dumps(formatted, indent=2)
            )]
        
        # Command is approved if not Cedar-related
        full_payload = {
            "approved": True,
            "command": command,
            "message": "Installation command approved. Proceed with the command.",
            "action": "PROCEED"
        }
        formatted = format_tool_output(full_payload, keep_fields=["approved", "command", "message"])
        return [types.TextContent(
            type="text",
            text=json.dumps(formatted, indent=2)
        )]