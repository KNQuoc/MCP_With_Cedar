## Cedar Modular MCP Server (Python)

Modular MCP server for Cedar-OS with clean separation between prompts and execution.

### Features
- **searchDocs**: query embedded Cedar-OS docs (and optionally local docs) and return relevant chunks with citations
- **getRelevantFeature**: map a goal/context to relevant Cedar-OS features
- **clarifyRequirements**: propose concise clarifying questions

### Quick Start
```bash
# Create and activate virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate  # zsh/bash

# Install (editable for console scripts)
pip install -e .
```

### Run
- Terminal (module):
```bash
python -m cedar_mcp
```

- Terminal (console script, after install -e .):
```bash
cedar-modular-mcp
```

- Cursor integration (`~/.cursor/mcp.json`):
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

### Environment
- **CEDAR_DOCS_PATH**: directory containing `.md`/`.json` docs to index (optional; built-in knowledge is included)
- **CEDAR_LOG_LEVEL**: `debug`, `info`, `warning`, `error` (default `info`)

### Tools
- **searchDocs**
  - input: `{ query: string, limit?: number }`
  - output: `{ prompt, results: [{ source, heading, content, matchCount }] }`

- **getRelevantFeature**
  - input: `{ goal: string, context?: string }`
  - output: `{ prompt, features: { goal, context, candidates: [{ feature, name, score }] } }`

- **clarifyRequirements**
  - input: `{ goal: string, known_constraints?: string[] }`
  - output: `{ prompt, questions: string[] }`

### Resources
- `cedar://docs` – describes the current docs index (`docs_path`, number of chunks, sources). Use `searchDocs` to query.

### Built-in Documentation
The server embeds curated content from Cedar-OS docs (Introduction, Getting Started, Chat, Agent Input Context, Agentic State) so it can answer without network access. You can augment with local docs via `CEDAR_DOCS_PATH`.

### Project Layout
```text
cedar-test/
  cedar_mcp/
    server.py              # MCP wiring and handlers
    __main__.py            # allow `python -m cedar_mcp`
    prompts/templates.py   # prompt builders (no execution)
    services/
      docs.py              # docs index/search (builtin + local)
      feature.py           # goal → feature mapping
      clarify.py           # clarifying questions
  pyproject.toml           # entrypoints & build config
  requirements.txt         # runtime deps (if using pip instead of pyproject)
```

### Notes
- MCP requires an initialization handshake; prefer running inside Cursor to interact with tools.
- Stop the server with Ctrl+C.


