#!/usr/bin/env python3
"""
FastAPI SSE implementation for MCP that works with Claude Code.
This creates a proper SSE transport that Claude Code can connect to.
"""

import os
import json
import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response
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

class SSEConnection:
    """Manages a single SSE connection."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.queue = asyncio.Queue()
        self.active = True

class MCPFastAPIServer:
    def __init__(self):
        self.mcp_server = CedarModularMCPServer()
        self.sse_connections: Dict[str, SSEConnection] = {}
        
    async def initialize_mcp(self):
        """Initialize the MCP server."""
        logger.info("MCP server initialized")
    
    async def handle_mcp_request(self, method: str, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle an MCP request and return the response."""
        
        if method == "initialize":
            return {
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
        
        elif method == "initialized":
            # Notification - no response
            return None
            
        elif method == "tools/list":
            tools = []
            for name, handler in self.mcp_server.tool_handlers.items():
                if hasattr(handler, 'list_tool'):
                    tool = handler.list_tool()
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Call tool
            handler = self.mcp_server.tool_handlers.get(tool_name)
            if not handler:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
            
            try:
                # Call the handler
                if hasattr(handler, "handle"):
                    try:
                        result = await handler.handle(tool_name, arguments)
                    except TypeError:
                        result = await handler.handle(arguments)
                else:
                    raise ValueError(f"Handler for {tool_name} lacks handle()")
                
                # Format results
                formatted_result = []
                for r in result:
                    if hasattr(r, 'text'):
                        formatted_result.append({"type": "text", "text": r.text})
                    else:
                        formatted_result.append({"type": "text", "text": str(r)})
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": formatted_result}
                }
                
            except Exception as e:
                logger.exception(f"Tool execution error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                }
        
        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": [
                        {
                            "uri": "cedar://docs",
                            "name": "Cedar Docs",
                            "description": "Cedar-OS documentation",
                            "mimeType": "application/json"
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MCP FastAPI server")
    await app.state.mcp.initialize_mcp()
    yield
    # Shutdown
    logger.info("Shutting down MCP FastAPI server")

app = FastAPI(lifespan=lifespan)

# Add CORS
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
    railway_url = os.getenv("RAILWAY_STATIC_URL") or "https://mcpwithcedar-production.up.railway.app"
    return {
        "status": "healthy",
        "service": "Cedar MCP Server (FastAPI)",
        "version": "0.4.0",
        "transports": ["sse"],
        "url": railway_url,
        "endpoints": {
            "sse": f"{railway_url}/sse"
        }
    }

@app.get("/sse")
async def handle_sse_get():
    """
    Handle SSE GET connections from Claude Code.
    This establishes a long-lived connection for server-sent events.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"SSE GET connection established: {session_id}")
    
    # Create connection object
    connection = SSEConnection(session_id)
    app.state.mcp.sse_connections[session_id] = connection
    
    async def event_generator():
        """Generate SSE events for this connection."""
        try:
            # Send initial connection event with session ID
            # This tells Claude Code that the connection is ready
            init_msg = {
                "type": "connection",
                "sessionId": session_id
            }
            yield f"event: open\ndata: {json.dumps(init_msg)}\nid: {session_id}\n\n"
            
            # Keep connection alive and send queued messages
            while connection.active:
                try:
                    # Wait for messages with timeout for keepalive
                    message = await asyncio.wait_for(
                        connection.queue.get(), 
                        timeout=30.0
                    )
                    
                    # Send the message as SSE event
                    yield f"data: {json.dumps(message)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield f": keepalive\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE generator: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled: {session_id}")
        finally:
            # Clean up connection
            connection.active = False
            if session_id in app.state.mcp.sse_connections:
                del app.state.mcp.sse_connections[session_id]
            logger.info(f"SSE connection closed: {session_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/sse")
async def handle_sse_post(request: Request):
    """
    Handle SSE POST requests from Claude Code.
    These are JSON-RPC requests that expect SSE-formatted responses.
    """
    try:
        # Get session ID from header
        session_id = request.headers.get("X-Session-Id")
        
        # Parse request body
        body = await request.body()
        if not body:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: Empty body"}
            }
            # Return as SSE event
            return StreamingResponse(
                iter([f"data: {json.dumps(error_response)}\n\n"]),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
        data = json.loads(body)
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"SSE POST: method={method}, session={session_id}")
        
        # Handle the MCP request
        response = await app.state.mcp.handle_mcp_request(method, params, request_id)
        
        if response is None:
            # Notification - no response needed
            return Response(status_code=204)
        
        # If we have an active SSE connection for this session, queue the response
        if session_id and session_id in app.state.mcp.sse_connections:
            connection = app.state.mcp.sse_connections[session_id]
            await connection.queue.put(response)
            # Return empty SSE response to acknowledge
            return StreamingResponse(
                iter([": ack\n\n"]),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
        # Otherwise return as SSE event directly
        return StreamingResponse(
            iter([f"data: {json.dumps(response)}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"}
        }
        return StreamingResponse(
            iter([f"data: {json.dumps(error_response)}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        logger.exception(f"SSE POST error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)}
        }
        if "request_id" in locals():
            error_response["id"] = request_id
        
        return StreamingResponse(
            iter([f"data: {json.dumps(error_response)}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            }
        )

@app.options("/sse")
async def handle_sse_options():
    """Handle OPTIONS requests for CORS preflight."""
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )

def main():
    """Entry point for the FastAPI MCP server."""
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    
    logger.info(f"Starting FastAPI MCP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()