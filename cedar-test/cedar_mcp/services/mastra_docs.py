import logging
from dataclasses import dataclass
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MastraDocChunk:
    source: str
    heading: Optional[str]
    content: str
    url: Optional[str] = None
    section: Optional[str] = None


class MastraDocsIndex:
    """Document indexer for Mastra documentation.
    
    Specifically designed to work with the mastra_llms_full.txt file
    which contains fetched Mastra documentation.
    """

    def __init__(self, docs_path: Optional[str] = None) -> None:
        self.docs_path = Path(docs_path) if docs_path else None
        self.chunks: List[MastraDocChunk] = []
        # Keep original file contents for line-level citations
        self._file_texts: Dict[str, str] = {}
        
        # Only load from provided docs path
        if self.docs_path and self.docs_path.exists():
            self._load()

    def _load(self) -> None:
        """Load Mastra docs from the specified file path."""
        if not self.docs_path.is_file():
            logger.warning(f"Mastra docs path is not a file: {self.docs_path}")
            return
            
        try:
            text = self.docs_path.read_text(encoding="utf-8")
            self._file_texts[str(self.docs_path)] = text
            
            # Parse the Mastra docs format which includes URLs and sections
            self._parse_mastra_docs(text)
        except Exception as e:
            logger.error(f"Failed to load Mastra docs: {e}")

    def _parse_mastra_docs(self, text: str) -> None:
        """Parse the Mastra documentation format.
        
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
                        self.chunks.append(MastraDocChunk(
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
                        self.chunks.append(MastraDocChunk(
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
                        self.chunks.append(MastraDocChunk(
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
                self.chunks.append(MastraDocChunk(
                    source=str(self.docs_path),
                    heading=current_heading,
                    content=content,
                    url=current_source,
                    section=current_section
                ))

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Mastra docs using keyword-based search.
        
        Optimized for Mastra-specific terminology and concepts.
        """
        if not query:
            return []

        def normalize(text: str) -> str:
            # Lowercase and replace non-alphanumeric with spaces
            lowered = text.lower()
            cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
            return re.sub(r"\s+", " ", cleaned).strip()

        def tokenize(text: str) -> List[str]:
            tokens = normalize(text).split(" ")
            # Mastra-specific short tokens
            short_whitelist = {"mcp", "ai", "llm", "api", "jwt", "cli", "sdk"}
            return [t for t in tokens if len(t) >= 3 or t in short_whitelist]

        query_tokens = list(dict.fromkeys(tokenize(query)))  # unique, preserve order
        if not query_tokens:
            return []

        scored: List[Tuple[float, MastraDocChunk, Dict[str, int]]] = []

        for chunk in self.chunks:
            heading_text = normalize(chunk.heading or "")
            body_text = normalize(chunk.content)
            chunk_score = 0.0
            token_hits: Dict[str, int] = {}

            for token in query_tokens:
                # Count token hits with suffix variants
                pattern = rf"\b{re.escape(token)}\w*\b"
                heading_hits = len(re.findall(pattern, heading_text))
                body_hits = len(re.findall(pattern, body_text))
                
                # Give extra weight to Mastra-specific terms
                weight = 2.0 if token in ["mastra", "agent", "workflow", "tool", "memory"] else 1.0
                token_total = (heading_hits * 3 + body_hits) * weight
                
                if token_total > 0:
                    token_hits[token] = int(token_total)
                    chunk_score += token_total

            if chunk_score > 0:
                scored.append((chunk_score, chunk, token_hits))

        # Sort by score desc
        scored.sort(key=lambda x: (x[0], len(x[2])), reverse=True)
        top = scored[:limit]

        results: List[Dict[str, Any]] = []
        for score, chunk, token_hits in top:
            entry: Dict[str, Any] = {
                "source": chunk.source,
                "heading": chunk.heading,
                "content": chunk.content[:2000],  # truncate for payload size
                "matchCount": int(score),
                "matchedTokens": token_hits,
            }
            
            # Add URL and section if available
            if chunk.url:
                entry["url"] = chunk.url
            if chunk.section:
                entry["section"] = chunk.section
                
            results.append(entry)
            
        return results

    def describe(self) -> Dict[str, Any]:
        """Return description of the loaded Mastra docs."""
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