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
        # Keep original file contents for line-level citations
        self._file_texts: Dict[str, str] = {}
        # Only load from provided docs path (e.g., cedar_llms_full.txt)
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
                    # Persist full file text for later line-level citation lookup
                    self._file_texts[str(path)] = text
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
        return  # disabled; rely solely on external cedar_llms_full.txt

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
            entry: Dict[str, Any] = {
                "source": c.source,
                "heading": c.heading,
                "content": c.content[:2000],  # truncate for payload size
                "matchCount": int(score),
                "matchedTokens": token_hits,
            }
            # Add best-effort line-level citations when the source is a local file we loaded
            if c.source and c.source.startswith("/") and c.source in self._file_texts and token_hits:
                file_text = self._file_texts[c.source]
                token_line_map: Dict[str, List[int]] = {}
                all_lines: List[int] = []
                for token in token_hits.keys():
                    lines_for_token = self._find_token_lines(file_text, token)
                    if lines_for_token:
                        token_line_map[token] = lines_for_token[:10]  # cap per token
                        all_lines.extend(lines_for_token)
                if all_lines:
                    entry["citations"] = {
                        "source": c.source,
                        "approxSpan": {
                            "start": min(all_lines),
                            "end": max(all_lines),
                        },
                        "tokenLines": token_line_map,
                    }
            results.append(entry)
        return results

    @staticmethod
    def _compute_line_number_index(text: str) -> List[int]:
        """Return cumulative character offsets at the start of each 1-based line.

        This enables fast char-index → line-number conversions.
        """
        offsets = [0]
        running = 0
        for part in text.splitlines(keepends=True):
            running += len(part)
            offsets.append(running)
        return offsets

    @staticmethod
    def _char_index_to_line(offsets: List[int], index: int) -> int:
        # Binary search for the greatest offset <= index
        lo, hi = 0, len(offsets) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if offsets[mid] <= index:
                lo = mid + 1
            else:
                hi = mid - 1
        return max(1, hi + 1)  # Convert to 1-based line number

    def _find_token_lines(self, text: str, token: str) -> List[int]:
        """Find 1-based line numbers for a token (word-boundary, case-insensitive)."""
        try:
            pattern = re.compile(rf"\b{re.escape(token)}\w*\b", re.IGNORECASE)
            offsets = self._compute_line_number_index(text)
            lines: List[int] = []
            for match in pattern.finditer(text):
                start_idx = match.start()
                line_num = self._char_index_to_line(offsets, start_idx)
                lines.append(line_num)
            # Deduplicate while preserving order
            seen = set()
            unique_lines: List[int] = []
            for ln in lines:
                if ln not in seen:
                    seen.add(ln)
                    unique_lines.append(ln)
            return unique_lines
        except Exception:
            return []

    def describe(self) -> Dict[str, Any]:
        return {
            "docs_path": str(self.docs_path) if self.docs_path else None,
            "num_chunks": len(self.chunks),
            "sources": sorted({Path(c.source).name if c.source.startswith("/") else c.source for c in self.chunks}),
            "has_builtin": False,
        }