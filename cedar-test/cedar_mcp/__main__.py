import asyncio
import logging
import os

from .server import main as run_main


if __name__ == "__main__":
    # Allow 'python -m cedar_mcp'
    asyncio.run(run_main())


