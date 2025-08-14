"""Tool to intelligently analyze and recommend Cedar installation approach."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import mcp.types as types
from ..shared import (
    is_blocked_install_command,
    BLOCKED_PACKAGES,
    DEFAULT_INSTALL_COMMAND,
    INSTALLATION_RULES,
    format_tool_output
)


class CheckInstallTool:
    """Tool that analyzes the project structure and recommends the best Cedar installation approach.
    
    This tool intelligently detects existing project setup and suggests:
    1. plant-seed for new projects (creates complete project)
    2. add-sapling for existing projects (adds Cedar components)
    3. npm install cedar-os as last resort for minimal integration
    """
    
    name = "checkInstall"
    
    def _analyze_project_structure(self, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the current project structure to determine what exists."""
        cwd = Path(working_dir or os.getcwd())
        
        analysis = {
            "is_empty": True,
            "has_package_json": False,
            "has_next_config": False,
            "has_react_app": False,
            "has_backend": False,
            "has_mastra": False,
            "has_cedar": False,
            "project_type": "unknown",
            "files_found": []
        }
        
        # Check if directory is empty or nearly empty
        try:
            dir_contents = list(cwd.iterdir())
            analysis["is_empty"] = len(dir_contents) <= 2  # Allow for .git and README
            
            # Check for package.json
            package_json = cwd / "package.json"
            if package_json.exists():
                analysis["has_package_json"] = True
                analysis["files_found"].append("package.json")
                
                # Read package.json to check for Cedar/Mastra
                try:
                    with open(package_json, 'r') as f:
                        pkg_data = json.load(f)
                        deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                        
                        # Check for Cedar packages
                        if any("cedar" in dep.lower() for dep in deps):
                            analysis["has_cedar"] = True
                            
                        # Check for Mastra
                        if "@mastra/core" in deps or "mastra" in deps:
                            analysis["has_mastra"] = True
                            
                        # Detect project type
                        if "next" in deps:
                            analysis["project_type"] = "nextjs"
                        elif "react" in deps:
                            analysis["project_type"] = "react"
                        elif "vue" in deps:
                            analysis["project_type"] = "vue"
                except:
                    pass
            
            # Check for Next.js
            if (cwd / "next.config.js").exists() or (cwd / "next.config.mjs").exists():
                analysis["has_next_config"] = True
                analysis["project_type"] = "nextjs"
                analysis["files_found"].append("next.config")
            
            # Check for app or pages directory (Next.js structure)
            if (cwd / "app").exists() or (cwd / "pages").exists() or (cwd / "src").exists():
                analysis["has_react_app"] = True
                
            # Check for backend indicators
            backend_indicators = ["server.js", "server.ts", "api", "backend", "server"]
            for indicator in backend_indicators:
                if (cwd / indicator).exists():
                    analysis["has_backend"] = True
                    analysis["files_found"].append(indicator)
                    break
                    
            # Check for Mastra directory
            if (cwd / "mastra").exists() or (cwd / ".mastra").exists():
                analysis["has_mastra"] = True
                analysis["files_found"].append("mastra")
                
        except Exception as e:
            # If we can't read the directory, assume it might not exist or have permissions
            pass
            
        return analysis
    
    def _determine_installation_strategy(self, analysis: Dict[str, Any], context: str = "") -> Tuple[str, str, str]:
        """
        Determine the best installation strategy based on project analysis.
        Returns: (command, strategy_name, reasoning)
        """
        
        # Strategy 1: Empty directory or new project - use plant-seed
        if analysis["is_empty"] or (not analysis["has_package_json"] and not analysis["has_react_app"]):
            return (
                "npx cedar-os-cli plant-seed --yes",
                "create_new_project",
                "Empty directory detected. Using plant-seed to create a complete Cedar project with frontend and Mastra backend."
            )
        
        # Strategy 2: Existing Cedar project - might just need npm install
        if analysis["has_cedar"]:
            return (
                "npm install",
                "existing_cedar",
                "Cedar already detected in project. Running npm install to ensure dependencies are up to date."
            )
        
        # Strategy 3: Existing Next.js/React without Cedar - use add-sapling
        if analysis["has_package_json"] and (analysis["project_type"] in ["nextjs", "react"]):
            return (
                "npx cedar-os-cli add-sapling --yes",
                "add_to_existing",
                "Existing Next.js/React project detected. Using add-sapling to integrate Cedar components into your existing project."
            )
        
        # Strategy 4: Has backend but no frontend - might need plant-seed for frontend
        if analysis["has_backend"] and not analysis["has_react_app"]:
            return (
                "npx cedar-os-cli plant-seed --yes",
                "create_frontend",
                "Backend detected but no frontend. Using plant-seed to create a Cedar frontend with Mastra integration."
            )
        
        # Strategy 5: Unknown project structure - recommend add-sapling as safer option
        if analysis["has_package_json"]:
            return (
                "npx cedar-os-cli add-sapling --yes",
                "safe_integration",
                "Existing project detected. Using add-sapling to safely add Cedar components without overwriting existing code."
            )
        
        # Default: Use plant-seed for new projects
        return (
            "npx cedar-os-cli plant-seed --yes",
            "default_new",
            "Recommending plant-seed to create a complete Cedar project. This is the best way to start with Cedar."
        )
    
    def list_tool(self) -> types.Tool:
        return types.Tool(
            name=self.name,
            description=(
                "ALWAYS CALL FIRST at conversation start! Verifies Cedar installation. "
                "IMPORTANT: After Cedar is confirmed, ALL components are in src/components/cedar-os/. "
                "TooltipMenu.tsx EXISTS in inputs/, FloatingCedarChat.tsx EXISTS in chatComponents/. "
                "NEVER create spell components - use the existing ones!"
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
        working_dir = arguments.get("working_dir")
        
        # Analyze current project structure
        analysis = self._analyze_project_structure(working_dir)
        
        # Determine the best installation strategy
        recommended_command, strategy, reasoning = self._determine_installation_strategy(analysis, context)
        
        # Handle create-next-app/create-react-app with intelligence
        if ("create-next-app" in command.lower() or 
            "create-react-app" in command.lower() or
            "npm create" in command.lower() or
            "npx create" in command.lower() or
            "yarn create" in command.lower() or
            "pnpm create" in command.lower()):
            
            # If Cedar context and empty directory, suggest plant-seed instead
            if ("cedar" in context.lower() or "cedar" in command.lower()) and analysis["is_empty"]:
                full_payload = {
                    "approved": False,
                    "recommendation": recommended_command,
                    "reason": reasoning,
                    "alternative": "You can use create-next-app if you prefer, then add Cedar with add-sapling",
                    "project_analysis": analysis,
                    "message": (
                        f"📊 Project Analysis: {reasoning}\n\n"
                        f"Recommended: {recommended_command}\n\n"
                        "Why? Cedar's plant-seed creates a more complete setup with:\n"
                        "• Pre-configured Next.js with TypeScript & Tailwind\n"
                        "• Cedar components already integrated\n"
                        "• Mastra backend initialized\n"
                        "• Demo UI ready to customize\n\n"
                        "Alternative: If you prefer vanilla Next.js first:\n"
                        "1. Run your create-next-app command\n"
                        "2. Then use: npx cedar-os-cli add-sapling --yes"
                    ),
                    "flexibility": "Your choice - both approaches work!"
                }
                formatted = format_tool_output(full_payload, keep_fields=["recommendation", "message", "flexibility"])
                return [types.TextContent(
                    type="text",
                    text=json.dumps(formatted, indent=2)
                )]
        
        # Handle Cedar initialization with intelligence
        if (command.lower() in ["init", "initialize", "start", ""] or 
            "cedar" in context.lower() or 
            "cedar" in command.lower() or
            "setup" in context.lower()):
            
            full_payload = {
                "approved": True,
                "recommendation": recommended_command,
                "strategy": strategy,
                "reason": reasoning,
                "project_analysis": {
                    "is_empty": analysis["is_empty"],
                    "has_existing_project": analysis["has_package_json"],
                    "project_type": analysis["project_type"],
                    "has_cedar": analysis["has_cedar"],
                    "files_found": analysis["files_found"]
                },
                "message": (
                    f"📊 Project Analysis Complete!\n\n"
                    f"✅ Recommended approach: {recommended_command}\n\n"
                    f"Reason: {reasoning}\n\n"
                    "Installation sequence:\n"
                    f"1. First try: {recommended_command}\n"
                    "2. If that doesn't work: npx cedar-os-cli add-sapling --yes\n"
                    "3. Last resort: npm install cedar-os\n\n"
                    "This adaptive approach ensures Cedar works with your specific setup."
                ),
                "fallback_commands": [
                    recommended_command,
                    "npx cedar-os-cli add-sapling --yes",
                    "npm install cedar-os"
                ]
            }
            formatted = format_tool_output(full_payload, keep_fields=["approved", "recommendation", "message", "fallback_commands"])
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
        
        # Handle npm install cedar-os with more flexibility
        if is_blocked_install_command(command):
            # Check if this is a last resort scenario
            if analysis["has_package_json"] and not analysis["is_empty"]:
                full_payload = {
                    "approved": True,  # Allow it as fallback
                    "recommendation": recommended_command,
                    "fallback_allowed": True,
                    "message": (
                        f"📊 Based on project analysis, recommended: {recommended_command}\n\n"
                        "However, if the Cedar CLI commands fail, you can use npm install cedar-os as a fallback.\n\n"
                        "Try in this order:\n"
                        f"1. {recommended_command} (best option)\n"
                        "2. npx cedar-os-cli add-sapling --yes (if first fails)\n"
                        "3. npm install cedar-os (last resort)\n\n"
                        "The npm install approach provides basic Cedar packages but won't create the full project structure."
                    ),
                    "installation_order": [
                        recommended_command,
                        "npx cedar-os-cli add-sapling --yes",
                        command  # Allow the original npm install as last resort
                    ]
                }
            else:
                # For empty projects, still recommend plant-seed strongly
                full_payload = {
                    "approved": False,
                    "recommendation": "npx cedar-os-cli plant-seed --yes",
                    "reason": "Empty project - plant-seed will create everything you need",
                    "message": (
                        "For new projects, use plant-seed instead of npm install:\n"
                        "npx cedar-os-cli plant-seed --yes\n\n"
                        "This creates a complete project with frontend, backend, and all Cedar components.\n"
                        "Only use npm install cedar-os if you have specific integration requirements."
                    )
                }
            formatted = format_tool_output(full_payload, keep_fields=["approved", "recommendation", "message"])
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