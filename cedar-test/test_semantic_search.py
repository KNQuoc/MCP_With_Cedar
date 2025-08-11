#!/usr/bin/env python3
"""
Test script for semantic search functionality in Cedar MCP Server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the cedar_mcp module to path
sys.path.insert(0, str(Path(__file__).parent))

from cedar_mcp.services.semantic_search import SemanticSearchService
from cedar_mcp.services.docs import DocsIndex


async def test_semantic_search():
    """Test the semantic search service directly."""
    print("Testing Semantic Search Service...")
    print("-" * 50)
    
    # Check for required environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ SUPABASE_URL and SUPABASE_KEY environment variables are required")
        print("Please set them before running this test")
        return
    
    try:
        # Initialize semantic search service
        semantic_service = SemanticSearchService()
        print("✅ Semantic search service initialized successfully")
        
        # Test queries
        test_queries = [
            "chat components",
            "agentic state management",
            "streaming responses",
            "Cedar-OS features"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            results = await semantic_service.search_by_vector(
                query=query,
                limit=3
            )
            
            if results:
                print(f"  Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Similarity: {result.similarity:.3f}")
                    print(f"     Content preview: {result.content[:100]}...")
                    if result.metadata:
                        print(f"     Metadata: {list(result.metadata.keys())}")
            else:
                print("  No results found")
                
    except Exception as e:
        print(f"❌ Error during semantic search test: {e}")


async def test_docs_index_with_semantic():
    """Test the DocsIndex with semantic search enabled."""
    print("\n\nTesting DocsIndex with Semantic Search...")
    print("-" * 50)
    
    try:
        # Initialize DocsIndex with semantic search
        docs_index = DocsIndex(
            docs_path="docs/cedar_llms_full.txt",
            enable_semantic_search=True
        )
        
        if docs_index.semantic_search:
            print("✅ DocsIndex initialized with semantic search")
        else:
            print("⚠️  DocsIndex initialized but semantic search not available")
        
        # Test search
        query = "Cedar chat components"
        print(f"\n🔍 Searching for: '{query}'")
        
        results = await docs_index.search(query, limit=3, use_semantic=True)
        
        if results:
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Source: {result.get('source', 'unknown')}")
                if 'similarity' in result:
                    print(f"     Similarity: {result['similarity']:.3f}")
                elif 'matchCount' in result:
                    print(f"     Match count: {result['matchCount']}")
                print(f"     Content preview: {result['content'][:100]}...")
        else:
            print("  No results found")
            
    except Exception as e:
        print(f"❌ Error during DocsIndex test: {e}")


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Cedar MCP Semantic Search Test Suite")
    print("=" * 50)
    
    # Test semantic search service
    await test_semantic_search()
    
    # Test DocsIndex integration
    await test_docs_index_with_semantic()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())