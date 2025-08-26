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
from datetime import datetime
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
        # OAuth discovery endpoints (indicate no auth required)
        self.app.router.add_get('/.well-known/oauth-protected-resource', self.oauth_discovery)
        self.app.router.add_get('/.well-known/oauth-protected-resource/sse', self.oauth_discovery)
        self.app.router.add_get('/.well-known/oauth-authorization-server', self.oauth_discovery)
        self.app.router.add_get('/.well-known/oauth-authorization-server/sse', self.oauth_discovery)
        self.app.router.add_get('/.well-known/openid-configuration', self.oauth_discovery)
        self.app.router.add_get('/.well-known/openid-configuration/sse', self.oauth_discovery)
        self.app.router.add_get('/sse/.well-known/openid-configuration', self.oauth_discovery)
        self.app.router.add_post('/register', self.register_handler)
        # JSON-RPC endpoint for Cursor
        self.app.router.add_post('/jsonrpc', self.jsonrpc_handler)
        self.app.router.add_get('/jsonrpc', self.jsonrpc_handler)
    
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
    
    async def _call_tool_with_server_logic(self, name: str, arguments: Dict[str, Any]):
        """
        Call tool handler with the same logic as the MCP server's handle_call_tool method.
        This ensures simplified output and environment variable handling works consistently.
        """
        import json
        import mcp.types as types
        
        try:
            # Track that a documentation search tool has been called
            doc_search_tools = {
                "searchDocs", "mastraSpecialist", "voiceSpecialist", 
                "spellsSpecialist", "contextSpecialist"
            }
            
            # Log documentation search for validation
            if name in doc_search_tools:
                logger.info(f"Documentation search performed: {name} with query: {arguments.get('query', '')}")
            
            # Soft enforcement - recommend but don't block most tools
            allowed_without_confirm = {
                "clarifyRequirements", "confirmRequirements", "searchDocs", 
                "mastraSpecialist", "checkInstall", "voiceSpecialist", 
                "spellsSpecialist", "contextSpecialist"
            }
            
            if name not in allowed_without_confirm and not self.mcp_server._requirements_confirmed:
                # Soft suggestion instead of hard block
                if name == "getRelevantFeature" and not self.mcp_server._requirements_confirmed:
                    # For feature requests, just add a gentle reminder
                    pass  # Allow it to proceed with just a note

            handler = self.mcp_server.tool_handlers.get(name)
            if not handler:
                raise ValueError(f"Unknown tool: {name}")
            # Handlers that multiplex tools accept (name, arguments)
            if hasattr(handler, "handle"):
                try:
                    # Try (name, args) signature first
                    result = await handler.handle(name, arguments)  # type: ignore
                except TypeError:
                    result = await self._call_tool_with_server_logic(tool_name, arguments)  # type: ignore
            else:
                raise ValueError(f"Handler for {name} lacks handle()")

            # Special-case: update gate flag on confirmRequirements
            if name == "confirmRequirements":
                try:
                    # The tool returns a single TextContent JSON payload
                    payload = json.loads(result[0].text) if result and result[0].text else {}
                    self.mcp_server._requirements_confirmed = bool(payload.get("satisfied"))
                except Exception:
                    # Keep gate closed on parse issues
                    self.mcp_server._requirements_confirmed = False

            # If tool returns no citations and is docs-related, append a guard note
            try:
                if name in {"searchDocs", "mastraSpecialist", "getRelevantFeature", "voiceSpecialist", "spellsSpecialist", "contextSpecialist"}:
                    enriched = []
                    for item in result:
                        payload = json.loads(item.text) if item.text else {}
                        if not payload.get("results"):
                            payload["note"] = payload.get("note") or "not in docs"
                        # Add reminder to base answers on documentation
                        if payload.get("results"):
                            payload["INSTRUCTION"] = "BASE YOUR ANSWER ONLY ON THESE DOCUMENTATION RESULTS"
                        enriched.append(types.TextContent(type="text", text=json.dumps(payload, indent=2)))
                    return enriched
            except Exception:
                pass
            return result
        except Exception as exc:
            logger.exception("Tool execution error: %s", exc)
            return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    
    async def oauth_discovery(self, request):
        """OAuth discovery endpoint - indicates no auth required."""
        return web.json_response({
            "issuer": "https://mcpwithcedar-production.up.railway.app",
            "authorization_endpoint": None,
            "token_endpoint": None,
            "userinfo_endpoint": None,
            "registration_endpoint": "https://mcpwithcedar-production.up.railway.app/register",
            "authentication_required": False,
            "grant_types_supported": ["none"],
            "response_types_supported": ["none"],
            "description": "No authentication required - public MCP server"
        })
    
    async def register_handler(self, request):
        """Registration endpoint - auto-approves all registrations."""
        # Generate a dummy client ID for the requester
        client_id = str(uuid.uuid4())
        
        return web.json_response({
            "client_id": client_id,
            "client_secret": "not_required",
            "registration_access_token": "not_required",
            "token_endpoint_auth_method": "none",
            "grant_types": ["none"],
            "response_types": ["none"],
            "description": "Auto-registered client - no authentication required"
        })
    
    async def health_check(self, request):
        """Health check endpoint for Railway."""
        return web.json_response({
            "status": "healthy",
            "service": "Cedar MCP Server",
            "version": "0.3.0",
            "transports": ["http", "websocket", "sse"],
            "url": "https://mcpwithcedar-production.up.railway.app",
            "sse_endpoint": "https://mcpwithcedar-production.up.railway.app/sse",
            "protocol": "MCP 0.1.0",
            "authentication": "none",
            "description": "No authentication required - plug and play MCP server"
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
            
            # Call the tool handler through the server's tool call processing
            # This ensures consistent behavior with stdio server and respects environment variables
            result = await self._call_tool_with_server_logic(tool_name, arguments)
            
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
                        
                        result = await self._call_tool_with_server_logic(tool_name, data.get('arguments', {}))
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
    
    async def jsonrpc_handler(self, request):
        """JSON-RPC handler for Cursor MCP integration."""
        try:
            # Handle GET requests (likely a health check or capabilities query)
            if request.method == 'GET':
                # Return server info for GET requests
                return web.json_response({
                    "jsonrpc": "2.0",
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
            
            data = await request.json()
            
            # Handle different MCP message types
            if data.get('method') == 'initialize':
                return web.json_response({
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
                
                return web.json_response({
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
                    return web.json_response({
                        "jsonrpc": "2.0",
                        "id": data.get('id', 1),
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
                
                result = await self._call_tool_with_server_logic(tool_name, arguments)
                formatted_result = []
                for r in result:
                    if hasattr(r, 'text'):
                        formatted_result.append({"type": "text", "text": r.text})
                    else:
                        formatted_result.append({"type": "text", "text": str(r)})
                
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {"content": formatted_result}
                })
            
            elif data.get('method') == 'resources/list':
                return web.json_response({
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
            
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {data.get('method')}"
                    }
                })
                
        except Exception as e:
            logger.error(f"JSON-RPC handling error: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": 1,  # Default ID since data might not be defined
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            })
    
    async def sse_handler(self, request):
        """SSE handler for Claude Desktop MCP integration."""
        response = StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        
        await response.prepare(request)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        self.sse_sessions[session_id] = {
            'response': response,
            'cwd': request.headers.get('X-CWD', os.getcwd())
        }
        
        logger.info(f"SSE connection established: {session_id}, CWD: {self.sse_sessions[session_id]['cwd']}")
        
        try:
            # Don't send anything initially - wait for client to send initialize request
            # Just keep the connection alive
            await self._handle_sse_stream(request, response, session_id)
                
        except Exception as e:
            if "Cannot write to closing transport" not in str(e):
                logger.error(f"SSE error: {e}", exc_info=True)
        finally:
            # Clean up session
            if session_id in self.sse_sessions:
                del self.sse_sessions[session_id]
                logger.info(f"SSE connection closed: {session_id}")
        
        return response
    
    async def _send_sse_event(self, response, data):
        """Send an SSE event to the client."""
        try:
            # StreamResponse doesn't have transport directly, just try to write
            event_data = f"data: {json.dumps(data)}\n\n"
            await response.write(event_data.encode('utf-8'))
        except ConnectionResetError:
            logger.info("Connection reset while sending SSE event")
            raise
        except Exception as e:
            if "Cannot write to closing transport" not in str(e):
                logger.error(f"Error sending SSE event: {e}")
            raise
    
    async def _handle_sse_post(self, request, response):
        """Handle SSE requests via POST (Claude Desktop style)."""
        try:
            # Read the raw body for debugging
            body = await request.read()
            logger.info(f"SSE POST received: {body[:500]}")  # Log first 500 chars
            
            # Try to parse as JSON
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from SSE POST: {body}")
                data = {}
            
            # Handle different MCP message types
            if data.get('method') == 'initialize':
                result = {
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {
                        "protocolVersion": "0.1.0",
                        "capabilities": {
                            "tools": True,
                            "resources": False,
                            "prompts": False
                        },
                        "serverInfo": {
                            "name": "cedar-mcp",
                            "version": "0.3.0"
                        }
                    }
                }
                logger.info(f"Sending initialize response: {result}")
                await self._send_sse_event(response, result)
            
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
                    result = await self._call_tool_with_server_logic(tool_name, arguments)
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
    
    async def _handle_sse_stream(self, request, response, session_id):
        """Handle SSE stream for keep-alive and periodic updates."""
        try:
            # Wait a bit before starting heartbeats
            await asyncio.sleep(2)
            
            # Send initial comment to establish connection
            await response.write(b": keepalive\n\n")
            
            # Send periodic heartbeat to keep connection alive
            heartbeat_interval = 30  # Send heartbeat every 30 seconds
            while True:
                try:
                    await asyncio.sleep(heartbeat_interval)
                    # Send a comment line as heartbeat (SSE comment format)
                    await response.write(b": heartbeat\n\n")
                except ConnectionResetError:
                    logger.info(f"Connection reset for session {session_id}")
                    break
                except Exception as e:
                    if "Cannot write to closing transport" in str(e):
                        logger.info(f"Client disconnected for session {session_id}")
                    else:
                        logger.error(f"Heartbeat error for session {session_id}: {e}")
                    break
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"SSE stream error for session {session_id}: {e}")
    
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