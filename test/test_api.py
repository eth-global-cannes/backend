#!/usr/bin/env python3
"""
Test script for the Agent Registry & MCP Server
This script demonstrates how to use the API endpoints
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def register_test_agent() -> str:
    """Register a test agent and return the agent ID"""
    print("📝 Registering test agent...")
    
    agent_data = {
        "user_id": "test-user-123",
        "name": "Calculator Agent",
        "description": "A simple calculator agent for testing",
        "webhook_url": "https://httpbin.org/post",  # Test webhook
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
        "pricing": 0.05
    }
    
    response = requests.post(
        f"{BASE_URL}/api/agents/register",
        json=agent_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 201:
        agent_id = result.get("agent_id")
        print(f"✅ Agent registered successfully with ID: {agent_id}")
        return agent_id
    else:
        print("❌ Failed to register agent")
        return None

def list_agents():
    """List all agents"""
    print("📋 Listing all agents...")
    
    response = requests.get(f"{BASE_URL}/api/agents/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Found {result['total']} agents:")
        for agent in result['agents']:
            print(f"  - {agent['name']} (ID: {agent['id']}) - ${agent['pricing']}")
    else:
        print(f"❌ Failed to list agents: {response.text}")
    print()

def get_agent_details(agent_id: str):
    """Get details of a specific agent"""
    print(f"🔍 Getting agent details for ID: {agent_id}")
    
    response = requests.get(f"{BASE_URL}/api/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Agent: {result['name']}")
        print(f"Description: {result['description']}")
        print(f"Pricing: ${result['pricing']}")
        print(f"Tools: {list(result['tool_schema']['tools'].keys())}")
    else:
        print(f"❌ Failed to get agent details: {response.text}")
    print()

def call_tool(agent_id: str) -> str:
    """Call a tool and return the tool call ID"""
    print(f"🔧 Calling tool 'add' on agent {agent_id}...")
    
    tool_call_data = {
        "agent_id": agent_id,
        "caller_user_id": "test-caller-456",
        "tool_name": "add",
        "parameters": {
            "a": 15,
            "b": 25
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/mcp/call-tool",
        json=tool_call_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        tool_call_id = result.get("id")
        print(f"✅ Tool call initiated with ID: {tool_call_id}")
        return tool_call_id
    else:
        print("❌ Failed to call tool")
        return None

def check_tool_call_status(tool_call_id: str):
    """Check the status of a tool call"""
    print(f"📊 Checking tool call status for ID: {tool_call_id}")
    
    # Wait a bit for the background task to process
    time.sleep(2)
    
    response = requests.get(f"{BASE_URL}/api/mcp/tool-call/{tool_call_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Tool Call Status: {result['payment_status']}")
        print(f"Cost: ${result['cost']}")
        if result['result']:
            print(f"Result: {json.dumps(result['result'], indent=2)}")
        if result['completed_at']:
            print(f"Completed at: {result['completed_at']}")
    else:
        print(f"❌ Failed to get tool call status: {response.text}")
    print()

def create_payment(tool_call_id: str):
    """Create a payment for a tool call"""
    print(f"💳 Creating payment for tool call {tool_call_id}...")
    
    payment_data = {
        "tool_call_id": tool_call_id,
        "amount": 0.05,
        "currency": "USD"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/mcp/create-payment",
        json=payment_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        print(f"✅ Payment created with checkout ID: {result['coinbase_checkout_id']}")
    else:
        print("❌ Failed to create payment")
    print()

def main():
    """Run all tests"""
    print("🚀 Starting API tests...\n")
    
    # Test health
    test_health()
    
    # Register an agent
    agent_id = register_test_agent()
    if not agent_id:
        print("❌ Cannot continue without agent ID")
        return
    
    print()
    
    # List agents
    list_agents()
    
    # Get agent details
    get_agent_details(agent_id)
    
    # Call a tool
    tool_call_id = call_tool(agent_id)
    if not tool_call_id:
        print("❌ Cannot continue without tool call ID")
        return
    
    print()
    
    # Check tool call status
    check_tool_call_status(tool_call_id)
    
    # Create payment
    create_payment(tool_call_id)
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}") 