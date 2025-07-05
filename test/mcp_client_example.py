#!/usr/bin/env python3
"""
MCP Client Example for FastMCP Server

This demonstrates how to interact with the FastMCP server to:
1. Use resources (GET-like operations)
2. Use tools (POST-like operations)
"""

import json
import requests
from typing import Dict, Any

class MCPClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    # RESOURCES (GET-like operations)
    
    def get_agent_list(self) -> Dict[str, Any]:
        """Get list of all agents"""
        try:
            # This would be an MCP resource call in a real MCP client
            # For now, using the FastAPI endpoint
            response = self.session.get(f"{self.server_url}/api/agents/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get details of a specific agent"""
        try:
            response = self.session.get(f"{self.server_url}/api/agents/{agent_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_tool_call_status(self, tool_call_id: str) -> Dict[str, Any]:
        """Get status of a tool call"""
        try:
            response = self.session.get(f"{self.server_url}/api/tokens/tool-call/{tool_call_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # TOOLS (POST-like operations - these would use the MCP server)
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent"""
        try:
            response = self.session.post(f"{self.server_url}/api/agents/register", json=agent_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_token(self, agent_id: str, user_id: str, expires_in_days: int = 30) -> Dict[str, Any]:
        """Create an access token for an agent"""
        try:
            token_data = {
                "agent_id": agent_id,
                "user_id": user_id,
                "expires_in_days": expires_in_days
            }
            response = self.session.post(f"{self.server_url}/api/tokens/create", json=token_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def demo_mcp_workflow():
    """Demonstrate a complete MCP workflow"""
    print("🚀 MCP Client Demo - FastMCP Server Integration")
    print("=" * 60)
    
    client = MCPClient()
    
    # Step 1: Register an agent
    print("\n📝 Step 1: Registering an agent...")
    agent_data = {
        "user_id": "demo-user-123",
        "name": "Demo Calculator Agent",
        "description": "A calculator agent for MCP demo",
        "webhook_url": "http://localhost:8001/webhook",
        "tool_schema": {
            "tools": {
                "add": {
                    "description": "Add two numbers",
                    "parameters": {
                        "a": "number",
                        "b": "number"
                    }
                },
                "multiply": {
                    "description": "Multiply two numbers",
                    "parameters": {
                        "x": "number",
                        "y": "number"
                    }
                }
            }
        },
        "pricing": 0.02
    }
    
    agent_result = client.register_agent(agent_data)
    if "error" in agent_result:
        print(f"❌ Failed to register agent: {agent_result['error']}")
        return
    
    agent_id = agent_result.get("agent_id")
    if not agent_id:
        print("❌ Agent registration failed - no agent ID returned")
        return
    
    print(f"✅ Agent registered with ID: {agent_id}")
    
    # Step 2: List all agents
    print("\n📋 Step 2: Listing all agents...")
    agents = client.get_agent_list()
    if "error" in agents:
        print(f"❌ Failed to list agents: {agents['error']}")
    else:
        print(f"✅ Found {agents.get('total', 0)} agents")
        for agent in agents.get('agents', []):
            print(f"   - {agent['name']} (ID: {agent['id'][:8]}...)")
    
    # Step 3: Get agent details
    print(f"\n🔍 Step 3: Getting details for agent {agent_id[:8]}...")
    agent_details = client.get_agent_details(agent_id)
    if "error" in agent_details:
        print(f"❌ Failed to get agent details: {agent_details['error']}")
    else:
        print(f"✅ Agent: {agent_details['name']}")
        print(f"   Tools: {list(agent_details['tool_schema']['tools'].keys())}")
        print(f"   Pricing: ${agent_details['pricing']}")
    
    # Step 4: Create access token
    print(f"\n🔐 Step 4: Creating access token...")
    token_result = client.create_token(agent_id, "demo-caller-456", 7)
    if "error" in token_result:
        print(f"❌ Failed to create token: {token_result['error']}")
        return
    
    access_token = token_result.get("token")
    if not access_token:
        print("❌ Token creation failed - no token returned")
        return
    
    print(f"✅ Access token created: {access_token[:16]}...")
    
    print("\n🎉 Demo completed successfully!")
    print(f"Agent ID: {agent_id}")
    print(f"Access Token: {access_token[:16]}...")
    print("\nNext steps:")
    print("1. Start the MCP server: python server.py")
    print("2. Use the FastMCP resources and tools")
    print("3. Call agent tools via the MCP server")

def show_mcp_usage_examples():
    """Show examples of how to use MCP resources and tools"""
    print("\n📚 MCP Server Usage Examples")
    print("=" * 40)
    
    print("\n🔗 RESOURCES (GET-like operations):")
    resources = [
        ("agent://list", "List all agents"),
        ("agent://get/{agent_id}", "Get specific agent details"),
        ("tool_call://status/{tool_call_id}", "Get tool call status"),
        ("payment://get_status/{identifier}", "Get payment status"),
        ("user://tokens/{user_id}", "Get user tokens")
    ]
    
    for resource, description in resources:
        print(f"   📄 {resource}")
        print(f"      {description}")
    
    print("\n🛠️ TOOLS (POST-like operations):")
    tools = [
        ("agent_call_tool", "Call a tool on an agent"),
        ("payment_create", "Create a payment for tool call"),
        ("tool_call_poll", "Poll tool call completion"),
        ("tool_call_finalize", "Finalize off-chain tool call")
    ]
    
    for tool, description in tools:
        print(f"   🔧 {tool}")
        print(f"      {description}")
    
    print("\n💡 Example tool call:")
    print("""
    # Using FastMCP client (pseudo-code)
    result = mcp_client.call_tool(
        'agent_call_tool',
        {
            'agent_id': 'your-agent-id',
            'tool_name': 'add',
            'parameters': {'a': 10, 'b': 20},
            'caller_user_id': 'user123'
        }
    )
    """)

def main():
    """Main function"""
    print("Select an option:")
    print("1. Run complete MCP workflow demo")
    print("2. Show MCP usage examples")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        demo_mcp_workflow()
    elif choice == "2":
        show_mcp_usage_examples()
    elif choice == "3":
        demo_mcp_workflow()
        show_mcp_usage_examples()
    else:
        print("Invalid choice. Running workflow demo...")
        demo_mcp_workflow()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}") 