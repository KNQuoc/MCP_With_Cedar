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
    # Railway provides RAILWAY_STATIC_URL or we construct it from the app name
    railway_url = os.getenv("RAILWAY_STATIC_URL") or os.getenv("RAILWAY_URL") or "https://mcpwithcedar-production.up.railway.app"
    return {
        "status": "healthy",
        "service": "Cedar MCP Server (FastAPI)",
        "version": "0.4.0",
        "transports": ["http", "sse"],
        "url": railway_url,
        "endpoints": {
            "jsonrpc": f"{railway_url}/jsonrpc",
            "sse": f"{railway_url}/sse"
        }
    }

@app.get("/health")
async def health():
    """Alternative health check endpoint."""
    return {"status": "ok"}

@app.options("/mcp")
@app.options("/jsonrpc")
@app.options("/sse")
async def handle_options():
    """Handle OPTIONS requests for CORS preflight."""
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.post("/mcp")
@app.post("/jsonrpc")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC requests for MCP."""
    try:
        # Log request details for debugging
        logger.info(f"Request path: {request.url.path}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get request body
        body = await request.body()
        logger.info(f"Request body: {body.decode('utf-8') if body else 'empty'}")
        
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
        
        elif method == "notifications/initialized":
            # Alternative notification endpoint some clients use
            logger.info("Client sent notifications/initialized")
            return Response(status_code=204)
        
        elif method == "ping":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        
        elif method == "prompts/list":
            logger.info("Processing prompts/list request")
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"prompts": []}
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
            # Check if this is a notification (starts with notifications/)
            if method and method.startswith("notifications/"):
                logger.info(f"Received notification: {method}")
                # Notifications don't need a response
                return Response(status_code=204)
            
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
    """Handle GET requests - just acknowledge server is ready."""
    logger.info("GET request received - health check")
    # Return simple JSON (not JSON-RPC) for health check
    return JSONResponse(content={
        "status": "ready",
        "server": "cedar-mcp",
        "version": "0.4.0",
        "transport": "http"
    })

@app.get("/sse")
async def handle_sse():
    """Handle SSE connections for MCP - Claude Code style."""
    logger.info("SSE connection requested from Claude Code")
    
    async def event_generator():
        """Generate SSE events for Claude Code."""
        try:
            # Don't send any initial events - Claude Code will POST to establish connection
            # Just keep the connection alive
            while True:
                await asyncio.sleep(30)
                # Send keepalive as comment (not data)
                yield f": keepalive\n\n"
                
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        except Exception as e:
            logger.error(f"SSE error: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id",
            "X-Accel-Buffering": "no",  # Disable nginx/proxy buffering
        }
    )

@app.post("/sse")
async def handle_sse_post(request: Request):
    """Handle SSE POST requests - MCP over SSE for Claude Code."""
    # Claude Code sends JSON-RPC over POST to SSE endpoint
    # We process it and return the response as SSE events
    try:
        body = await request.body()
        if not body:
            # Return SSE formatted error
            return StreamingResponse(
                iter([f'data: {json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Empty request"}})}\n\n']),
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
        
        logger.info(f"SSE POST: method={method}")
        
        # Process the request using the same logic as JSON-RPC
        if method == "initialize":
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
            
            # Return as SSE event
            return StreamingResponse(
                iter([f'data: {json.dumps(response)}\n\n']),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                    "Mcp-Session-Id": session_id
                }
            )
        
        # For other methods, use the existing JSON-RPC handler logic
        # but return as SSE events
        json_response = await handle_jsonrpc(request)
        response_body = json.loads(json_response.body)
        
        return StreamingResponse(
            iter([f'data: {json.dumps(response_body)}\n\n']),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"SSE POST error: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
        if "request_id" in locals() and request_id:
            error_response["id"] = request_id
            
        return StreamingResponse(
            iter([f'data: {json.dumps(error_response)}\n\n']),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            }
        )

def main():
    """Entry point for the FastAPI MCP server."""
    # Railway sets PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    
    logger.info(f"Starting FastAPI MCP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()