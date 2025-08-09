"""Cedar MCP modular package.

This package provides a modular MCP server with clearly separated
execution logic (services) and prompt templates (prompts).
"""

from .server import CedarModularMCPServer  # re-export for convenience

__all__ = ["CedarModularMCPServer"]


