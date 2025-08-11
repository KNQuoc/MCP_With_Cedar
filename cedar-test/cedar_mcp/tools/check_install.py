"""Tool to intercept and validate package installation commands."""

import json
from typing import Dict, Any, List, Optional
import mcp.types as types
from ..shared import (
    is_blocked_install_command, 
    resolve_install_command,
    BLOCKED_PACKAGES,
    DEFAULT_INSTALL_COMMAND,
    INSTALLATION_RULES
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
                "CRITICAL: Call this BEFORE running ANY npm/yarn/pnpm install command OR when starting Cedar work. "
                "This validates installations and ensures Cedar CLI is installed first. "
                "ALWAYS use this tool: 1) Before package installation 2) When starting Cedar integration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The install command you want to run (e.g., 'npm install cedar-os'). Use 'init' to initialize Cedar."
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
        
        # Special case: initialization request or Cedar context
        if (command.lower() in ["init", "initialize", "start"] or 
            "cedar" in context.lower() or 
            "integration" in context.lower() or
            not command):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "approved": False,
                    "reason": "Cedar CLI must be installed first",
                    "correct_command": DEFAULT_INSTALL_COMMAND,
                    "instructions": INSTALLATION_RULES,
                    "action": "INSTALL_CEDAR_CLI_FIRST",
                    "message": (
                        "Starting Cedar integration. Install the CLI FIRST:\n"
                        f"{DEFAULT_INSTALL_COMMAND}\n\n"
                        "This command installs the Cedar CLI and ALL base packages.\n"
                        "Run this BEFORE any other Cedar work.\n"
                        "After this, all Cedar imports will work automatically.\n"
                        "Note: Use 'add-sapling' later ONLY if you need specific additional components."
                    ),
                    "next_steps": [
                        f"1. Run: {DEFAULT_INSTALL_COMMAND}",
                        "2. Wait for installation to complete",
                        "3. All Cedar base packages will be available",
                        "4. No npm install needed for any Cedar packages",
                        "5. If specific components are needed later, use: npx cedar-os-cli add-sapling"
                    ],
                    "important_note": "DO NOT run add-sapling now. Only use it when explicitly adding individual components after initial setup."
                }, indent=2)
            )]
        
        # Extract packages from command if not provided
        if not packages and command:
            cmd_lower = command.lower()
            for pkg in BLOCKED_PACKAGES:
                if pkg.lower() in cmd_lower:
                    packages.append(pkg)
        
        # Check if this is a blocked Cedar installation
        if is_blocked_install_command(command):
            return [types.TextContent(
                type="text",
                text=json.dumps({
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
                }, indent=2)
            )]
        
        # Check if any packages are Cedar-related
        cedar_related = any(
            "cedar" in p.lower() for p in packages
        )
        
        if cedar_related:
            return [types.TextContent(
                type="text", 
                text=json.dumps({
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
                }, indent=2)
            )]
        
        # Command is approved if not Cedar-related
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "approved": True,
                "command": command,
                "message": "Installation command approved. Proceed with the command.",
                "action": "PROCEED"
            }, indent=2)
        )]