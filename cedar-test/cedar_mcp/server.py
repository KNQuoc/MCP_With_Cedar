import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
from pydantic import AnyUrl

# Load environment variables from .env file
load_dotenv()

from .services.docs import DocsIndex
from .services.feature import FeatureResolver
from .services.clarify import RequirementsClarifier
from .tools.search_docs import SearchDocsTool
from .tools.get_relevant_feature import GetRelevantFeatureTool
from .tools.clarify_requirements import ClarifyRequirementsTool
from .tools.confirm_requirements import ConfirmRequirementsTool
from .tools.check_install import CheckInstallTool
from .shared import GROUNDING_CONFIG, DEFAULT_INSTALL_COMMAND


logger = logging.getLogger(__name__)


class CedarModularMCPServer:
    """MCP Server exposing modular tools:
    - searchDocs: query Cedar-OS docs
    - getRelevantFeature: map a user goal to relevant Cedar features
    - clarifyRequirements: comprehensive structured requirement gathering
    - confirmRequirements: validate requirements and generate implementation plan

    Prompts and execution are separated. Services perform execution;
    prompts build structured content used by those services.
    """

    def __init__(self, docs_path: Optional[str] = None) -> None:
        self.server = Server("cedar-modular-mcp")
        # Prefer explicit arg, then env, then local bundled cedar_llms_full.txt
        resolved_docs_path = (
            docs_path
            or os.getenv("CEDAR_DOCS_PATH")
            or self._default_docs_path()
        )
        # Enable semantic search if Supabase credentials are available
        enable_semantic = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
        self.docs_index = DocsIndex(resolved_docs_path, enable_semantic_search=enable_semantic)
        self.feature_resolver = FeatureResolver(self.docs_index)
        self.requirements_clarifier = RequirementsClarifier(self.docs_index)
        # Gate: require confirmRequirements to pass before other tools
        self._requirements_confirmed: bool = False
        # Initialize tool handlers
        self.tool_handlers: Dict[str, Any] = {}
        self._init_tools()
        self._setup_handlers()

    def _init_tools(self) -> None:
        """Instantiate tool handlers and register name → handler mapping."""
        search_tool = SearchDocsTool(self.docs_index)
        feature_tool = GetRelevantFeatureTool(self.feature_resolver)
        clarify_tool = ClarifyRequirementsTool(self.requirements_clarifier)
        confirm_tool = ConfirmRequirementsTool(self.requirements_clarifier)
        check_install_tool = CheckInstallTool()

        self.tool_handlers = {
            search_tool.name: search_tool,
            feature_tool.name: feature_tool,
            clarify_tool.name: clarify_tool,
            confirm_tool.name: confirm_tool,
            check_install_tool.name: check_install_tool,
        }

    def _setup_handlers(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            tools: List[types.Tool] = []
            seen: set[str] = set()
            for handler in self.tool_handlers.values():
                # Some handlers expose multiple tool names; guard duplicates
                if hasattr(handler, "list_tools"):
                    for t in handler.list_tools():
                        if t.name not in seen:
                            seen.add(t.name)
                            tools.append(t)
                elif hasattr(handler, "list_tool"):
                    t = handler.list_tool()
                    if t.name not in seen:
                        seen.add(t.name)
                        tools.append(t)
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                # Enforce requirements gate for all tools except clarify/confirm, checkInstall, and the integration wizard/searchDocs
                allowed_preconfirm = {
                    "clarifyRequirements",
                    "confirmRequirements",
                    "searchDocs",
                    "checkInstall",  # Always allow install checking
                }
                if name not in allowed_preconfirm and not self._requirements_confirmed:
                    message = {
                        "error": "requirements_not_confirmed",
                        "message": "Please run checkInstall FIRST, then clarifyRequirements and confirmRequirements before using other tools.",
                        "required": [
                            "checkInstall(context='starting Cedar integration') - ALWAYS DO THIS FIRST",
                            "clarifyRequirements(goal, known_constraints?)",
                            "confirmRequirements({ provider_config, structured_outputs, docs_loaded, ... })",
                        ],
                        "grounding": GROUNDING_CONFIG,
                        "installCommand": DEFAULT_INSTALL_COMMAND,
                        "installCommandNote": "NEVER use 'npm install' for any Cedar packages. ONLY use the plant-seed CLI commands.",
                        "errorHandling": "For ANY Cedar-related errors, ALWAYS call searchDocs first to find the solution.",
                        "criticalRule": "ALWAYS call checkInstall FIRST when starting Cedar work to install the CLI",
                    }
                    return [types.TextContent(type="text", text=json.dumps(message))]

                handler = self.tool_handlers.get(name)
                if not handler:
                    raise ValueError(f"Unknown tool: {name}")
                # Handlers that multiplex tools accept (name, arguments)
                if hasattr(handler, "handle"):
                    try:
                        # Try (name, args) signature first
                        result = await handler.handle(name, arguments)  # type: ignore
                    except TypeError:
                        result = await handler.handle(arguments)  # type: ignore
                else:
                    raise ValueError(f"Handler for {name} lacks handle()")

                # Special-case: update gate flag on confirmRequirements
                if name == "confirmRequirements":
                    try:
                        # The tool returns a single TextContent JSON payload
                        payload = json.loads(result[0].text) if result and result[0].text else {}
                        self._requirements_confirmed = bool(payload.get("satisfied"))
                    except Exception:
                        # Keep gate closed on parse issues
                        self._requirements_confirmed = False

                # If tool returns no citations and is docs-related, append a guard note
                try:
                    if name in {"searchDocs", "getRelevantFeature"}:
                        enriched = []
                        for item in result:
                            payload = json.loads(item.text) if item.text else {}
                            if not payload.get("results"):
                                payload["note"] = payload.get("note") or "not in docs"
                            enriched.append(types.TextContent(type="text", text=json.dumps(payload, indent=2)))
                        return enriched
                except Exception:
                    pass
                return result
            except Exception as exc:
                logger.exception("Tool execution error: %s", exc)
                return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]

        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:  # type: ignore
            return [
                types.Resource(
                    uri=AnyUrl("cedar://docs"),
                    name="Cedar Docs",
                    description="Indexed Cedar-OS documentation",
                    mimeType="application/json",
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:  # type: ignore
            if str(uri) == "cedar://docs":
                meta = self.docs_index.describe()
                return json.dumps(meta, indent=2)
            raise ValueError(f"Unknown resource: {uri}")

    def _default_docs_path(self) -> Optional[str]:
        """Resolve the bundled cedar_llms_full.txt as a default docs source."""
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, os.pardir))
            candidate = os.path.join(root, "docs", "cedar_llms_full.txt")
            return candidate if os.path.exists(candidate) else None
        except Exception:
            return None


async def run_stdio_server(server: CedarModularMCPServer) -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options(),
        )


async def main() -> None:
    # Configure logging only when running as a script
    logging.basicConfig(
        level=os.getenv("CEDAR_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting Cedar Modular MCP Server…")
    instance = CedarModularMCPServer()
    await run_stdio_server(instance)


if __name__ == "__main__":
    asyncio.run(main())


def cli() -> None:
    """Console script entrypoint (sync wrapper)."""
    asyncio.run(main())


