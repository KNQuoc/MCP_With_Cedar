#!/usr/bin/env python3
"""
Test script for Cedar MCP Web Server
Run this after deploying to Railway to test the endpoints.
"""

import requests
import json
import sys

def test_server(base_url):
    """Test the web server endpoints."""
    
    print(f"Testing Cedar MCP Web Server at: {base_url}\n")
    
    # Test 1: Health Check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✅ Health check passed\n")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}\n")
        return False
    
    # Test 2: List Tools
    print("2. Testing list tools...")
    try:
        response = requests.get(f"{base_url}/tools")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Found {len(data.get('tools', []))} tools:")
        for tool in data.get('tools', [])[:5]:  # Show first 5 tools
            print(f"   - {tool['name']}")
        print("   ✅ List tools passed\n")
    except Exception as e:
        print(f"   ❌ List tools failed: {e}\n")
        return False
    
    # Test 3: Execute Tool (searchDocs)
    print("3. Testing tool execution (searchDocs)...")
    try:
        payload = {
            "tool": "searchDocs",
            "arguments": {
                "query": "voice setup",
                "limit": 3
            }
        }
        response = requests.post(
            f"{base_url}/tool",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        print(f"   Status: {response.status_code}")
        if data.get('success'):
            print(f"   ✅ Tool executed successfully")
            print(f"   Results: {len(data.get('result', []))} items returned")
        else:
            print(f"   ❌ Tool execution failed: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ Tool execution failed: {e}\n")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    # Default to localhost for local testing
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Remove trailing slash if present
    url = url.rstrip('/')
    
    success = test_server(url)
    sys.exit(0 if success else 1)