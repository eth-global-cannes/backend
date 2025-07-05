#!/usr/bin/env python3
"""
Example Agent Webhook Handler

This is a simple example of how to implement a webhook handler for an agent.
It demonstrates how to receive tool calls and return results.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

app = FastAPI(title="Example Agent Webhook", version="1.0.0")

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    tool_call_id: str

def calculator_add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

def calculator_multiply(x: float, y: float) -> float:
    """Multiply two numbers"""
    return x * y

def calculator_subtract(a: float, b: float) -> float:
    """Subtract two numbers"""
    return a - b

def calculator_divide(a: float, b: float) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

# Tool registry
TOOLS = {
    "add": calculator_add,
    "multiply": calculator_multiply,
    "subtract": calculator_subtract,
    "divide": calculator_divide
}

@app.post("/webhook")
async def handle_tool_call(request: ToolCallRequest):
    """
    Handle incoming tool calls from the agent server
    """
    try:
        tool_name = request.tool_name
        parameters = request.parameters
        tool_call_id = request.tool_call_id
        
        print(f"Received tool call: {tool_name} with parameters: {parameters}")
        
        # Check if tool exists
        if tool_name not in TOOLS:
            return {
                "error": f"Tool '{tool_name}' not found",
                "tool_call_id": tool_call_id
            }
        
        # Get the tool function
        tool_func = TOOLS[tool_name]
        
        # Execute the tool
        try:
            result = tool_func(**parameters)
            
            return {
                "result": result,
                "tool_call_id": tool_call_id,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "tool_call_id": tool_call_id,
                "status": "error"
            }
    
    except Exception as e:
        return {
            "error": f"Webhook error: {str(e)}",
            "tool_call_id": request.tool_call_id if hasattr(request, 'tool_call_id') else None,
            "status": "error"
        }

@app.get("/")
async def root():
    return {
        "message": "Example Agent Webhook",
        "available_tools": list(TOOLS.keys()),
        "webhook_endpoint": "/webhook"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting Example Agent Webhook server...")
    print("Available tools:")
    for tool_name in TOOLS:
        print(f"  - {tool_name}")
    print("\nWebhook endpoint: http://localhost:8001/webhook")
    print("Visit http://localhost:8001/docs for API documentation")
    
    uvicorn.run(
        "example_agent_webhook:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 