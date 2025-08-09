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
from .prompts.templates import (
    build_search_docs_prompt,
    build_get_relevant_feature_prompt,
    build_clarify_requirements_prompt,
)


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
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="searchDocs",
                    description="Search Cedar-OS documentation for relevant content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "number", "default": 5},
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="getRelevantFeature",
                    description="Identify relevant Cedar-OS feature(s) for a described goal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string", "description": "What the user wants to achieve"},
                            "context": {"type": "string", "description": "Optional project/context details"},
                        },
                        "required": ["goal"],
                    },
                ),
                types.Tool(
                    name="clarifyRequirements",
                    description="Suggest clarifying questions to better understand requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string"},
                            "known_constraints": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["goal"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "searchDocs":
                    query: str = arguments.get("query", "")
                    limit: int = int(arguments.get("limit", 5))
                    prompt = build_search_docs_prompt(query)
                    results = await self.docs_index.search(query, limit=limit)
                    payload = {"prompt": prompt, "results": results}
                    return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

                if name == "getRelevantFeature":
                    goal: str = arguments.get("goal", "")
                    context: Optional[str] = arguments.get("context")
                    prompt = build_get_relevant_feature_prompt(goal, context)
                    mapping = await self.feature_resolver.map_goal_to_features(goal, context)
                    payload = {"prompt": prompt, "features": mapping}
                    return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

                if name == "clarifyRequirements":
                    goal: str = arguments.get("goal", "")
                    known_constraints: List[str] = arguments.get("known_constraints", [])
                    prompt = build_clarify_requirements_prompt(goal, known_constraints)
                    questions = await self.requirements_clarifier.suggest_questions(goal, known_constraints)
                    payload = {"prompt": prompt, "questions": questions}
                    return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

                raise ValueError(f"Unknown tool: {name}")
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


