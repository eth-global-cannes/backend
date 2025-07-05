#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Implementation

This implements a proper MCP server that:
1. Loads agents and tools dynamically from the database
2. Enforces authentication via tokens
3. Supports JSON-RPC 2.0 protocol
4. Calls agent webhooks for tool execution
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from mcp.server import MCPServer, Tool
from mcp.server.exceptions import MCPError

from database import SessionLocal, Agent, Token, ToolCall
from config import DATABASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPAgentServer:
    def __init__(self):
        self.server = MCPServer()
        self.agents_cache = {}
        self.tools_cache = {}
        self.setup_middleware()
        self.load_agents()
    
    def setup_middleware(self):
        """Setup authentication middleware"""
        
        @self.server.middleware
        async def auth_middleware(request, call_next):
            """Authentication middleware to check tokens"""
            try:
                # Extract token from Authorization header
                auth_header = request.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    raise MCPError("Missing or invalid Authorization header")
                
                token = auth_header.replace("Bearer ", "")
                
                # Extract method/tool name from JSON-RPC request
                body = await request.json()
                method = body.get("method")
                
                if not method:
                    raise MCPError("Missing method in request")
                
                # Check token validity
                db = SessionLocal()
                try:
                    token_record = db.query(Token).filter(
                        Token.token == token,
                        Token.is_active == True
                    ).first()
                    
                    if not token_record:
                        raise MCPError("Invalid or expired token")
                    
                    # Check if token has access to this agent/tool
                    agent = db.query(Agent).filter(
                        Agent.id == token_record.agent_id,
                        Agent.is_active == True
                    ).first()
                    
                    if not agent:
                        raise MCPError("Agent not found or inactive")
                    
                    # Check if tool exists for this agent
                    if method not in agent.tool_schema.get("tools", {}):
                        raise MCPError(f"Tool '{method}' not found for this agent")
                    
                    # Add agent and token info to request context
                    request.context = {
                        "agent": agent,
                        "token": token_record,
                        "user_id": token_record.user_id
                    }
                    
                finally:
                    db.close()
                
                # Continue to the actual handler
                return await call_next(request)
                
            except MCPError:
                raise
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                raise MCPError("Authentication failed")
    
    def load_agents(self):
        """Load agents and their tools from database"""
        db = SessionLocal()
        try:
            agents = db.query(Agent).filter(Agent.is_active == True).all()
            
            for agent in agents:
                self.agents_cache[agent.id] = agent
                
                # Register tools for this agent
                for tool_name, tool_schema in agent.tool_schema.get("tools", {}).items():
                    self.register_agent_tool(agent, tool_name, tool_schema)
                    
            logger.info(f"Loaded {len(agents)} agents with tools")
            
        finally:
            db.close()
    
    def register_agent_tool(self, agent: Agent, tool_name: str, tool_schema: Dict[str, Any]):
        """Register a tool for an agent"""
        
        class DynamicTool(Tool):
            def __init__(self, name: str, schema: Dict[str, Any], agent_data: Agent):
                self.name = name
                self.schema = schema
                self.agent_data = agent_data
                super().__init__()
            
            async def call(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                """Execute the tool call"""
                try:
                    # Create tool call record
                    db = SessionLocal()
                    try:
                        tool_call = ToolCall(
                            agent_id=self.agent_data.id,
                            caller_user_id=context.get("user_id") if context else "unknown",
                            tool_name=self.name,
                            parameters=params,
                            cost=self.agent_data.pricing,
                            payment_status="pending"
                        )
                        
                        db.add(tool_call)
                        db.commit()
                        db.refresh(tool_call)
                        
                        # Execute via webhook if available
                        if self.agent_data.webhook_url:
                            result = await self.call_webhook(params, tool_call.id)
                        else:
                            result = {"error": "No webhook configured for this agent"}
                        
                        # Update tool call with result
                        tool_call.result = result
                        tool_call.completed_at = datetime.utcnow()
                        db.commit()
                        
                        return result
                        
                    finally:
                        db.close()
                        
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return {"error": str(e)}
            
            async def call_webhook(self, params: Dict[str, Any], tool_call_id: str) -> Dict[str, Any]:
                """Call the agent's webhook"""
                try:
                    webhook_payload = {
                        "tool_name": self.name,
                        "parameters": params,
                        "tool_call_id": tool_call_id
                    }
                    
                    response = requests.post(
                        self.agent_data.webhook_url,
                        json=webhook_payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        return {
                            "error": f"Webhook call failed with status {response.status_code}",
                            "details": response.text
                        }
                        
                except requests.exceptions.RequestException as e:
                    return {"error": f"Webhook request failed: {str(e)}"}
                except Exception as e:
                    return {"error": f"Webhook execution error: {str(e)}"}
        
        # Create and register the tool
        tool = DynamicTool(tool_name, tool_schema, agent)
        self.server.register_tool(tool)
        
        # Cache the tool
        tool_key = f"{agent.id}:{tool_name}"
        self.tools_cache[tool_key] = tool
        
        logger.info(f"Registered tool '{tool_name}' for agent '{agent.name}'")
    
    def reload_agents(self):
        """Reload agents from database (for runtime updates)"""
        logger.info("Reloading agents from database...")
        
        # Clear current cache
        self.agents_cache.clear()
        self.tools_cache.clear()
        
        # Clear registered tools
        self.server.clear_tools()
        
        # Reload
        self.load_agents()
    
    async def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the MCP server"""
        logger.info(f"Starting MCP server on {host}:{port}")
        logger.info(f"Registered {len(self.tools_cache)} tools from {len(self.agents_cache)} agents")
        
        await self.server.start(host=host, port=port)

# Global server instance
mcp_server = MCPAgentServer()

async def main():
    """Main entry point"""
    try:
        await mcp_server.start()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 