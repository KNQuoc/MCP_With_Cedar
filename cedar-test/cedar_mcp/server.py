import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
from pydantic import AnyUrl

from .services.docs import DocsIndex
from .services.feature import FeatureResolver
from .services.clarify import RequirementsClarifier
from .tools.search_docs import SearchDocsTool
from .tools.get_relevant_feature import GetRelevantFeatureTool
from .tools.clarify_requirements import ClarifyRequirementsTool


logger = logging.getLogger(__name__)


class CedarModularMCPServer:
    """MCP Server exposing modular tools:
    - searchDocs: query Cedar-OS docs
    - getRelevantFeature: map a user goal to relevant Cedar features
    - clarifyRequirements: ask clarifying questions

    Prompts and execution are separated. Services perform execution;
    prompts build structured content used by those services.
    """

    def __init__(self, docs_path: Optional[str] = None) -> None:
        self.server = Server("cedar-modular-mcp")
        self.docs_index = DocsIndex(docs_path or os.getenv("CEDAR_DOCS_PATH"))
        self.feature_resolver = FeatureResolver(self.docs_index)
        self.requirements_clarifier = RequirementsClarifier()
        # Initialize tool handlers
        self.tool_handlers: Dict[str, Any] = {}
        self._init_tools()
        self._setup_handlers()

    def _init_tools(self) -> None:
        """Instantiate tool handlers and register name → handler mapping."""
        search_tool = SearchDocsTool(self.docs_index)
        feature_tool = GetRelevantFeatureTool(self.feature_resolver)
        clarify_tool = ClarifyRequirementsTool(self.requirements_clarifier)

        self.tool_handlers = {
            search_tool.name: search_tool,
            feature_tool.name: feature_tool,
            clarify_tool.name: clarify_tool,
        }

    def _setup_handlers(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [handler.list_tool() for handler in self.tool_handlers.values()]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                handler = self.tool_handlers.get(name)
                if not handler:
                    raise ValueError(f"Unknown tool: {name}")
                return await handler.handle(arguments)
            except Exception as exc:
                logger.exception("Tool execution error: %s", exc)
                return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]

        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:
            return [
                types.Resource(
                    uri=AnyUrl("cedar://docs"),
                    name="Cedar Docs",
                    description="Indexed Cedar-OS documentation",
                    mimeType="application/json",
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            if str(uri) == "cedar://docs":
                meta = self.docs_index.describe()
                return json.dumps(meta, indent=2)
            raise ValueError(f"Unknown resource: {uri}")


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


