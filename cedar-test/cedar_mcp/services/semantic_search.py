import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from supabase import create_client, Client
from openai import OpenAI

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_PRODUCT_ID = "b0cd564c-50e0-4cf5-812a-5d11c1fa63c8"
EMBEDDING_DIMENSION = 512  # OpenAI text-embedding-3-small with custom dimensions
DEFAULT_TABLE_NAME = "browser_agent_nodes"


@dataclass
class SemanticSearchResult:
    content: str
    metadata: Dict[str, Any]
    similarity: float
    source: Optional[str] = None
    id: Optional[str] = None


class SemanticSearchService:
    """Semantic search service using Supabase vector database with OpenAI embeddings."""
    
    def __init__(
        self, 
        supabase_url: Optional[str] = None, 
        supabase_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided or set in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for semantic search")
        else:
            logger.warning("OpenAI API key not found. Semantic search will fall back to keyword search.")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI text-embedding-3-small model."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Please provide OPENAI_API_KEY.")
        
        try:
            # Use text-embedding-3-small with custom dimensions to match your database
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small",
                dimensions=EMBEDDING_DIMENSION
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def search_by_vector(
        self, 
        query: str, 
        table_name: str = DEFAULT_TABLE_NAME,
        product_id: str = DEFAULT_PRODUCT_ID,
        limit: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search using vector similarity with OpenAI embeddings.
        
        Args:
            query: The search query text
            table_name: Supabase table name
            product_id: Product ID to filter by
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score threshold
        
        Returns:
            List of semantic search results sorted by similarity
        """
        try:
            # Check if OpenAI is available
            if not self.openai_client:
                logger.debug("OpenAI not available, falling back to keyword search")
                return await self._direct_search(query, table_name, product_id, limit)
            
            # Generate embedding for the query using OpenAI
            query_embedding = self._get_embedding(query)
            
            # Call the Supabase function we created
            response = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit,
                    'product_filter': product_id
                }
            ).execute()
            
            if response.data:
                results = []
                for item in response.data:
                    metadata = item.get('metadata', {})
                    result = SemanticSearchResult(
                        content=item.get('content', ''),
                        metadata=metadata,
                        similarity=item.get('similarity', 0.0),
                        source=metadata.get('source_label'),
                        id=item.get('id')
                    )
                    results.append(result)
                return results
            
            return []
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Fall back to direct search if semantic search fails
            return await self._direct_search(query, table_name, product_id, limit)
    
    async def _direct_search(
        self,
        query: str,
        table_name: str,
        product_id: str,
        limit: int
    ) -> List[SemanticSearchResult]:
        """
        Direct search using Supabase query filters.
        This is a fallback if vector similarity search is not available.
        """
        try:
            # Query documents filtered by product_id
            response = self.supabase.table(table_name).select("*").eq(
                "metadata->>product_id", product_id
            ).limit(limit * 3).execute()  # Get more results for better filtering
            
            if not response.data:
                return []
            
            # Convert to SemanticSearchResult objects
            results = []
            query_lower = query.lower()
            query_terms = query_lower.split()
            
            for item in response.data:
                # Get text content from metadata (based on your schema)
                metadata = item.get('metadata', {})
                text_content = metadata.get('text', '')
                
                # If no text in metadata, try other fields
                if not text_content:
                    text_content = item.get('text', '') or item.get('content', '')
                
                # Basic relevance scoring based on query term presence
                content_lower = text_content.lower()
                matches = sum(1 for term in query_terms if term in content_lower)
                relevance = matches / len(query_terms) if query_terms else 0
                
                # Boost score if query terms appear in headers or section_title
                headers = metadata.get('headers', [])
                section_title = metadata.get('section_title', '')
                
                if headers:
                    header_text = ' '.join(headers).lower()
                    header_matches = sum(1 for term in query_terms if term in header_text)
                    relevance += (header_matches / len(query_terms)) * 0.5 if query_terms else 0
                
                if section_title:
                    title_lower = section_title.lower()
                    title_matches = sum(1 for term in query_terms if term in title_lower)
                    relevance += (title_matches / len(query_terms)) * 0.5 if query_terms else 0
                
                result = SemanticSearchResult(
                    content=text_content,
                    metadata=metadata,
                    similarity=relevance,
                    source=metadata.get('source_label') or metadata.get('url'),
                    id=item.get('id')
                )
                results.append(result)
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in direct search: {e}")
            return []
    
    async def search_with_metadata_filters(
        self,
        query: str,
        metadata_filters: Dict[str, Any],
        table_name: str = DEFAULT_TABLE_NAME,
        limit: int = 5
    ) -> List[SemanticSearchResult]:
        """
        Search with additional metadata filters.
        
        Args:
            query: Search query
            metadata_filters: Dictionary of metadata field filters
            table_name: Supabase table name
            limit: Maximum number of results
        
        Returns:
            Filtered semantic search results
        """
        try:
            # Build the query with metadata filters
            query_builder = self.supabase.table(table_name).select("*")
            
            # Apply metadata filters
            for key, value in metadata_filters.items():
                query_builder = query_builder.eq(f"metadata->>{key}", value)
            
            response = query_builder.limit(limit).execute()
            
            if not response.data:
                return []
            
            # Convert to results with basic text matching
            results = []
            query_lower = query.lower()
            query_terms = query_lower.split()
            
            for item in response.data:
                metadata = item.get('metadata', {})
                content = metadata.get('text', '')
                
                if not content:
                    content = item.get('text', '') or item.get('content', '')
                
                # Calculate basic relevance
                content_lower = content.lower()
                matches = sum(1 for term in query_terms if term in content_lower)
                relevance = matches / len(query_terms) if query_terms else 0
                
                result = SemanticSearchResult(
                    content=content,
                    metadata=metadata,
                    similarity=relevance,
                    source=metadata.get('source_label') or metadata.get('url'),
                    id=item.get('id')
                )
                results.append(result)
            
            # Sort by relevance
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error in metadata filtered search: {e}")
            return []