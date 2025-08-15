import logging
from dataclasses import dataclass
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .semantic_search import SemanticSearchService

logger = logging.getLogger(__name__)


@dataclass
class DocChunk:
    source: str
    heading: Optional[str]
    content: str
    url: Optional[str] = None
    section: Optional[str] = None


class DocsIndex:
    """Document indexer that supports multiple documentation sources.
    
    Can handle both Cedar and Mastra documentation formats, with the ability
    to load from different files based on the documentation type.
    """

    def __init__(self, docs_path: Optional[str] = None, doc_type: str = "cedar", enable_semantic_search: bool = False) -> None:
        self.docs_path = Path(docs_path) if docs_path else None
        self.doc_type = doc_type  # 'cedar' or 'mastra'
        self.chunks: List[DocChunk] = []
        # Keep original file contents for line-level citations
        self._file_texts: Dict[str, str] = {}
        # Initialize semantic search if enabled and credentials are available
        self.semantic_search: Optional[SemanticSearchService] = None
        if enable_semantic_search:
            try:
                logger.info(f"[{doc_type}] Attempting to initialize semantic search...")
                self.semantic_search = SemanticSearchService()
                logger.info(f"[{doc_type}] Semantic search initialized successfully")
            except ValueError as e:
                logger.info(f"[{doc_type}] Semantic search not available: {e}")
            except Exception as e:
                logger.error(f"[{doc_type}] Unexpected error initializing semantic search: {e}")
        # Only load from provided docs path
        if self.docs_path and self.docs_path.exists():
            self._load()

    def _load(self) -> None:
        """Load docs based on the doc_type (cedar or mastra).
        
        Supports .md/.markdown/.json and .txt files.
        For Mastra docs, uses special parsing to extract URLs and sections.
        """
        if not self.docs_path.is_file():
            logger.warning(f"Docs path is not a file: {self.docs_path}")
            return
            
        try:
            text = self.docs_path.read_text(encoding="utf-8")
            self._file_texts[str(self.docs_path)] = text
            
            # Parse based on doc type
            if self.doc_type == "mastra":
                self._parse_mastra_docs(text)
            else:
                # Default Cedar parsing or generic markdown
                self._parse_cedar_docs(text)
        except Exception as e:
            logger.error(f"Failed to load {self.doc_type} docs: {e}")

    def _parse_cedar_docs(self, text: str) -> None:
        """Parse Cedar documentation format.
        
        Cedar docs use standard markdown with Source URLs at the top.
        """
        lines = text.splitlines()
        current_source = None
        current_heading = None
        buffer = []
        
        for line in lines:
            # Check for source URL
            if line.startswith("Source: https://"):
                # Save previous chunk if exists
                if buffer and current_heading:
                    content = "\n".join(buffer).strip()
                    if content:
                        self.chunks.append(DocChunk(
                            source=str(self.docs_path),
                            heading=current_heading,
                            content=content,
                            url=current_source
                        ))
                buffer = []
                current_source = line[8:].strip()  # Remove "Source: " prefix
                continue
            
            # Check for markdown heading
            if line.startswith("#"):
                # Save previous chunk if exists
                if buffer and current_heading:
                    content = "\n".join(buffer).strip()
                    if content:
                        self.chunks.append(DocChunk(
                            source=str(self.docs_path),
                            heading=current_heading,
                            content=content,
                            url=current_source
                        ))
                buffer = []
                current_heading = line.lstrip("#").strip()
            else:
                buffer.append(line)
        
        # Save last chunk
        if buffer and current_heading:
            content = "\n".join(buffer).strip()
            if content:
                self.chunks.append(DocChunk(
                    source=str(self.docs_path),
                    heading=current_heading,
                    content=content,
                    url=current_source
                ))
    
    def _parse_mastra_docs(self, text: str) -> None:
        """Parse Mastra documentation format.
        
        The format includes:
        - Source URLs (Source: https://mastra.ai/...)
        - Section markers ([EN] Source: ...)
        - Markdown headings
        - Code blocks and content
        """
        lines = text.splitlines()
        current_source = None
        current_section = None
        current_heading = None
        buffer = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for source URL
            if line.startswith("Source: https://mastra.ai/"):
                # Save previous chunk if exists
                if buffer and current_heading:
                    content = "\n".join(buffer).strip()
                    if content:
                        self.chunks.append(DocChunk(
                            source=str(self.docs_path),
                            heading=current_heading,
                            content=content,
                            url=current_source,
                            section=current_section
                        ))
                buffer = []
                current_source = line[8:].strip()  # Remove "Source: " prefix
                i += 1
                continue
            
            # Check for section marker
            if line.startswith("[EN] Source:"):
                # Save previous chunk if exists
                if buffer and current_heading:
                    content = "\n".join(buffer).strip()
                    if content:
                        self.chunks.append(DocChunk(
                            source=str(self.docs_path),
                            heading=current_heading,
                            content=content,
                            url=current_source,
                            section=current_section
                        ))
                buffer = []
                current_section = line
                i += 1
                continue
            
            # Check for markdown heading
            if line.startswith("#"):
                # Save previous chunk if exists
                if buffer and current_heading:
                    content = "\n".join(buffer).strip()
                    if content:
                        self.chunks.append(DocChunk(
                            source=str(self.docs_path),
                            heading=current_heading,
                            content=content,
                            url=current_source,
                            section=current_section
                        ))
                buffer = []
                current_heading = line.lstrip("#").strip()
            else:
                buffer.append(line)
            
            i += 1
        
        # Save last chunk
        if buffer and current_heading:
            content = "\n".join(buffer).strip()
            if content:
                self.chunks.append(DocChunk(
                    source=str(self.docs_path),
                    heading=current_heading,
                    content=content,
                    url=current_source,
                    section=current_section
                ))


    async def search(self, query: str, limit: int = 5, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """Search over docs using semantic search if available, otherwise keyword-based search.

        Previous implementation required the full query string to appear verbatim
        inside a doc chunk, which often returned zero results for long queries.
        This version tokenizes the query and scores chunks by keyword matches,
        with a small boost for heading matches.
        
        If semantic search is enabled and available, it will be used first.
        """
        if not query:
            return []
        
        # Try semantic search first if available and enabled
        if use_semantic and self.semantic_search:
            try:
                logger.debug(f"[{self.doc_type}] Using semantic search for query: {query[:50]}...")
                semantic_results = await self.semantic_search.search_by_vector(
                    query=query,
                    limit=limit
                )
                
                if semantic_results:
                    logger.debug(f"[{self.doc_type}] Semantic search returned {len(semantic_results)} results")
                    # Convert semantic results to the expected format
                    results = []
                    import os
                    simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
                    
                    for sr in semantic_results:
                        # Filter out headers from metadata when simplified output is enabled
                        if simplified_env.lower() == "true" and sr.metadata:
                            filtered_metadata = {k: v for k, v in sr.metadata.items() if k != "headers"}
                        else:
                            filtered_metadata = sr.metadata
                            
                        entry = {
                            "source": sr.source or "supabase",
                            "heading": sr.metadata.get("heading"),
                            "content": sr.content[:2000],  # truncate for payload size
                            "similarity": sr.similarity,
                            "metadata": filtered_metadata
                        }
                        results.append(entry)
                    return results
            except Exception as e:
                logger.debug(f"[{self.doc_type}] Semantic search failed, falling back to keyword search: {e}")
        else:
            logger.debug(f"[{self.doc_type}] Using keyword search (semantic={use_semantic}, available={bool(self.semantic_search)})")

        def normalize(text: str) -> str:
            # Lowercase and replace non-alphanumeric with spaces, then collapse whitespace
            lowered = text.lower()
            cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
            return re.sub(r"\s+", " ", cleaned).strip()

        def tokenize(text: str) -> List[str]:
            tokens = normalize(text).split(" ")
            # Keep common short-but-meaningful tokens for both Cedar and Mastra
            short_whitelist = {"ui", "os", "ai", "llm", "sse", "ux", "mcp", "api", "jwt", "cli", "sdk"}
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
                # Count token hits allowing simple suffix variants
                pattern = rf"\b{re.escape(token)}\w*\b"
                heading_hits = len(re.findall(pattern, heading_text))
                body_hits = len(re.findall(pattern, body_text))
                
                # Give extra weight to doc-specific terms
                weight = 1.0
                if self.doc_type == "mastra" and token in ["mastra", "agent", "workflow", "tool", "memory"]:
                    weight = 2.0
                elif self.doc_type == "cedar" and token in ["cedar", "voice", "chat", "copilot", "mention"]:
                    weight = 2.0
                    
                token_total = (heading_hits * 3 + body_hits) * weight
                
                if token_total > 0:
                    token_hits[token] = int(token_total)
                    chunk_score += token_total

            if chunk_score > 0:
                scored.append((chunk_score, chunk, token_hits))

        # Sort by score desc, then by presence of more distinct tokens
        scored.sort(key=lambda x: (x[0], len(x[2])), reverse=True)
        top = scored[: max(0, int(limit))]

        # Check if simplified output is enabled
        import os
        simplified_env = os.getenv("CEDAR_MCP_SIMPLIFIED_OUTPUT", "true")
        
        results: List[Dict[str, Any]] = []
        for score, chunk, token_hits in top:
            entry: Dict[str, Any] = {
                "source": chunk.source,
                "heading": chunk.heading,
                "content": chunk.content[:2000],  # truncate for payload size
                "matchCount": int(score),
            }
            
            # Only include matchedTokens if not simplified
            if simplified_env.lower() != "true":
                entry["matchedTokens"] = token_hits
            
            # Add URL and section if available (for Mastra docs)
            if chunk.url:
                entry["url"] = chunk.url
            if chunk.section:
                entry["section"] = chunk.section
            
            # Add best-effort line-level citations when the source is a local file we loaded
            # Only include citations if not simplified
            if simplified_env.lower() != "true":
                if chunk.source and chunk.source.startswith("/") and chunk.source in self._file_texts and token_hits:
                    file_text = self._file_texts[chunk.source]
                    token_line_map: Dict[str, List[int]] = {}
                    all_lines: List[int] = []
                    for token in token_hits.keys():
                        lines_for_token = self._find_token_lines(file_text, token)
                        if lines_for_token:
                            token_line_map[token] = lines_for_token[:10]  # cap per token
                            all_lines.extend(lines_for_token)
                    if all_lines:
                        entry["citations"] = {
                            "source": chunk.source,
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
        """Return description of the loaded docs."""
        if self.doc_type == "mastra":
            sections = set()
            for chunk in self.chunks:
                if chunk.section:
                    # Extract the main section name from [EN] Source: ...
                    match = re.search(r'\[EN\] Source: https://mastra\.ai/en/docs/(.+?)(?:/|$)', chunk.section)
                    if match:
                        sections.add(match.group(1))
            
            return {
                "docs_path": str(self.docs_path) if self.docs_path else None,
                "num_chunks": len(self.chunks),
                "sections": sorted(sections),
                "type": "Mastra Documentation"
            }
        
        return {
            "docs_path": str(self.docs_path) if self.docs_path else None,
            "num_chunks": len(self.chunks),
            "sources": sorted({Path(c.source).name if c.source.startswith("/") else c.source for c in self.chunks}),
            "type": "Cedar Documentation"
        }