"""
Web wrapper for Cedar MCP Server to enable Railway deployment.
This creates HTTP/WebSocket/SSE interfaces for the stdio-based MCP server.
Supports direct Claude Desktop integration via SSE transport.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Optional, Dict, Any
from aiohttp import web
from aiohttp import web_ws
from aiohttp.web_response import StreamResponse
import aiohttp_cors

from .server import CedarModularMCPServer

logger = logging.getLogger(__name__)

class MCPWebServer:
    def __init__(self):
        self.mcp_server = CedarModularMCPServer()
        self.app = web.Application()
        self.sse_sessions = {}  # Track SSE sessions
        self.setup_routes()
        self.setup_cors()
    
    def setup_routes(self):
        """Setup HTTP, WebSocket, and SSE routes."""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/tool', self.handle_tool_call)
        self.app.router.add_get('/tools', self.list_tools)
        self.app.router.add_get('/ws', self.websocket_handler)
        # SSE endpoints for Claude Desktop
        self.app.router.add_get('/sse', self.sse_handler)
        self.app.router.add_post('/sse', self.sse_handler)  # Claude may use POST
    
    def setup_cors(self):
        """Setup CORS for web clients."""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def health_check(self, request):
        """Health check endpoint for Railway."""
        return web.json_response({
            "status": "healthy",
            "service": "Cedar MCP Server",
            "version": "0.3.0",
            "transports": ["http", "websocket", "sse"],
            "url": "https://mcpwithcedar-production.up.railway.app",
            "sse_endpoint": "https://mcpwithcedar-production.up.railway.app/sse"
        })
    
    async def list_tools(self, request):
        """List available MCP tools."""
        # Get tool handlers from the MCP server
        tools = []
        for name, handler in self.mcp_server.tool_handlers.items():
            if hasattr(handler, 'list_tool'):
                tool = handler.list_tool()
                tools.append({"name": tool.name, "description": tool.description})
        return web.json_response({"tools": tools})
    
    async def handle_tool_call(self, request):
        """Handle tool execution via HTTP POST."""
        try:
            data = await request.json()
            tool_name = data.get('tool')
            arguments = data.get('arguments', {})
            
            # Get the tool handler
            handler = self.mcp_server.tool_handlers.get(tool_name)
            if not handler:
                return web.json_response({
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }, status=404)
            
            # Call the tool handler
            result = await handler.handle(arguments)
            
            # Format the result
            formatted_result = []
            for r in result:
                if hasattr(r, 'text'):
                    formatted_result.append({"type": "text", "text": r.text})
                else:
                    formatted_result.append({"type": "text", "text": str(r)})
            
            return web.json_response({
                "success": True,
                "result": formatted_result
            })
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def websocket_handler(self, request):
        """WebSocket handler for real-time MCP communication."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        async for msg in ws:
            if msg.type == web_ws.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    if data.get('type') == 'tool_call':
                        tool_name = data.get('tool')
                        handler = self.mcp_server.tool_handlers.get(tool_name)
                        
                        if not handler:
                            await ws.send_json({
                                "type": "error",
                                "error": f"Unknown tool: {tool_name}"
                            })
                            continue
                        
                        result = await handler.handle(data.get('arguments', {}))
                        formatted_result = []
                        for r in result:
                            if hasattr(r, 'text'):
                                formatted_result.append({"type": "text", "text": r.text})
                            else:
                                formatted_result.append({"type": "text", "text": str(r)})
                        
                        await ws.send_json({
                            "type": "result",
                            "result": formatted_result
                        })
                    elif data.get('type') == 'list_tools':
                        tools = []
                        for name, handler in self.mcp_server.tool_handlers.items():
                            if hasattr(handler, 'list_tool'):
                                tool = handler.list_tool()
                                tools.append({"name": tool.name, "description": tool.description})
                        await ws.send_json({
                            "type": "tools",
                            "tools": tools
                        })
                except Exception as e:
                    await ws.send_json({"type": "error", "error": str(e)})
            elif msg.type == web_ws.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
        
        return ws
    
    async def sse_handler(self, request):
        """SSE handler for Claude Desktop MCP integration."""
        response = StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        await response.prepare(request)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        self.sse_sessions[session_id] = response
        
        try:
            # Send initial connection event
            await self._send_sse_event(response, {
                "type": "connection",
                "sessionId": session_id,
                "status": "connected"
            })
            
            # Handle incoming messages via query params or POST body
            if request.method == 'POST':
                await self._handle_sse_post(request, response)
            else:
                # Keep connection alive and handle messages
                await self._handle_sse_stream(request, response)
                
        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            # Clean up session
            if session_id in self.sse_sessions:
                del self.sse_sessions[session_id]
        
        return response
    
    async def _send_sse_event(self, response, data):
        """Send an SSE event to the client."""
        event_data = f"data: {json.dumps(data)}\n\n"
        await response.write(event_data.encode('utf-8'))
    
    async def _handle_sse_post(self, request, response):
        """Handle SSE requests via POST (Claude Desktop style)."""
        try:
            data = await request.json()
            
            # Handle different MCP message types
            if data.get('method') == 'initialize':
                await self._send_sse_event(response, {
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {
                        "protocolVersion": "0.1.0",
                        "capabilities": {
                            "tools": True,
                            "resources": True
                        },
                        "serverInfo": {
                            "name": "cedar-mcp",
                            "version": "0.3.0"
                        }
                    }
                })
            
            elif data.get('method') == 'tools/list':
                tools = []
                for name, handler in self.mcp_server.tool_handlers.items():
                    if hasattr(handler, 'list_tool'):
                        tool = handler.list_tool()
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        })
                
                await self._send_sse_event(response, {
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {"tools": tools}
                })
            
            elif data.get('method') == 'tools/call':
                params = data.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                handler = self.mcp_server.tool_handlers.get(tool_name)
                if not handler:
                    await self._send_sse_event(response, {
                        "jsonrpc": "2.0",
                        "id": data.get('id', 1),
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
                else:
                    result = await handler.handle(arguments)
                    formatted_result = []
                    for r in result:
                        if hasattr(r, 'text'):
                            formatted_result.append({"type": "text", "text": r.text})
                        else:
                            formatted_result.append({"type": "text", "text": str(r)})
                    
                    await self._send_sse_event(response, {
                        "jsonrpc": "2.0",
                        "id": data.get('id', 1),
                        "result": {"content": formatted_result}
                    })
            
            elif data.get('method') == 'resources/list':
                # Return available resources
                await self._send_sse_event(response, {
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {
                        "resources": [
                            {
                                "uri": "cedar://docs",
                                "name": "Cedar Docs",
                                "description": "Indexed Cedar-OS documentation",
                                "mimeType": "application/json"
                            },
                            {
                                "uri": "mastra://docs",
                                "name": "Mastra Docs",
                                "description": "Indexed Mastra backend documentation",
                                "mimeType": "application/json"
                            }
                        ]
                    }
                })
                
        except Exception as e:
            logger.error(f"SSE POST handling error: {e}")
            await self._send_sse_event(response, {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            })
    
    async def _handle_sse_stream(self, request, response):
        """Handle SSE stream for keep-alive and periodic updates."""
        try:
            # Send periodic heartbeat to keep connection alive
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await self._send_sse_event(response, {
                    "type": "heartbeat",
                    "timestamp": os.popen('date').read().strip()
                })
        except asyncio.CancelledError:
            pass
    
    def run(self, host='0.0.0.0', port=None):
        """Run the web server."""
        port = port or int(os.environ.get('PORT', 8080))
        logger.info(f"Starting MCP Web Server on {host}:{port}")
        web.run_app(self.app, host=host, port=port)

def main():
    """Entry point for web server."""
    logging.basicConfig(
        level=os.getenv("CEDAR_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    server = MCPWebServer()
    server.run()

if __name__ == "__main__":
    main()