#!/usr/bin/env python3
"""
FastAPI wrapper for Cedar MCP Server to enable Railway deployment.
This creates HTTP/SSE interfaces for the stdio-based MCP server.
"""

import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from cedar_mcp.server import CedarModularMCPServer

# Configure logging
logging.basicConfig(
    level=os.getenv("CEDAR_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class MCPFastAPIServer:
    def __init__(self):
        self.mcp_server = CedarModularMCPServer()
        self.sessions = {}  # Track sessions
        
    async def initialize_mcp(self):
        """Initialize the MCP server."""
        # Initialize the MCP server if needed
        logger.info("MCP server initialized")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Call a tool with the MCP server's logic."""
        import mcp.types as types
        
        try:
            # Track documentation search tools
            doc_search_tools = {
                "searchDocs", "mastraSpecialist", "voiceSpecialist", 
                "spellsSpecialist", "contextSpecialist"
            }
            
            if name in doc_search_tools:
                logger.info(f"Documentation search: {name} with query: {arguments.get('query', '')}")
            
            handler = self.mcp_server.tool_handlers.get(name)
            if not handler:
                raise ValueError(f"Unknown tool: {name}")
            
            # Call the handler
            if hasattr(handler, "handle"):
                try:
                    result = await handler.handle(name, arguments)
                except TypeError:
                    result = await handler.handle(arguments)
            else:
                raise ValueError(f"Handler for {name} lacks handle()")
            
            # Format results
            formatted_result = []
            for r in result:
                if hasattr(r, 'text'):
                    formatted_result.append({"type": "text", "text": r.text})
                else:
                    formatted_result.append({"type": "text", "text": str(r)})
            
            return formatted_result
            
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return [{"type": "text", "text": json.dumps({"error": str(e)})}]

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MCP FastAPI server")
    await app.state.mcp.initialize_mcp()
    yield
    # Shutdown
    logger.info("Shutting down MCP FastAPI server")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP server
app.state.mcp = MCPFastAPIServer()

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Cedar MCP Server (FastAPI)",
        "version": "0.4.0",
        "transports": ["http", "sse"],
        "url": os.getenv("RAILWAY_URL", "http://localhost:8000")
    }

@app.get("/health")
async def health():
    """Alternative health check endpoint."""
    return {"status": "ok"}

@app.post("/mcp")
@app.post("/jsonrpc")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC requests for MCP."""
    try:
        # Get request body
        body = await request.body()
        logger.info(f"Received request: {body[:500] if body else 'empty'}...")
        
        if not body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: Empty body"
                    }
                }
            )
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
            )
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"Processing method: {method}")
        
        # Handle different MCP methods
        if method == "initialize":
            # Generate session ID
            session_id = str(uuid.uuid4())
            app.state.mcp.sessions[session_id] = {
                "initialized": True,
                "protocol_version": params.get("protocolVersion", "2024-11-05")
            }
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "cedar-mcp",
                        "version": "0.4.0"
                    }
                }
            }
            
            logger.info(f"Initialized session: {session_id}")
            return JSONResponse(
                content=response,
                headers={"Mcp-Session-Id": session_id}
            )
        
        elif method == "initialized":
            # Client confirmation - notification, no response needed
            logger.info("Client confirmed initialization")
            return Response(status_code=204)
        
        elif method == "ping":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        
        elif method == "tools/list":
            tools = []
            for name, handler in app.state.mcp.mcp_server.tool_handlers.items():
                if hasattr(handler, 'list_tool'):
                    tool = handler.list_tool()
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
            
            logger.info(f"Returning {len(tools)} tools")
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            })
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Calling tool: {tool_name}")
            result = await app.state.mcp.call_tool(tool_name, arguments)
            
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": result}
            })
        
        elif method == "resources/list":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": [
                        {
                            "uri": "cedar://docs",
                            "name": "Cedar Docs",
                            "description": "Cedar-OS documentation",
                            "mimeType": "application/json"
                        },
                        {
                            "uri": "mastra://docs",
                            "name": "Mastra Docs",
                            "description": "Mastra backend documentation",
                            "mimeType": "application/json"
                        }
                    ]
                }
            })
        
        else:
            logger.warning(f"Unknown method: {method}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )
    
    except Exception as e:
        logger.exception(f"Request handling error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
        )

@app.get("/mcp")
@app.get("/jsonrpc")
async def handle_get():
    """Handle GET requests - health check only."""
    logger.info("GET request received")
    return JSONResponse(content={})

@app.get("/sse")
async def handle_sse():
    """Handle SSE connections."""
    logger.info("SSE connection requested")
    
    async def generate():
        # Send initial connection message
        yield "data: {\"type\": \"connected\"}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield ": keepalive\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable proxy buffering
        }
    )

@app.post("/sse")
async def handle_sse_post(request: Request):
    """Handle SSE POST requests."""
    # Delegate to JSON-RPC handler
    return await handle_jsonrpc(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting FastAPI MCP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)