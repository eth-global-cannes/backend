#!/usr/bin/env python3
"""
MCP Server using FastMCP

This implements a proper MCP server with resources (GET-like) and tools (POST-like)
for agent management, tool calls, and payments.
"""

import uuid
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

from database import SessionLocal, Agent, ToolCall, Payment, Token

# Create MCP server
mcp = FastMCP("Agent Registry MCP Server")

# Helper function to get database session
def get_db():
    return SessionLocal()

# RESOURCES (GET-like endpoints)

@mcp.resource("agent://list")
def agent_list() -> str:
    """Return a list of all registered agents and metadata"""
    db = get_db()
    try:
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        agent_list = []
        for agent in agents:
            agent_data = {
                "id": agent.id,
                "name": agent.name,
                "imageUrl": agent.imageUrl,
                "price": agent.price,
                "apiKey": agent.apiKey,
                "webhookUrl": agent.webhookUrl,
                "toolCallsExampleJson": agent.toolCallsExampleJson,
                "agentOwner": agent.agentOwner,
                "is_active": agent.is_active,
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat()
            }
            agent_list.append(agent_data)
        
        return json.dumps({
            "agents": agent_list,
            "total": len(agent_list),
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)
        
    finally:
        db.close()

@mcp.resource("agent://get/{agent_id}")
def agent_get(agent_id: str) -> str:
    """Return details and schema of a specific agent"""
    db = get_db()
    try:
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.is_active == True
        ).first()
        
        if not agent:
            return json.dumps({"error": "Agent not found"})
        
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "imageUrl": agent.imageUrl,
            "price": agent.price,
            "apiKey": agent.apiKey,
            "webhookUrl": agent.webhookUrl,
            "toolCallsExampleJson": agent.toolCallsExampleJson,
            "agentOwner": agent.agentOwner,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        }
        
        return json.dumps(agent_data, indent=2)
        
    finally:
        db.close()

@mcp.resource("tool_call://status/{tool_call_id}")
def tool_call_status(tool_call_id: str) -> str:
    """Return the status of a tool call"""
    db = get_db()
    try:
        tool_call = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
        
        if not tool_call:
            return json.dumps({"error": "Tool call not found"})
        
        status_data = {
            "id": tool_call.id,
            "agent_id": tool_call.agent_id,
            "caller_user_id": tool_call.caller_user_id,
            "tool_name": tool_call.tool_name,
            "parameters": tool_call.parameters,
            "result": tool_call.result,
            "cost": tool_call.cost,
            "payment_status": tool_call.payment_status,
            "created_at": tool_call.created_at.isoformat(),
            "completed_at": tool_call.completed_at.isoformat() if tool_call.completed_at is not None else None,
            "status": "completed" if tool_call.completed_at is not None else "pending"
        }
        
        return json.dumps(status_data, indent=2)
        
    finally:
        db.close()

@mcp.resource("payment://get_status/{identifier}")
def payment_get_status(identifier: str) -> str:
    """Return status of a payment given tool_call_id or checkout_id"""
    db = get_db()
    try:
        # Try to find by tool_call_id first, then by checkout_id
        payment = db.query(Payment).filter(
            (Payment.tool_call_id == identifier) | 
            (Payment.coinbase_checkout_id == identifier)
        ).first()
        
        if not payment:
            return json.dumps({"error": "Payment not found"})
        
        payment_data = {
            "id": payment.id,
            "tool_call_id": payment.tool_call_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "coinbase_checkout_id": payment.coinbase_checkout_id,
            "status": payment.status,
            "created_at": payment.created_at.isoformat(),
            "completed_at": payment.completed_at.isoformat() if payment.completed_at is not None else None
        }
        
        return json.dumps(payment_data, indent=2)
        
    finally:
        db.close()

@mcp.resource("user://tokens/{user_id}")
def user_tokens(user_id: str) -> str:
    """Return tokens owned by a user"""
    db = get_db()
    try:
        tokens = db.query(Token).filter(
            Token.user_id == user_id,
            Token.is_active == True
        ).all()
        
        token_list = []
        for token in tokens:
            token_data = {
                "id": token.id,
                "token": token.token[:16] + "...",  # Masked for security
                "agent_id": token.agent_id,
                "user_id": token.user_id,
                "is_active": token.is_active,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "created_at": token.created_at.isoformat()
            }
            token_list.append(token_data)
        
        return json.dumps({
            "tokens": token_list,
            "total": len(token_list),
            "user_id": user_id
        }, indent=2)
        
    finally:
        db.close()

# TOOLS (POST-like endpoints)

