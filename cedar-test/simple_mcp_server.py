#!/usr/bin/env python3
"""
Simplified MCP Server for Cursor compatibility.
Focuses on basic JSON-RPC without complex streaming.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from cedar_mcp.server import CedarModularMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware with permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize MCP server
mcp_server = CedarModularMCPServer()
sessions = {}

@app.get("/")
async def root():
    """Root endpoint - return server info."""
    return {
        "name": "cedar-mcp",
        "version": "0.5.0",
        "protocol": "jsonrpc",
        "status": "ready"
    }

@app.post("/")
@app.post("/jsonrpc")
@app.post("/mcp")
async def handle_request(request: Request):
    """Handle all JSON-RPC requests."""
    try:
        # Log all request headers and body for debugging
        headers = dict(request.headers)
        logger.info(f"Request headers: {headers}")
        
        body = await request.body()
        logger.info(f"Request body size: {len(body) if body else 0} bytes")
        logger.info(f"Request body: {body.decode('utf-8') if body else 'empty'}")
        
        # Handle empty body
        if not body:
            logger.warning("Empty request body")
            # Return a valid JSON-RPC error
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: Empty body"
                    }
                }
            )
        
        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
            )
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"Method: {method}, ID: {request_id}")
        
        # Handle methods
        if method == "initialize":
            session_id = str(uuid.uuid4())
            sessions[session_id] = {"initialized": True}
            
            # Try the newer protocol version that Cursor might expect
            client_version = params.get("protocolVersion", "2024-11-05")
            
            result = {
                "protocolVersion": client_version,  # Echo back client's version
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "cedar-mcp",
                    "version": "0.5.0"
                }
            }
            
            logger.info(f"Initialize successful, session: {session_id}")
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                },
                headers={
                    "Mcp-Session-Id": session_id
                }
            )
        
        elif method == "initialized":
            # Notification - no response needed
            logger.info("Client confirmed initialization")
            return Response(status_code=204)
        
        elif method == "ping":
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                }
            )
        
        elif method == "tools/list":
            tools = []
            for name, handler in mcp_server.tool_handlers.items():
                if hasattr(handler, 'list_tool'):
                    tool = handler.list_tool()
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
            
            logger.info(f"Returning {len(tools)} tools")
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }
            )
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Calling tool: {tool_name}")
            
            handler = mcp_server.tool_handlers.get(tool_name)
            if not handler:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                )
            
            # Call the tool
            try:
                if hasattr(handler, "handle"):
                    try:
                        result = await handler.handle(tool_name, arguments)
                    except TypeError:
                        result = await handler.handle(arguments)
                else:
                    raise ValueError(f"Handler lacks handle()")
                
                # Format result
                formatted = []
                for r in result:
                    if hasattr(r, 'text'):
                        formatted.append({"type": "text", "text": r.text})
                    else:
                        formatted.append({"type": "text", "text": str(r)})
                
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"content": formatted}
                    }
                )
            except Exception as e:
                logger.error(f"Tool error: {e}")
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                )
        
        else:
            logger.warning(f"Unknown method: {method}")
            return JSONResponse(
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
        logger.exception(f"Request error: {e}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            },
            status_code=500
        )

@app.get("/jsonrpc")
@app.get("/mcp")
async def handle_get(request: Request):
    """Handle GET requests - just acknowledge server is ready."""
    logger.info("GET request received - health check")
    
    # Just return a simple acknowledgment that server is ready
    # Don't return JSON-RPC format since this is just a health check
    return JSONResponse(
        content={
            "status": "ready",
            "server": "cedar-mcp",
            "version": "0.5.0",
            "transport": "http"
        },
        headers={
            "Content-Type": "application/json"
        }
    )

@app.options("/")
@app.options("/jsonrpc")
@app.options("/mcp")
async def handle_options():
    """Handle OPTIONS requests."""
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    
    logger.info(f"Starting Simple MCP Server on {host}:{port}")
    logger.info("Endpoints: /, /jsonrpc, /mcp")
    
    uvicorn.run(app, host=host, port=port, log_level="info")