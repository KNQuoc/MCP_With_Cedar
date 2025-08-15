# Railway Deployment Guide for Cedar MCP Server

## Overview

The Cedar MCP Server is designed as a stdio-based service (communicates via standard input/output). To deploy it on Railway (which expects HTTP services), we've added a web wrapper that exposes the MCP functionality via HTTP and WebSocket endpoints.

## Files Created for Railway Deployment

1. **`cedar_mcp/web_server.py`** - Web wrapper that exposes MCP via HTTP/WebSocket
2. **`railway.json`** - Railway configuration file
3. **`Procfile`** - Backup deployment configuration
4. **`.env.example`** - Environment variable template
5. **Updated `requirements.txt`** - Added missing dependencies

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Deploy on Railway

1. Go to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Python project

### 3. Configure Environment Variables

In Railway dashboard, add these environment variables:

**Required:**
```
CEDAR_LOG_LEVEL=INFO
CEDAR_MCP_SIMPLIFIED_OUTPUT=true
```

**Optional (for semantic search):**
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
```

**Optional (for custom docs):**
```
CEDAR_DOCS_PATH=/path/to/cedar_docs
MASTRA_DOCS_PATH=/path/to/mastra_docs
```

### 4. Verify Deployment

Once deployed, Railway will provide a URL like `https://your-app.up.railway.app`

Test the endpoints:
- Health check: `GET https://your-app.up.railway.app/health`
- List tools: `GET https://your-app.up.railway.app/tools`
- Execute tool: `POST https://your-app.up.railway.app/tool`

## API Endpoints

### Health Check
```bash
curl https://your-app.up.railway.app/health
```

### List Available Tools
```bash
curl https://your-app.up.railway.app/tools
```

### Execute a Tool
```bash
curl -X POST https://your-app.up.railway.app/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "searchDocs",
    "arguments": {
      "query": "voice setup",
      "limit": 5
    }
  }'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('wss://your-app.up.railway.app/ws');

ws.send(JSON.stringify({
  type: 'tool_call',
  tool: 'searchDocs',
  arguments: { query: 'voice setup' }
}));
```

## Important Notes

1. **MCP Protocol**: The original MCP server uses stdio protocol. The web wrapper translates HTTP/WebSocket requests to MCP calls.

2. **Authentication**: Currently no authentication is implemented. Add authentication middleware if needed for production.

3. **CORS**: CORS is enabled for all origins. Restrict in production if needed.

4. **Port**: Railway automatically sets the PORT environment variable. The server listens on this port.

## Troubleshooting

### Server won't start
- Check logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility (requires 3.10+)

### Tools not working
- Check environment variables are set correctly
- Verify documentation files are accessible
- Check server logs for specific errors

### Memory issues
- The server loads documentation into memory at startup
- Consider using smaller documentation files or implementing lazy loading

## Alternative Deployment Options

If you don't need HTTP access and just want to run the MCP server:

1. **Container Service**: Deploy as a container that communicates via stdio
2. **Background Worker**: Run as a background job (not web-accessible)
3. **Local Development**: Keep it local and use with Claude Desktop/Cursor

## Security Considerations

1. **Add Authentication**: Implement API key or JWT authentication
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Already implemented via Pydantic schemas
4. **HTTPS Only**: Railway provides HTTPS by default
5. **Environment Variables**: Never commit secrets, use Railway's env vars

## Support

For issues with:
- MCP Server: Check the main README.md
- Railway Deployment: Check Railway documentation
- Web Wrapper: See `cedar_mcp/web_server.py` implementation