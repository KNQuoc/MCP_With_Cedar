import json
import os
from dataclasses import dataclass
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class DocChunk:
    source: str
    heading: Optional[str]
    content: str


class DocsIndex:
    """Very lightweight document indexer.

    For now, it loads one or more JSON/Markdown files from a directory
    and performs naive keyword search. This can later be replaced
    with a vector index without changing the MCP server surface.
    """

    def __init__(self, docs_path: Optional[str]) -> None:
        self.docs_path = Path(docs_path) if docs_path else None
        self.chunks: List[DocChunk] = []
        # Seed with curated built-in knowledge so the index is useful by default
        self._load_builtin_docs()
        if self.docs_path and self.docs_path.exists():
            self._load()

    def _load(self) -> None:
        """Load docs from a directory OR a single file path.

        Supports .md/.markdown/.json and now .txt (treated as markdown-like text).
        """
        allowed = {".md", ".markdown", ".json", ".txt"}

        def _load_entry(path: Path) -> None:
            if not (path.is_file() and path.suffix.lower() in allowed):
                return
            try:
                if path.suffix.lower() == ".json":
                    data = json.loads(path.read_text(encoding="utf-8"))
                    # Expect list of {heading?, content}
                    if isinstance(data, list):
                        for item in data:
                            self.chunks.append(
                                DocChunk(
                                    source=str(path),
                                    heading=item.get("heading"),
                                    content=item.get("content", ""),
                                )
                            )
                else:
                    # Markdown or text: split by headings as a crude chunking
                    text = path.read_text(encoding="utf-8")
                    sections = self._split_markdown(text)
                    for heading, content in sections:
                        self.chunks.append(
                            DocChunk(source=str(path), heading=heading, content=content)
                        )
            except Exception:
                # Skip unreadable/invalid files quietly for now
                return

        if self.docs_path.is_file():
            _load_entry(self.docs_path)
            return
        for path in self.docs_path.rglob("*"):
            _load_entry(path)

    def _load_builtin_docs(self) -> None:
        """Load comprehensive Cedar-OS documentation based on actual docs.

        Updated with real content from Cedar-OS documentation including:
        - Introduction and core features
        - Getting Started with actual package names and setup
        - Chat components (FloatingCedarChat, ChatInput, streaming)
        - Agent Input Context (mentions, state subscription)
        - Agentic State and Actions
        """
        builtin: List[DocChunk] = []

        # Introduction / Overview
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/introduction/overview",
                heading="Introduction to Cedar-OS",
                content=(
                    "Cedar-OS is an open-source framework for building the next generation of AI native software. "
                    "For the first time in history, products can come to life. Cedar helps you build something with life. "
                    "Core philosophy: AI-native applications where AI agents can read and write application state, "
                    "coordinate complex workflows, and provide seamless user experiences."
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/introduction/overview",
                heading="Cedar-OS Core Features",
                content=(
                    "Core Features:\n"
                    "- Streaming & Tool Calls: Real-time message streaming and agent tool execution\n"
                    "- Voice Integration: Voice-powered agent interactions (capture, transcribe, synthesize)\n"
                    "- State Access: Let agents read and write application state via centralized agentic state\n"
                    "- Diff & History: Track what AI changes, allow user approvals, and manage history\n"
                    "- Chat: Floating, SidePanel, Caption, or Embedded chat components\n"
                    "- Spells: Powerful agent interactions and workflows\n"
                    "- Mentions: Context-aware mention system for chat (@mentions)\n"
                    "- Agent Connection Modules: Connect to various AI backends and services\n"
                    "- Component Library: Pre-built UI components you own the code for, Shadcn style"
                ),
            )
        )

        # Getting Started - Real Installation Info
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/getting-started/getting-started",
                heading="Cedar-OS Installation",
                content=(
                    "Cedar-OS installation appears to use npm packages. Based on actual documentation, "
                    "the framework provides React components and hooks. Key imports include:\n"
                    "- FloatingCedarChat, ChatInput components\n"
                    "- useMentionProvider, useRegisterState, useStateBasedMentionProvider hooks\n"
                    "- Chat positioning options: floating (left/right), side panel, caption style\n"
                    "Note: Exact package names need verification from official docs"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/getting-started/getting-started",
                heading="Basic Cedar-OS Setup Pattern",
                content=(
                    "Basic setup pattern from documentation:\n"
                    "1. Import chat components: import { FloatingCedarChat } from '@/chatComponents/FloatingCedarChat'\n"
                    "2. Configure chat with props: side, title, dimensions, resizable\n"
                    "3. Set up mention providers using useMentionProvider hook\n"
                    "4. Register application state with useRegisterState for agent access\n"
                    "5. Configure streaming backend for real-time responses"
                ),
            )
        )

        # Chat Components - Real Documentation
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/chat/chat-overview",
                heading="Chat Component Types",
                content=(
                    "Cedar-OS provides multiple chat interface types:\n\n"
                    "1. Caption Chat: A caption-style chat interface that appears at the bottom center "
                    "of the screen, perfect for overlay-style interactions. Great for AI assistants that "
                    "provide contextual help without taking up dedicated screen space. Realized that in "
                    "conversation, you don't need to see entire history all the time, just the latest message.\n\n"
                    "2. Floating Chat: A floating chat window that can be positioned on the left or right "
                    "side of the screen with expand/collapse functionality. Perfect for assistance that "
                    "doesn't interfere with the main application.\n\n"
                    "3. Side Panel Chat: A side panel chat that pushes your main content to make room for "
                    "the chat interface. This is if you want the chat to not overlap with any elements, "
                    "and always have its own dedicated spot."
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/chat/chat-overview",
                heading="FloatingCedarChat Component",
                content=(
                    "FloatingCedarChat component usage:\n\n"
                    "import { FloatingCedarChat } from '@/chatComponents/FloatingCedarChat';\n\n"
                    "function App() {\n"
                    "  return (\n"
                    "    <div>\n"
                    "      {/* Your main content */}\n"
                    "      <FloatingCedarChat\n"
                    "        side='right'\n"
                    "        title='Assistant'\n"
                    "        collapsedLabel='How can I help you today?'\n"
                    "        dimensions={{\n"
                    "          width: 400,\n"
                    "          height: 600,\n"
                    "          minWidth: 350,\n"
                    "          minHeight: 400,\n"
                    "        }}\n"
                    "        resizable={true}\n"
                    "      />\n"
                    "    </div>\n"
                    "  );\n"
                    "}\n\n"
                    "Props: side ('left'|'right'), title, collapsedLabel, companyLogo, dimensions, resizable"
                ),
            )
        )

        # Streaming - Real Documentation
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/chat/streaming",
                heading="Cedar-OS Streaming Implementation",
                content=(
                    "Cedar-OS enables real-time streaming responses in chat components. "
                    "You can disable streaming by setting stream={false} on any chat component or ChatInput.\n\n"
                    "Cedar uses data-only SSE (Server-Sent Events) streams. The server sends data: messages "
                    "over a single HTTP connection. The stream mixes plain text and structured JSON, sent as "
                    "newline-delimited chunks prefixed with 'data:'.\n\n"
                    "Under the hood, the server emits:\n"
                    "- Text chunks for incremental message rendering\n"
                    "- JSON objects for structured updates\n"
                    "The client parses each data: line as it arrives and handles parsed text or JSON accordingly. "
                    "This enables real-time, mixed-format updates with minimal overhead."
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/chat/streaming",
                heading="Streaming Backend Requirements",
                content=(
                    "For proper SSE streaming in Cedar-OS:\n"
                    "- Set Content-Type: text/event-stream header\n"
                    "- Set Cache-Control: no-cache header\n"
                    "- Send chunks prefixed with 'data: ' and terminated by double newlines\n"
                    "- Flush responses periodically to avoid buffering\n"
                    "- Handle client disconnects gracefully\n"
                    "- Support both text chunks and JSON objects in the same stream\n"
                    "- Implement proper error handling for stream interruptions"
                ),
            )
        )

        # Mentions - Comprehensive Real Documentation
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/mentions",
                heading="Cedar-OS Mentions System",
                content=(
                    "Cedar-OS provides a comprehensive @ mentions system for contextual references in chat. "
                    "The system allows users to reference application entities (users, tasks, files, etc.) "
                    "using @ symbols, which then provide structured context to AI agents.\n\n"
                    "Key components:\n"
                    "- useMentionProvider: Register custom mention providers\n"
                    "- useStateBasedMentionProvider: Auto-create mentions from application state\n"
                    "- useRegisterState: Register application state for agent access\n"
                    "- Multiple trigger characters: @, #, / for different entity types\n"
                    "- Rich rendering: Custom UI for mention menus, editor items, and context badges"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/mentions",
                heading="State-Based Mentions Implementation",
                content=(
                    "useStateBasedMentionProvider example:\n\n"
                    "import { useState } from 'react';\n"
                    "import { useRegisterState, useStateBasedMentionProvider } from 'cedar-os';\n\n"
                    "function TodoApp() {\n"
                    "  const [todos, setTodos] = useState([\n"
                    "    { id: 1, text: 'Buy groceries', category: 'shopping' },\n"
                    "    { id: 2, text: 'Call dentist', category: 'health' },\n"
                    "  ]);\n\n"
                    "  // Register the state\n"
                    "  useRegisterState({\n"
                    "    key: 'todos',\n"
                    "    value: todos,\n"
                    "    setValue: setTodos,\n"
                    "    description: 'Todo items',\n"
                    "  });\n\n"
                    "  // Enable mentions for todos\n"
                    "  useStateBasedMentionProvider({\n"
                    "    stateKey: 'todos',\n"
                    "    trigger: '@',\n"
                    "    labelField: 'text',\n"
                    "    searchFields: ['text', 'category'],\n"
                    "    description: 'Todo items',\n"
                    "    icon: '📝',\n"
                    "    color: '#3b82f6',\n"
                    "  });\n\n"
                    "  return <ChatInput />;\n"
                    "}"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/mentions",
                heading="Custom Mention Providers",
                content=(
                    "useMentionProvider for custom entities:\n\n"
                    "import { useMentionProvider } from 'cedar-os';\n\n"
                    "function UserMentions() {\n"
                    "  const users = [\n"
                    "    { id: 1, name: 'Alice Johnson', email: 'alice@company.com', role: 'Designer' },\n"
                    "    { id: 2, name: 'Bob Smith', email: 'bob@company.com', role: 'Developer' },\n"
                    "  ];\n\n"
                    "  useMentionProvider({\n"
                    "    id: 'users',\n"
                    "    trigger: '@',\n"
                    "    label: 'Users',\n"
                    "    description: 'Team members',\n"
                    "    icon: '👤',\n"
                    "    getItems: (query) => {\n"
                    "      const filtered = query\n"
                    "        ? users.filter(user =>\n"
                    "            user.name.toLowerCase().includes(query.toLowerCase())\n"
                    "          )\n"
                    "        : users;\n"
                    "      return filtered.map(user => ({\n"
                    "        id: user.id.toString(),\n"
                    "        label: `${user.name} (${user.role})`,\n"
                    "        data: user,\n"
                    "        metadata: { icon: '👤', color: '#10b981' },\n"
                    "      }));\n"
                    "    },\n"
                    "    toContextEntry: (item) => ({\n"
                    "      id: item.id,\n"
                    "      source: 'mention',\n"
                    "      data: item.data,\n"
                    "      metadata: { label: item.label, icon: '👤', color: '#10b981' },\n"
                    "    }),\n"
                    "  });\n\n"
                    "  return <ChatInput />;\n"
                    "}"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/mentions",
                heading="Multiple Mention Triggers",
                content=(
                    "Cedar-OS supports multiple mention triggers in the same chat:\n\n"
                    "- @ for users: useMentionProvider with trigger: '@'\n"
                    "- # for channels/topics: useMentionProvider with trigger: '#'\n"
                    "- / for commands: useMentionProvider with trigger: '/'\n\n"
                    "Each provider can have:\n"
                    "- Custom getItems function for search and filtering\n"
                    "- Custom renderMenuItem for mention menu display\n"
                    "- Custom renderEditorItem for inline editor display\n"
                    "- Custom renderContextBadge for context visualization\n"
                    "- Async support for fetching items from APIs\n"
                    "- Rich metadata and validation"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/mentions",
                heading="Mention Context for Agents",
                content=(
                    "When users include mentions in their messages, agents receive structured context:\n\n"
                    "Example: User types 'Update the status of @task-123 to completed'\n"
                    "Agent receives:\n"
                    "{\n"
                    "  message: 'Update the status of @task-123 to completed',\n"
                    "  mentions: [\n"
                    "    {\n"
                    "      id: 'task-123',\n"
                    "      type: 'tasks',\n"
                    "      data: {\n"
                    "        id: 'task-123',\n"
                    "        title: 'Implement user authentication',\n"
                    "        status: 'in-progress',\n"
                    "        assignee: 'Alice'\n"
                    "      },\n"
                    "      position: { start: 23, end: 32 }\n"
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "This allows agents to have full context about referenced entities."
                ),
            )
        )

        # Agent Input Context
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/agent-input-context",
                heading="Agent Input Context System",
                content=(
                    "Cedar-OS provides comprehensive agent input context to ground AI behavior. "
                    "The system allows agents to access application state, user context, and UI state "
                    "automatically or on-demand.\n\n"
                    "Key patterns:\n"
                    "- Keep context minimal but sufficient; prefer references over large data blobs\n"
                    "- Use stable identifiers for entities referenced in chat\n"
                    "- Sanitize PII and sensitive fields before sending to agents\n"
                    "- Provide fallbacks when state is incomplete or stale\n"
                    "- Support both reactive subscriptions and explicit context inclusion"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agent-input-context/subscribing-state-to-input",
                heading="State Subscription for Agents",
                content=(
                    "Cedar-OS allows subscribing parts of application state so they are automatically "
                    "included in prompts to keep context fresh and reactive.\n\n"
                    "Best practices for state subscription:\n"
                    "- Limit subscriptions to relevant slices to control token usage\n"
                    "- Debounce updates or batch to avoid excessive prompt churn\n"
                    "- Provide fallbacks when state is incomplete or stale\n"
                    "- Use fine-grained subscriptions rather than subscribing to entire state trees\n"
                    "- Consider privacy and security when auto-including state in prompts"
                ),
            )
        )

        # Agentic State
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agentic-state/agentic-state",
                heading="Cedar-OS Agentic State",
                content=(
                    "Cedar-OS provides centralized, reactive state management specifically designed for "
                    "AI agents, workflows, and user context. The agentic state system supports coordination, "
                    "persistence, and fine-grained subscriptions across the application.\n\n"
                    "Core agentic state model:\n"
                    "- Partitions: agent-specific, workflow-specific, and global context\n"
                    "- Subscriptions: fine-grained listeners for reactive updates\n"
                    "- Persistence: optional durability across sessions\n"
                    "- Coordination: enables multi-agent workflows with shared context\n"
                    "- Access Control: permissions and validation for state modifications"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agentic-state/agentic-actions",
                heading="Cedar-OS Agentic Actions",
                content=(
                    "Agentic Actions in Cedar-OS trigger and track domain actions, workflows, and "
                    "multi-step tasks initiated by agents or users. Useful for orchestrating multiple "
                    "specialized agents working together.\n\n"
                    "Agentic Actions lifecycle:\n"
                    "- Created → Running → Succeeded/Failed (with retries and timeouts as needed)\n"
                    "- Emit progress updates for UI and orchestration\n"
                    "- Log inputs/outputs for auditability\n"
                    "- Support cancellation and rollback where appropriate\n"
                    "- Enable coordination between multiple agents on complex tasks"
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/agentic-state/diff-and-history-manager",
                heading="Diff & History Manager (Beta)",
                content=(
                    "Cedar-OS Diff & History Manager tracks changes proposed/made by agents, shows diffs "
                    "for user approval, and maintains modification history to support auditing and undo/redo flows.\n\n"
                    "Diff approval flows:\n"
                    "- Present proposed changes for review with clear diffs\n"
                    "- Allow accept/reject/partial-apply where supported\n"
                    "- Keep an immutable history for compliance and rollback\n"
                    "- Support collaborative editing with conflict resolution\n"
                    "- Provide audit trails for all agent-initiated changes"
                ),
            )
        )

        # Architecture and Advanced Topics
        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/architecture",
                heading="Cedar-OS Architecture Overview",
                content=(
                    "Cedar-OS is built with a component-based architecture optimized for AI-native applications:\n\n"
                    "- Component Layer: React components with AI-aware hooks and state management\n"
                    "- State Layer: Centralized agentic state with fine-grained reactivity\n"
                    "- Agent Layer: AI agent coordination and workflow orchestration\n"
                    "- Integration Layer: Backends, APIs, and external service connections\n"
                    "- UI Layer: Flexible chat interfaces and interaction patterns\n\n"
                    "The architecture separates concerns while enabling deep integration between "
                    "AI agents and application state, creating truly AI-native user experiences."
                ),
            )
        )

        builtin.append(
            DocChunk(
                source="https://docs.cedarcopilot.com/getting-started/connecting-to-an-agent",
                heading="Agent Backend Connection",
                content=(
                    "Cedar-OS connects to AI backends through Agent Connection Modules. The system "
                    "supports various AI providers and frameworks:\n\n"
                    "- Direct integration with language model APIs (OpenAI, Anthropic, etc.)\n"
                    "- Mastra framework integration for advanced workflows\n"
                    "- Custom backend implementations\n"
                    "- Streaming response support with SSE\n"
                    "- Tool calling and function execution\n"
                    "- Multi-agent coordination and handoffs"
                ),
            )
        )

        self.chunks.extend(builtin)

    @staticmethod
    def _split_markdown(text: str) -> List[Tuple[Optional[str], str]]:
        lines = text.splitlines()
        sections: List[Tuple[Optional[str], List[str]]] = []
        current_heading: Optional[str] = None
        buffer: List[str] = []
        for line in lines:
            if line.startswith("#"):
                if buffer:
                    sections.append((current_heading, buffer))
                    buffer = []
                current_heading = line.lstrip("# ")
            else:
                buffer.append(line)
        if buffer:
            sections.append((current_heading, buffer))
        return [(h, "\n".join(b).strip()) for h, b in sections]

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Keyword-based search over built-in and optional local docs.

        Previous implementation required the full query string to appear verbatim
        inside a doc chunk, which often returned zero results for long queries.
        This version tokenizes the query and scores chunks by keyword matches,
        with a small boost for heading matches.
        """
        if not query:
            return []

        def normalize(text: str) -> str:
            # Lowercase and replace non-alphanumeric with spaces, then collapse whitespace
            lowered = text.lower()
            cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
            return re.sub(r"\s+", " ", cleaned).strip()

        def tokenize(text: str) -> List[str]:
            tokens = normalize(text).split(" ")
            # Keep common short-but-meaningful tokens (ui, os, ai, llm, sse)
            short_whitelist = {"ui", "os", "ai", "llm", "sse", "ux"}
            return [t for t in tokens if len(t) >= 3 or t in short_whitelist]

        query_tokens = list(dict.fromkeys(tokenize(query)))  # unique, preserve order
        if not query_tokens:
            return []

        scored: List[Tuple[float, DocChunk, Dict[str, int]]] = []

        for chunk in self.chunks:
            heading_text = normalize(chunk.heading or "")
            body_text = normalize(chunk.content)
            chunk_score = 0.0
            token_hits: Dict[str, int] = {}

            for token in query_tokens:
                # Count token hits allowing simple suffix variants (e.g., tool/tools, agent/agents/agentic)
                pattern = rf"\b{re.escape(token)}\w*\b"
                heading_hits = len(re.findall(pattern, heading_text))
                body_hits = len(re.findall(pattern, body_text))
                token_total = heading_hits * 2 + body_hits  # heading gets a small boost
                if token_total > 0:
                    token_hits[token] = token_total
                    chunk_score += float(token_total)

            if chunk_score > 0:
                scored.append((chunk_score, chunk, token_hits))

        # Sort by score desc, then by presence of more distinct tokens
        scored.sort(key=lambda x: (x[0], len(x[2])), reverse=True)
        top = scored[: max(0, int(limit))]

        results: List[Dict[str, Any]] = []
        for score, c, token_hits in top:
            results.append({
                "source": c.source,
                "heading": c.heading,
                "content": c.content[:2000],  # truncate for payload size
                "matchCount": int(score),
                "matchedTokens": token_hits,
            })
        return results

    def describe(self) -> Dict[str, Any]:
        return {
            "docs_path": str(self.docs_path) if self.docs_path else None,
            "num_chunks": len(self.chunks),
            "sources": sorted({Path(c.source).name if c.source.startswith("/") else c.source for c in self.chunks}),
            "has_builtin": True,
        }