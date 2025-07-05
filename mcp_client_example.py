#!/usr/bin/env python3
"""
MCP Client Example

This demonstrates how to use the MCP server with proper authentication
and JSON-RPC 2.0 protocol.
"""

import requests
import json
import uuid
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self, server_url: str, token: str):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool using JSON-RPC 2.0 protocol
        """
        request_id = str(uuid.uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params,
            "id": request_id
        }
        
        try:
            response = self.session.post(self.server_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "id": result.get("id")
                }
            else:
                return {
                    "success": True,
                    "result": result.get("result"),
                    "id": result.get("id")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON response: {str(e)}"
            }

def demo_mcp_client():
    """
    Demonstrate MCP client usage
    """
    print("🔧 MCP Client Demo")
    print("=" * 40)
    
    # You'll need to get a token first from the token API
    # This is a placeholder - replace with an actual token
    token = "your-token-here"
    mcp_server_url = "http://localhost:8080"
    
    client = MCPClient(mcp_server_url, token)
    
    # Example tool calls
    test_cases = [
        {
            "name": "Addition",
            "tool": "add",
            "params": {"a": 10, "b": 20}
        },
        {
            "name": "Multiplication",
            "tool": "multiply",
            "params": {"x": 7, "y": 8}
        },
        {
            "name": "Division",
            "tool": "divide",
            "params": {"a": 100, "b": 5}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing {test_case['name']}:")
        print(f"   Tool: {test_case['tool']}")
        print(f"   Params: {test_case['params']}")
        
        result = client.call_tool(test_case['tool'], test_case['params'])
        
        if result['success']:
            print(f"   ✅ Result: {result['result']}")
        else:
            print(f"   ❌ Error: {result['error']}")

def create_test_token(agent_id: str, user_id: str) -> Optional[str]:
    """
    Create a test token for the demo
    """
    token_api_url = "http://localhost:8000/api/tokens/create"
    
    payload = {
        "agent_id": agent_id,
        "user_id": user_id,
        "expires_in_days": 7
    }
    
    try:
        response = requests.post(token_api_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("token")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create token: {e}")
        return None

def full_demo():
    """
    Complete demo including token creation
    """
    print("🚀 Complete MCP Demo")
    print("=" * 50)
    
    # First, you need to register an agent and get its ID
    # This is a placeholder - replace with actual agent ID
    agent_id = "your-agent-id-here"
    user_id = "demo-user-123"
    
    print("📝 Creating access token...")
    token = create_test_token(agent_id, user_id)
    
    if not token:
        print("❌ Could not create token. Make sure:")
        print("   1. Agent Registry server is running on localhost:8000")
        print("   2. You have a registered agent")
        print("   3. Replace 'your-agent-id-here' with actual agent ID")
        return
    
    print(f"✅ Token created: {token[:16]}...")
    
    # Now use the MCP client
    print("\n🔧 Using MCP Client...")
    mcp_server_url = "http://localhost:8080"
    
    client = MCPClient(mcp_server_url, token)
    
    # Test the client
    result = client.call_tool("add", {"a": 15, "b": 25})
    
    if result['success']:
        print(f"✅ MCP Call successful: {result['result']}")
    else:
        print(f"❌ MCP Call failed: {result['error']}")

def curl_examples():
    """
    Show curl examples for MCP calls
    """
    print("\n📚 cURL Examples for MCP Server:")
    print("=" * 40)
    
    examples = [
        {
            "name": "Add two numbers",
            "curl": """curl -X POST http://localhost:8080/ \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "add",
    "params": {"a": 10, "b": 20},
    "id": "test-123"
  }'"""
        },
        {
            "name": "Multiply two numbers",
            "curl": """curl -X POST http://localhost:8080/ \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "multiply",
    "params": {"x": 7, "y": 8},
    "id": "test-456"
  }'"""
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print(example['curl'])

if __name__ == "__main__":
    print("Select an option:")
    print("1. Simple MCP Client Demo (requires token)")
    print("2. Full Demo (creates token and calls MCP)")
    print("3. Show cURL Examples")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        demo_mcp_client()
    elif choice == "2":
        full_demo()
    elif choice == "3":
        curl_examples()
    else:
        print("Invalid choice. Showing cURL examples...")
        curl_examples() 