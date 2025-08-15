"""
Web wrapper for Cedar MCP Server to enable Railway deployment.
This creates an HTTP/WebSocket interface for the stdio-based MCP server.
"""

import asyncio
import json
import logging
import os
from typing import Optional
from aiohttp import web
from aiohttp import web_ws
import aiohttp_cors

from .server import CedarModularMCPServer

logger = logging.getLogger(__name__)

class MCPWebServer:
    def __init__(self):
        self.mcp_server = CedarModularMCPServer()
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
    
    def setup_routes(self):
        """Setup HTTP and WebSocket routes."""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/tool', self.handle_tool_call)
        self.app.router.add_get('/tools', self.list_tools)
        self.app.router.add_get('/ws', self.websocket_handler)
    
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
            "version": "0.3.0"
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