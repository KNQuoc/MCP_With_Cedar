# Cedar MCP Server - Complete Documentation

## Quick Navigation

- [Quick Start](#quick-start) - Get running in 2 minutes
- [IDE Integration](#ide-integration) - Claude Code & Cursor setup
- [Architecture Overview](#architecture-overview) - System design
- [Complete Tool Reference](#complete-tool-reference) - All tools explained
- [Documentation System](#documentation-system) - How search works
- [Development Guide](#development-guide) - Extend the system

---

## Quick Start

### Important Context for AI Agents

**Cedar CLI creates COMPLETE projects!** The `npx cedar-os-cli plant-seed` command doesn't just install packages - it creates a full working application with:

- Demo frontend (Next.js/React) with Cedar pre-integrated
- Mastra backend already initialized with Cedar-OS
- All Cedar packages and dependencies pre-installed
- Working example components and configuration

**DO NOT** create a Next.js project first - plant-seed handles everything!

### Installation

```bash

# Create and activate virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate  # zsh/bash

# Install (editable for console scripts)
pip install -e .

# Or install dependencies directly
pip install mcp pydantic python-dotenv supabase openai
```

### Run the Server

```bash
# As a module
python -m cedar_mcp

# Or as console script (after pip install -e .)
cedar-modular-mcp

# With debug logging
CEDAR_LOG_LEVEL=DEBUG python -m cedar_mcp
```

## IDE Integration

### Claude Code Integration

**Option 1: Global Installation (available in all projects)**

```bash
# Install globally for all Claude Code sessions
claude mcp add cedar --scope user python -- -m cedar_mcp

# Verify installation
claude mcp list
```

**Option 2: Project-Specific Installation**

```bash
# Install only for current project
claude mcp add cedar --scope project python -- -m cedar_mcp

# This creates a .mcp.json file in your project root
```

**Option 3: Manual Configuration**
Add to `~/.claude.json` (global) or `.mcp.json` (project):

```json
{
  "mcpServers": {
    "cedar": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "cedar_mcp"],
      "env": {
        "CEDAR_LOG_LEVEL": "info",
        "CEDAR_DOCS_PATH": "/path/to/local/docs"
      }
    }
  }
}
```

### Cursor Integration

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cedar-agentic-server": {
      "command": "/ABS/PATH/TO/REPO/cedar-test/.venv/bin/python",
      "args": ["-m", "cedar_mcp"],
      "env": {
        "CEDAR_ENV": "development",
        "CEDAR_LOG_LEVEL": "info",
        "PYTHONPATH": "/ABS/PATH/TO/REPO/cedar-test",
        "CEDAR_DOCS_PATH": "/ABS/PATH/TO/LOCAL/DOCS"
      }
    }
  }
}
```

After configuration, restart your IDE. The Cedar MCP server will start automatically.

## Environment Configuration

Create a `.env` file in the cedar-test directory:

```bash
# Optional: Semantic Search Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key

# Optional: Custom Documentation Paths
CEDAR_DOCS_PATH=/path/to/cedar_llms_full.txt
MASTRA_DOCS_PATH=/path/to/mastra_llms_full.txt

# Output Configuration
CEDAR_MCP_SIMPLIFIED_OUTPUT=true  # Simplifies tool output

# Logging
CEDAR_LOG_LEVEL=INFO  # debug, info, warning, error
```

---

## Overview

The Cedar MCP (Model Context Protocol) Server is an intelligent assistant system designed to provide expert guidance for Cedar-OS implementations. It serves as an authoritative knowledge base and implementation advisor for developers working with Cedar-OS, a comprehensive framework for building AI-powered applications with voice, chat, and interactive features.

### Key Features

- **Expert Knowledge System**: Comprehensive documentation search with semantic and keyword-based retrieval
- **Intelligent Installation Guidance**: Project analysis and adaptive installation recommendations
- **Specialized Domain Experts**: Dedicated tools for Voice, Spells, and Mastra backend features
- **Documentation Enforcement**: Mandatory documentation verification to prevent hallucination
- **Multi-Source Documentation**: Supports both Cedar-OS and Mastra documentation
- **Semantic Search**: Optional vector-based search using Supabase and OpenAI embeddings
- **Project-Aware Recommendations**: Analyzes existing project structure to provide contextual advice

### Purpose

The MCP server acts as a bridge between AI assistants (like Claude) and the Cedar-OS documentation ecosystem, ensuring that:

1. All responses are grounded in actual documentation
2. Installation approaches are tailored to project requirements
3. Common mistakes are prevented through proactive guidance
4. Expert knowledge is consistently accessible

---

## Architecture Overview

### System Design

```
cedar_mcp/
│
├── Core Layer (server.py)
│   ├── MCP Server Instance
│   ├── Tool Registration
│   ├── Request Routing
│   └── Documentation Enforcement
│
├── Services Layer (services/)
│   ├── Documentation Indexing (docs.py)
│   ├── Semantic Search (semantic_search.py)
│   ├── Feature Resolution (feature.py)
│   └── Requirements Clarification (clarify.py)
│
├── Tools Layer (tools/)
│   ├── Search Tools
│   │   ├── SearchDocs (search_docs.py)
│   │   └── SearchMastraDocs (search_mastra_docs.py)
│   │
│   ├── Specialist Tools
│   │   ├── VoiceSpecialist (voice_specialist.py)
│   │   ├── SpellsSpecialist (spells_specialist.py)
│   │   └── MastraSpecialist (mastra_specialist.py)
│   │
│   ├── Installation Tools
│   │   └── CheckInstall (check_install.py)
│   │
│   └── Planning Tools
│       ├── GetRelevantFeature (get_relevant_feature.py)
│       ├── ClarifyRequirements (clarify_requirements.py)
│       └── ConfirmRequirements (confirm_requirements.py)
│
└── Configuration Layer (shared.py)
    ├── Constants & Rules
    ├── Expert Persona Configuration
    ├── Installation Guidelines
    └── Utility Functions
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between services (business logic) and tools (MCP interface)
2. **Documentation-First**: All responses must be grounded in searchable documentation
3. **Adaptive Intelligence**: Tools analyze context and provide tailored recommendations
4. **Fail-Safe Patterns**: Multiple fallback strategies for installation and implementation
5. **Expert Emulation**: System behaves as a senior Cedar architect would

### Project Layout

```text
cedar-test/
├── cedar_mcp/
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Entry point for module execution
│   ├── server.py                # Main MCP server (315 lines)
│   ├── shared.py                # Shared constants and utilities (450 lines)
│   ├── services/                # Business logic layer
│   │   ├── clarify.py          # Requirements clarification
│   │   ├── docs.py             # Documentation indexing and search
│   │   ├── feature.py          # Feature mapping logic
│   │   ├── mastra_docs.py      # Mastra documentation service
│   │   └── semantic_search.py  # Vector search integration
│   └── tools/                  # MCP tools layer
│       ├── check_install.py
│       ├── clarify_requirements.py
│       ├── confirm_requirements.py
│       ├── get_relevant_feature.py
│       ├── mastra_specialist.py
│       ├── search_docs.py
│       ├── search_mastra_docs.py
│       ├── spells_specialist.py
│       └── voice_specialist.py
├── docs/                        # Documentation files
│   ├── cedar_llms_full.txt
│   └── mastra_llms_full.txt
├── pyproject.toml              # Entrypoints & build config
├── requirements.txt            # Runtime dependencies
└── README.md                   # This file
```

---

## Complete Tool Reference

### Tool Registry

| Tool Name             | Purpose                      | Mandatory Usage                   | Description                                                                |
| --------------------- | ---------------------------- | --------------------------------- | -------------------------------------------------------------------------- |
| `checkInstall`        | Installation analysis        | **YES - At conversation start**   | Analyzes project structure and recommends best Cedar installation approach |
| `searchDocs`          | Cedar documentation search   | **YES - Before any Cedar answer** | Primary documentation search with keyword and semantic capabilities        |
| `searchMastraDocs`    | Mastra documentation search  | **YES - For Mastra questions**    | Searches Mastra backend documentation                                      |
| `voiceSpecialist`     | Voice feature expertise      | **YES - For voice questions**     | Expert guidance for voice implementation                                   |
| `spellsSpecialist`    | Spells/interaction expertise | **YES - For Spells questions**    | Guidance for AI-powered interactions                                       |
| `mastraSpecialist`    | Backend expertise            | **YES - For Mastra questions**    | Mastra backend and agent guidance                                          |
| `getRelevantFeature`  | Feature mapping              | Optional                          | Maps user goals to Cedar features                                          |
| `clarifyRequirements` | Requirement questions        | Optional                          | Generates clarifying questions                                             |
| `confirmRequirements` | Requirement validation       | Optional                          | Validates and plans implementation                                         |

### Detailed Tool Descriptions

#### 🔍 **searchDocs**

Primary documentation search interface with mandatory usage enforcement.

**Input Schema:**

```json
{
  "query": "string", // Search query
  "limit": 5, // Result limit (optional)
  "use_semantic": true, // Use vector search (optional)
  "doc_type": "auto" // "cedar" | "mastra" | "auto"
}
```

**Output:**

```json
{
  "results": [
    {
      "source": "file path",
      "heading": "section heading",
      "content": "documentation excerpt",
      "matchCount": 10,
      "matchedTokens": {"token": count},
      "citations": {
        "approxSpan": {"start": 123, "end": 145}
      }
    }
  ]
}
```

#### 🛠️ **checkInstall**

Intelligent project analysis and installation recommendation.

**Project Analysis Features:**

- Directory structure examination
- Package.json dependency analysis
- Framework detection (Next.js, React, Vue)
- Cedar/Mastra presence checking
- Backend component identification

**Installation Strategies:**

1. **Empty Directory** → `npx cedar-os-cli plant-seed --yes`
2. **Existing Cedar** → `npm install`
3. **Existing Next.js/React** → `npx cedar-os-cli add-sapling --yes`
4. **Backend Only** → `npx cedar-os-cli plant-seed --yes`
5. **Unknown Structure** → Adaptive recommendation

**Input Schema:**

```json
{
  "command": "string", // Command to analyze (optional)
  "packages": ["array"], // Package list (optional)
  "context": "string" // Context description (optional)
}
```

#### 🎤 **voiceSpecialist**

Expert guidance for voice feature implementation.

**Specializations:**

- Voice components (VoiceIndicator, VoiceButton, VoiceSettings)
- Microphone permission handling
- Real-time audio processing
- WebRTC integration
- OpenAI Realtime API
- Browser compatibility

**Actions:**

- `search`: Find voice documentation
- `guide`: Implementation guidance
- `troubleshoot`: Diagnose issues
- `explore`: Discover capabilities

**Input Schema:**

```json
{
  "action": "search", // "search" | "guide" | "troubleshoot" | "explore"
  "query": "string", // Your question
  "focus": "general" // "components" | "permissions" | "integration" | "setup"
}
```

#### ✨ **spellsSpecialist**

Expert guidance for Cedar Spells (AI-powered interactions).

**Specializations:**

- Spell architecture and lifecycle
- Radial menus and gestures
- Hotkey configurations
- QuestioningSpell and TooltipMenuSpell
- Custom spell creation
- Event handling patterns

**Core Concepts:**

- Activation modes: TOGGLE, HOLD, TRIGGER
- Event types: Hotkey, MouseEvent, SelectionEvent
- Lifecycle: onActivate, onDeactivate
- Component integration with useSpell hook

**Input Schema:**

```json
{
  "action": "search", // "search" | "guide" | "troubleshoot" | "explore"
  "query": "string", // Your question
  "focus": "general" // "creating" | "activation" | "components" | "lifecycle" | "patterns"
}
```

#### 🔧 **mastraSpecialist**

Expert guidance for Mastra backend integration.

**Specializations:**

- Agent architecture
- Workflow design
- Tool integration
- Memory systems
- MCP setup
- Authentication

**Input Schema:**

```json
{
  "query": "string", // Search query
  "limit": 5 // Result limit
}
```

#### 🎯 **getRelevantFeature**

Maps user goals to Cedar features.

**Feature Categories:**

- AI Chat System
- Voice Interaction
- Floating Chat Widget
- AI Content Assistant
- AI Actions (Spells)
- Contextual AI
- Agent Backend
- State Management
- Interactive UI
- Search & Q&A

**Input Schema:**

```json
{
  "goal": "string", // What you want to achieve
  "context": "string" // Optional project context
}
```

#### ❓ **clarifyRequirements**

Generates clarifying questions for requirements.

**Question Categories:**

- Scope and user goals
- Framework constraints
- Integration needs
- UI/UX requirements

**Input Schema:**

```json
{
  "goal": "string",
  "known_constraints": ["array"]
}
```

#### ✅ **confirmRequirements**

Validates requirements and generates implementation plan.

**Input Schema:**

```json
{
  "confirmations": {
    "requirement_id": true/false
  }
}
```

---

## Documentation System

### Documentation Sources

1. **Cedar Documentation** (`cedar_llms_full.txt`)

   - Comprehensive Cedar-OS component documentation
   - API references and implementation examples
   - Best practices and patterns
   - Voice, Chat, Spells, and UI components

2. **Mastra Documentation** (`mastra_llms_full.txt`)
   - Backend framework documentation
   - Agent and workflow guides
   - Tool development documentation
   - Memory and persistence strategies

### Search Strategies

#### Semantic Search (When Available)

- Requires Supabase and OpenAI configuration
- Uses vector embeddings for conceptual matching
- 512-dimension embeddings with text-embedding-3-small
- Similarity threshold filtering

#### Keyword Search (Fallback)

- Intelligent tokenization with stop-word filtering
- Weighted scoring (headings 3x body text)
- Pattern matching with suffix variants
- Special weighting for domain-specific terms

### Citation System

The system provides multi-level citations:

1. **Source File**: Path to documentation file
2. **Heading**: Section within documentation
3. **Line Numbers**: Exact line references [file:L123-L145]
4. **URL**: Original documentation URL when available
5. **Token Matches**: Shows which search terms matched

### Built-in Documentation

The server embeds curated content from Cedar-OS docs:

- Introduction to Cedar
- Getting Started guides
- Chat implementation
- Agent Input Context
- Agentic State management
- Voice features
- Spells system

You can augment with local docs via `CEDAR_DOCS_PATH`.

---

## Usage Guide

### Typical Workflow

1. **Initial Setup Check**

   ```
   User: "I want to add Cedar to my project"
   AI: [Calls checkInstall] → Analyzes project → Recommends approach
   ```

2. **Feature Implementation**

   ```
   User: "Add voice features to my chat"
   AI: [Calls voiceSpecialist] → Searches documentation → Provides implementation guide
   ```

3. **Troubleshooting**
   ```
   User: "RadialMenu not appearing"
   AI: [Calls spellsSpecialist with action="troubleshoot"] → Diagnoses issue
   ```

### Best Practices

1. **Always Start with checkInstall**: Ensures proper Cedar setup
2. **Use Specialist Tools**: Get domain-specific guidance
3. **Verify with Documentation**: All advice should reference docs
4. **Follow Installation Sequence**: Try recommended approach first

### Common Patterns

#### Adding Cedar to New Project

```
1. checkInstall → Empty directory detected
2. Recommends: npx cedar-os-cli plant-seed --yes
3. Creates complete project structure
```

#### Integrating with Existing Next.js

```
1. checkInstall → Existing Next.js detected
2. Recommends: npx cedar-os-cli add-sapling --yes
3. Preserves existing code, adds Cedar
```

#### Implementing Voice Features

```
1. voiceSpecialist("search", "VoiceButton setup")
2. Returns documentation with examples
3. voiceSpecialist("guide", "microphone permissions")
4. Provides implementation steps
```

---

## Core Components

### CedarModularMCPServer (server.py)

The main server class that orchestrates all MCP operations.

**Key Responsibilities:**

- Initialize and manage documentation indexes (Cedar and Mastra)
- Register and coordinate all tools
- Enforce documentation search requirements
- Track tool usage and validation
- Handle MCP protocol communication

**Critical Features:**

- **Dual Documentation Support**: Maintains separate indexes for Cedar and Mastra docs
- **Tool Registration System**: Dynamic registration of all available tools
- **Requirements Gate**: Optional confirmation system for guided workflows
- **Semantic Search Integration**: Automatic detection and use of vector search when available
- **Documentation Enforcement**: Tracks and validates documentation searches

### Shared Configuration (shared.py)

Central configuration hub containing all constants, rules, and shared utilities.

**Major Components:**

1. **Installation Commands & Rules**

   - Primary install: "npx cedar-os-cli plant-seed --yes"
   - Comprehensive adaptive installation guide
   - Smart detection of project type

2. **Expert Persona Configuration**

   - Behavioral guidelines for AI assistant
   - Emphasis on searching before creating
   - Component location awareness

3. **Error Handling Patterns**

   - Common error signatures requiring documentation search
   - Protocol for handling Cedar-related errors

4. **Implementation Rules**
   - Critical facts about Cedar component locations
   - Mandatory scanning procedures
   - Import verification requirements

---

## Services Layer

### DocsIndex Service (services/docs.py)

Sophisticated documentation indexing and search system.

**Features:**

- Multi-format support (.txt, .md, .json)
- Dual parsing modes for Cedar and Mastra
- Intelligent chunking with metadata
- Hybrid search (semantic + keyword)
- Line-level citations

### SemanticSearchService (services/semantic_search.py)

Vector-based search using Supabase and OpenAI.

**Components:**

- OpenAI text-embedding-3-small model
- Supabase vector database
- Cosine similarity matching
- Graceful fallback to keyword search

### FeatureResolver Service (services/feature.py)

Maps user goals to relevant Cedar features through keyword and use case matching.

### RequirementsClarifier Service (services/clarify.py)

Generates clarifying questions and validates setup requirements.

---

## Development Guide

### Adding New Tools

1. Create tool class in `tools/` directory
2. Implement required methods:
   - `list_tool()`: Returns MCP tool definition
   - `handle()`: Processes tool invocation
3. Register in server.py `_init_tools()` method
4. Add to tool_handlers dictionary

Example template:

```python
class NewSpecialistTool:
    name = "newSpecialist"

    def __init__(self, docs_index: DocsIndex):
        self.docs_index = docs_index

    def list_tool(self) -> McpTool:
        return McpTool(
            name=self.name,
            description="[MANDATORY] Tool description",
            inputSchema={...}
        )

    async def handle(self, arguments: Dict[str, Any]) -> List[TextContent]:
        # Implementation
        pass
```

### Adding Documentation Sources

1. Place documentation file in `docs/` directory
2. Update path resolution in server.py
3. Implement parser in DocsIndex if needed
4. Configure environment variable for path

### Extending Search Capabilities

1. **Keyword Search**: Modify tokenization in `DocsIndex.search()`
2. **Semantic Search**: Adjust embedding parameters in `SemanticSearchService`
3. **Ranking**: Update scoring algorithm in search methods

### Error Handling Patterns

Follow established patterns:

```python
try:
    # Main logic
    result = await operation()
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    # Return error response
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # Fallback behavior
```

---

## API Reference

### MCP Protocol Implementation

The server implements the standard MCP protocol:

#### Available Methods

1. **list_tools()**: Returns all available tools
2. **call_tool(name, arguments)**: Executes specific tool
3. **list_resources()**: Lists available resources
4. **read_resource(uri)**: Reads specific resource

#### Resource URIs

- `cedar://docs`: Cedar documentation metadata
- `mastra://docs`: Mastra documentation metadata

### Tool Response Format

Standard response structure:

```typescript
interface ToolResponse {
  action?: string; // Action performed
  results?: Array<any>; // Main results
  error?: string; // Error message if failed
  note?: string; // Additional notes
  INSTRUCTION?: string; // Usage instructions
  [key: string]: any; // Additional fields
}
```

### Search Result Format

```typescript
interface SearchResult {
  source: string; // Documentation source
  heading?: string; // Section heading
  content: string; // Content excerpt
  url?: string; // Original URL
  matchCount?: number; // Keyword match count
  matchedTokens?: Record<string, number>; // Token hit map
  similarity?: number; // Semantic similarity score
  citations?: {
    source: string;
    approxSpan: {
      start: number;
      end: number;
    };
    tokenLines: Record<string, number[]>;
  };
}
```

---

## Advanced Features

### Semantic Search Integration

When configured with Supabase and OpenAI:

1. **Automatic Detection**: System detects availability of credentials
2. **Hybrid Approach**: Tries semantic first, falls back to keyword
3. **Vector Storage**: Uses Supabase vector database
4. **Embedding Model**: OpenAI text-embedding-3-small (512 dimensions)

### Multi-Documentation Support

System maintains separate indexes for different documentation sources:

- **Cedar Index**: Primary Cedar-OS documentation
- **Mastra Index**: Backend framework documentation
- **Extensible**: Easy to add new documentation sources

### Project Intelligence

CheckInstallTool provides sophisticated project analysis:

1. **Framework Detection**: Identifies Next.js, React, Vue, etc.
2. **Dependency Analysis**: Checks for Cedar/Mastra presence
3. **Structure Recognition**: Understands project organization
4. **Adaptive Recommendations**: Tailors approach to project state

### Documentation Enforcement

Multiple layers ensure documentation-based responses:

1. **Tool Descriptions**: Marked as "MANDATORY"
2. **Server Tracking**: Logs documentation searches
3. **Result Instructions**: Include "BASE ANSWER ON DOCUMENTATION"
4. **Expert Persona**: Emphasizes documentation verification

---

## Troubleshooting

### Common Issues

1. **"Not in docs" responses**

   - Ensure documentation files are properly loaded
   - Check file paths in environment variables
   - Verify documentation parsing in logs

2. **Semantic search not working**

   - Verify Supabase and OpenAI credentials
   - Check network connectivity
   - Review error logs for API issues

3. **Tools not appearing**

   - Ensure proper tool registration in server.py
   - Check MCP client configuration
   - Verify server is running without errors

4. **Installation recommendations incorrect**
   - Update project analysis logic in CheckInstallTool
   - Verify directory structure detection
   - Check package.json parsing

### Debug Mode

Enable detailed logging:

```bash
CEDAR_LOG_LEVEL=DEBUG python -m cedar_mcp
```

### Testing Tools

Test individual tools:

```python
from cedar_mcp.tools.search_docs import SearchDocsTool
from cedar_mcp.services.docs import DocsIndex

# Initialize
docs_index = DocsIndex("path/to/docs.txt")
tool = SearchDocsTool(docs_index)

# Test search
import asyncio
results = asyncio.run(tool.handle({"query": "voice setup"}))
print(results)
```

---

## Performance Considerations

### Optimization Strategies

1. **Documentation Indexing**: Chunks are created once at startup
2. **Search Caching**: Consider implementing result caching
3. **Concurrent Tool Calls**: Tools can be called in parallel
4. **Simplified Output**: Reduces payload size significantly

### Scalability

- **Memory Usage**: Proportional to documentation size
- **Search Performance**: O(n) for keyword search, O(log n) for vector
- **Tool Execution**: Async design allows concurrent operations

---

## Security Considerations

### API Key Management

- Store keys in environment variables
- Never commit `.env` files
- Use secure key rotation practices

### Input Validation

- All tool inputs are validated against schemas
- Path traversal prevention in file operations
- SQL injection prevention in database queries

### Output Sanitization

- Documentation content is truncated to prevent oversized responses
- Sensitive information filtered from error messages

---

## Configuration Examples

### Minimal Configuration (Keyword Search Only)

```bash
# .env
CEDAR_LOG_LEVEL=INFO
CEDAR_MCP_SIMPLIFIED_OUTPUT=true
```

### Full Configuration (With Semantic Search)

```bash
# .env
CEDAR_LOG_LEVEL=INFO
CEDAR_MCP_SIMPLIFIED_OUTPUT=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
OPENAI_API_KEY=sk-...
CEDAR_DOCS_PATH=/custom/path/to/cedar_docs.txt
MASTRA_DOCS_PATH=/custom/path/to/mastra_docs.txt
```

### Development Configuration

```bash
# .env
CEDAR_LOG_LEVEL=DEBUG
CEDAR_MCP_SIMPLIFIED_OUTPUT=false
# Verbose output for debugging
```

---

## Notes

- MCP requires an initialization handshake; prefer running inside Claude Code or Cursor to interact with tools
- Stop the server with Ctrl+C
- The server includes built-in Cedar documentation, so it can answer without network access
- You can augment with local docs via `CEDAR_DOCS_PATH`

---

## Support

For issues, questions, or contributions:

- GitHub Issues: [Repository Issues URL]
- Documentation: Cedar-OS Documentation
- Community: Cedar Community Forum

---

_This documentation represents the complete architecture and functionality of the Cedar MCP Server. For the latest updates, refer to the source code and inline documentation._