@mcp.tool()
def agent_call_tool(agent_id: str, tool_name: str, parameters: Dict[str, Any], caller_user_id: str) -> Dict[str, Any]:
    """Call a specific tool on an agent via webhook"""
    db = get_db()
    try:
        # Get the agent
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.is_active == True
        ).first()
        
        if not agent:
            return {"error": "Agent not found"}
        
        # Parse the tool calls example to validate available tools
        try:
            import json as json_module
            tool_calls_data = json_module.loads(agent.toolCallsExampleJson)
            available_tools = tool_calls_data.get("available_tools", [])
            if tool_name not in available_tools:
                return {"error": f"Tool '{tool_name}' not found in agent's available tools"}
        except (json_module.JSONDecodeError, KeyError):
            # If parsing fails, allow the tool call to proceed
            pass
        
        # Create tool call record
        # Convert price from wei to float for cost calculation
        cost_in_eth = float(agent.price) / 1e18
        tool_call = ToolCall(
            agent_id=agent_id,
            caller_user_id=caller_user_id,
            tool_name=tool_name,
            parameters=parameters,
            cost=cost_in_eth,
            payment_status="pending"
        )
        
        db.add(tool_call)
        db.commit()
        db.refresh(tool_call)
        
        # Execute via webhook if available
        result = None
        if agent.webhookUrl:
            try:
                webhook_payload = {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "tool_call_id": tool_call.id
                }
                
                response = requests.post(
                    agent.webhookUrl,
                    json=webhook_payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                else:
                    result = {
                        "error": f"Webhook call failed with status {response.status_code}",
                        "details": response.text
                    }
                    
            except requests.exceptions.RequestException as e:
                result = {"error": f"Webhook request failed: {str(e)}"}
        else:
            result = {"error": "No webhook configured for this agent"}
        
        # Update tool call with result
        tool_call.result = result
        tool_call.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "tool_call_id": tool_call.id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "result": result,
            "cost": cost_in_eth,
            "status": "completed"
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def payment_create(tool_call_id: str, amount: float, currency: str = "USD") -> Dict[str, Any]:
    """Create a payment (Coinbase checkout) for a tool call"""
    db = get_db()
    try:
        # Verify tool call exists
        tool_call = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
        
        if not tool_call:
            return {"error": "Tool call not found"}
        
        # Create payment record
        payment = Payment(
            tool_call_id=tool_call_id,
            amount=amount,
            currency=currency,
            status="pending"
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # TODO: Create actual Coinbase checkout session
        # For now, simulate this
        coinbase_checkout_id = f"checkout_{uuid.uuid4().hex[:8]}"
        payment.coinbase_checkout_id = coinbase_checkout_id
        db.commit()
        
        return {
            "payment_id": payment.id,
            "tool_call_id": tool_call_id,
            "amount": amount,
            "currency": currency,
            "coinbase_checkout_id": coinbase_checkout_id,
            "status": "pending",
            "checkout_url": f"https://commerce.coinbase.com/checkout/{coinbase_checkout_id}"
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def tool_call_poll(tool_call_id: str) -> Dict[str, Any]:
    """Poll to see if the result of a tool call has been completed"""
    db = get_db()
    try:
        tool_call = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
        
        if not tool_call:
            return {"error": "Tool call not found"}
        
        return {
            "tool_call_id": tool_call_id,
            "status": "completed" if tool_call.completed_at else "pending",
            "result": tool_call.result,
            "completed_at": tool_call.completed_at.isoformat() if tool_call.completed_at else None,
            "payment_status": tool_call.payment_status
        }
        
    finally:
        db.close()

@mcp.tool()
def tool_call_finalize(tool_call_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize an off-chain tool call and store its result"""
    db = get_db()
    try:
        tool_call = db.query(ToolCall).filter(ToolCall.id == tool_call_id).first()
        
        if not tool_call:
            return {"error": "Tool call not found"}
        
        if tool_call.completed_at:
            return {"error": "Tool call already completed"}
        
        # Update with provided result
        tool_call.result = result
        tool_call.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "tool_call_id": tool_call_id,
            "status": "finalized",
            "result": result,
            "completed_at": tool_call.completed_at.isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting MCP Server with FastMCP...")
    print("Resources available:")
    print("  - agent://list")
    print("  - agent://get/{agent_id}")
    print("  - tool_call://status/{tool_call_id}")
    print("  - payment://get_status/{identifier}")
    print("  - user://tokens/{user_id}")
    print()
    print("Tools available:")
    print("  - agent_call_tool")
    print("  - payment_create")
    print("  - tool_call_poll")
    print("  - tool_call_finalize")
    print()
    print("Server running on default MCP port...")
    
    # Run the server
    mcp.run() 