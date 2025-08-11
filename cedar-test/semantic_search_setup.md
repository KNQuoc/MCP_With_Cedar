# Semantic Search Setup for Cedar MCP Server

## Overview
The searchDocs tool has been upgraded to support semantic search using vector similarity from your Supabase database containing pre-vectorized document chunks.

## Configuration

### Environment Variables
Set the following environment variables to enable semantic search:

```bash
export SUPABASE_URL="your-supabase-project-url"
export SUPABASE_KEY="your-supabase-anon-key"
```

### Database Schema
The implementation expects a table named `browser_agent_nodes` with the following structure:
- `content`: Text content of the document chunk
- `metadata`: JSONB field containing at least:
  - `product_id`: Product identifier (default: `b0cd564c-50e0-4cf5-812a-5d11c1fa63c8`)
  - `heading`: Optional section heading
- `source`: Optional source file reference
- `id`: Document chunk identifier

## Usage

### Using the searchDocs Tool
The searchDocs tool automatically uses semantic search when Supabase credentials are configured:

```json
{
  "tool": "searchDocs",
  "arguments": {
    "query": "your search query",
    "limit": 5,
    "use_semantic": true  // Optional, defaults to true
  }
}
```

### Parameters
- `query`: Search query text
- `limit`: Maximum number of results (default: 5)
- `use_semantic`: Enable/disable semantic search (default: true)

## Fallback Behavior
If semantic search is not available (missing credentials or connection failure), the system automatically falls back to keyword-based search.

## Required Supabase Function (Optional)
For optimal performance, create a Supabase RPC function named `search_similar_docs`:

```sql
CREATE OR REPLACE FUNCTION search_similar_docs(
  query_text TEXT,
  product_filter TEXT,
  result_limit INT
)
RETURNS TABLE (
  id TEXT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT,
  source TEXT
) AS $$
BEGIN
  -- Your vector similarity search implementation
  -- This should use the pre-computed vectors in your database
END;
$$ LANGUAGE plpgsql;
```

If this function doesn't exist, the system will use a direct query fallback with basic text matching.

## Testing
To test semantic search:

1. Ensure environment variables are set
2. Run the MCP server
3. Use the searchDocs tool with various queries
4. Check logs for "Semantic search enabled" confirmation

## Notes
- No OpenAI API key is required since vectors are pre-computed in Supabase
- The system seamlessly falls back to keyword search if semantic search fails
- Results include similarity scores when using semantic search