-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Create function for semantic search on browser_agent_nodes
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(512),  -- Adjust dimension if your embeddings are different size
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 10,
  product_filter text DEFAULT NULL
)
RETURNS TABLE (
  id text,
  vector_id text,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ban.id::text,  -- Cast to text if id is integer
    ban.vector_id::text,  -- Cast to text if needed
    ban.metadata->>'text' as content,
    ban.metadata,
    1 - (ban.embedding <=> query_embedding)::float as similarity
  FROM browser_agent_nodes ban
  WHERE 
    -- Apply product filter if provided
    (product_filter IS NULL OR ban.metadata->>'product_id' = product_filter)
    -- Apply similarity threshold
    AND ban.embedding <=> query_embedding < 1 - match_threshold
  ORDER BY ban.embedding <=> query_embedding ASC
  LIMIT least(match_count, 200);
END;
$$;

-- Alternative version using negative inner product for better performance with normalized vectors
CREATE OR REPLACE FUNCTION match_documents_fast (
  query_embedding vector(512),  -- Adjust dimension if your embeddings are different size
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 10,
  product_filter text DEFAULT NULL
)
RETURNS TABLE (
  id text,
  vector_id text,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ban.id::text,  -- Cast to text if id is integer
    ban.vector_id::text,  -- Cast to text if needed
    ban.metadata->>'text' as content,
    ban.metadata,
    -(ban.embedding <#> query_embedding)::float as similarity  -- Negative inner product
  FROM browser_agent_nodes ban
  WHERE 
    -- Apply product filter if provided
    (product_filter IS NULL OR ban.metadata->>'product_id' = product_filter)
    -- Apply similarity threshold (note the negative for inner product)
    AND ban.embedding <#> query_embedding < -match_threshold
  ORDER BY ban.embedding <#> query_embedding ASC
  LIMIT least(match_count, 200);
END;
$$;

-- Create an index for better performance
CREATE INDEX IF NOT EXISTS browser_agent_nodes_embedding_idx 
ON browser_agent_nodes 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Optional: Create index for inner product if using the fast version
CREATE INDEX IF NOT EXISTS browser_agent_nodes_embedding_ip_idx 
ON browser_agent_nodes 
USING ivfflat (embedding vector_ip_ops)
WITH (lists = 100);