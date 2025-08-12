# Mastra Documentation Search Tool

## Overview

The `searchMastraDocs` tool provides keyword-based search functionality for Mastra backend documentation. This tool is designed to help developers find information about Mastra's agents, workflows, tools, memory systems, and other backend integration features.

## Features

- **Keyword-based search** with tokenization and relevance scoring
- **Weighted scoring** for Mastra-specific terms (agents, workflows, tools, memory)
- **Heading boost** - matches in headings are weighted more heavily
- **URL tracking** - preserves source URLs from the documentation
- **Section awareness** - maintains context about which documentation section content comes from

## Usage

The tool is automatically available through the Cedar MCP server and can be called with:

```json
{
  "tool": "searchMastraDocs",
  "arguments": {
    "query": "agent memory",
    "limit": 5
  }
}
```

## Search Topics

The tool is optimized for searching Mastra backend concepts including:

- **Agents** - Agent creation, configuration, dynamic agents, runtime context
- **Workflows** - Workflow orchestration and execution
- **Tools** - Tool development and MCP integration
- **Memory** - Memory systems, persistence, and recall
- **Voice** - Voice capabilities, TTS, STT, streaming
- **Authentication** - JWT, Auth0, Clerk, and other auth providers
- **Deployment** - Server setup, Docker, cloud deployment

## Configuration

### Environment Variables

- `MASTRA_DOCS_PATH` - Override the default path to the Mastra documentation file

### Default Path

By default, the tool looks for documentation at:
```
cedar-test/docs/mastra_llms_full.txt
```

## Integration with Cedar MCP

The Mastra search tool is integrated into the Cedar MCP server as a pre-confirmation tool, meaning it can be used without requiring the confirmation workflow. This allows developers to search for Mastra documentation at any time during their integration work.

## Implementation Details

The tool uses:
- Non-semantic keyword search (no vector embeddings required)
- Token-based matching with suffix support (e.g., "agent" matches "agents", "agentic")
- Special handling for Mastra-specific short tokens (mcp, ai, llm, api, jwt, cli, sdk)
- Content truncation to 2000 characters for response payload management