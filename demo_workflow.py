#!/usr/bin/env python3
"""
Complete Workflow Demonstration

This script demonstrates the complete workflow:
1. Register an agent with real webhook
2. Call the agent's tools
3. Process payments
4. Show the results

Make sure to run example_agent_webhook.py first on port 8001
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"
WEBHOOK_URL = "http://localhost:8001/webhook"
MCP_SERVER_URL = "http://localhost:8080"

class AgentDemo:
    def __init__(self):
        self.agent_id = None
        self.access_token = None
        self.payment_id = None
    
    def check_webhook_server(self):
        """Check if the webhook server is running"""
        try:
            response = requests.get("http://localhost:8001/health")
            if response.status_code == 200:
                print("✅ Webhook server is running")
                return True
            else:
                print("❌ Webhook server is not responding correctly")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Webhook server is not running")
            print("Please start the webhook server first:")
            print("  python example_agent_webhook.py")
            return False
    
    def check_mcp_server(self):
        """Check if the MCP server is running"""
        try:
            response = requests.get(f"{MCP_SERVER_URL}/health")
            if response.status_code == 200:
                print("✅ MCP server is running")
                return True
            else:
                print("❌ MCP server is not responding correctly")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ MCP server is not running")
            print("Please start the MCP server first:")
            print("  python mcp_server.py")
            return False
    
    def register_agent(self):
        """Register an agent with webhook"""
        print("🚀 Registering agent with webhook...")
        
        agent_data = {
            "user_id": "demo-user-123",
            "name": "Demo Calculator Agent",
            "description": "A calculator agent with webhook integration",
            "webhook_url": WEBHOOK_URL,
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
                    },
                    "subtract": {
                        "description": "Subtract two numbers",
                        "parameters": {
                            "a": "number",
                            "b": "number"
                        }
                    },
                    "divide": {
                        "description": "Divide two numbers",
                        "parameters": {
                            "a": "number",
                            "b": "number"
                        }
                    }
                }
            },
            "pricing": 0.02
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/agents/register",
                json=agent_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                self.agent_id = result["agent_id"]
                print(f"✅ Agent registered successfully!")
                print(f"   Agent ID: {self.agent_id}")
                print(f"   Pricing: ${agent_data['pricing']} per call")
                return True
            else:
                print(f"❌ Failed to register agent: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error registering agent: {e}")
            return False
    
    def create_access_token(self):
        """Create an access token for the agent"""
        if not self.agent_id:
            print("❌ No agent registered")
            return False
        
        print("🔐 Creating access token...")
        
        token_data = {
            "agent_id": self.agent_id,
            "user_id": "demo-caller-456",
            "expires_in_days": 7
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/tokens/create",
                json=token_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["token"]
                print(f"✅ Access token created!")
                print(f"   Token: {self.access_token[:16]}...")
                return True
            else:
                print(f"❌ Failed to create token: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating token: {e}")
            return False

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Call a tool via MCP server"""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        print(f"🔧 Calling tool '{tool_name}' via MCP server with parameters: {parameters}")
        
        # JSON-RPC 2.0 request
        request_id = str(uuid.uuid4())
        mcp_request = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": parameters,
            "id": request_id
        }
        
        try:
            response = requests.post(
                "http://localhost:8080/",
                json=mcp_request,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "error" in result:
                    print(f"❌ MCP Error: {result['error']}")
                    return False
                else:
                    print(f"✅ Tool call successful!")
                    print(f"   Result: {result.get('result')}")
                    return True
            else:
                print(f"❌ Failed to call tool: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return False
    

    
    def run_demo(self):
        """Run the complete demo workflow"""
        print("🎬 Agent Registry & MCP Server - Complete Demo")
        print("=" * 50)
        
        # Check webhook server
        if not self.check_webhook_server():
            return
        
        print()
        
        # Check MCP server
        if not self.check_mcp_server():
            return
        
        print()
        
        # Register agent
        if not self.register_agent():
            return
        
        print()
        
        # Create access token
        if not self.create_access_token():
            return
        
        print()
        
        # Demonstrate different tool calls
        test_cases = [
            {
                "name": "Addition",
                "tool": "add",
                "params": {"a": 15, "b": 27}
            },
            {
                "name": "Multiplication",
                "tool": "multiply",
                "params": {"x": 8, "y": 6}
            },
            {
                "name": "Division",
                "tool": "divide",
                "params": {"a": 100, "b": 4}
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            
            # Call tool via MCP
            self.call_tool(test_case["tool"], test_case["params"])
            
            # Small delay between calls
            time.sleep(1)
        
        print("\n🎉 Demo completed successfully!")
        print(f"Agent ID: {self.agent_id}")
        print(f"Access Token: {self.access_token[:16]}...")
        print("\nYou can now:")
        print("1. Visit http://localhost:8000/docs to explore the Agent Registry API")
        print("2. Use the MCP server at http://localhost:8080 for tool calls")
        print("3. Check the webhook server logs for tool execution details")
        print("4. Use the MCP client example: python mcp_client_example.py")

def main():
    """Main function"""
    demo = AgentDemo()
    
    try:
        demo.run_demo()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the main server is running on http://localhost:8000")
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    main() 