from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from database import get_db, Agent
from models import (
    AgentRegisterRequest, 
    AgentResponse, 
    AgentListResponse
)

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.post("/register", response_model=dict)
async def register_agent(
    agent_data: AgentRegisterRequest, 
    db: Session = Depends(get_db)
):
    """
    Register a new agent with blockchain-compatible structure
    """
    try:
        # Validate required fields
        if not agent_data.name or not agent_data.imageUrl or not agent_data.webhookUrl or not agent_data.agentOwner:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate price (must be positive)
        if agent_data.price <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than 0")
        
        # Validate Ethereum address format (basic validation)
        if not agent_data.agentOwner.startswith("0x") or len(agent_data.agentOwner) != 42:
            raise HTTPException(status_code=400, detail="Invalid Ethereum address format")
        
        # Create new agent
        agent_id = str(uuid.uuid4())
        
        new_agent = Agent(
            id=agent_id,
            name=agent_data.name,
            imageUrl=agent_data.imageUrl,
            price=agent_data.price,
            apiKey=agent_data.apiKey,
            webhookUrl=agent_data.webhookUrl,
            toolCallsExampleJson=agent_data.toolCallsExampleJson,
            agentOwner=agent_data.agentOwner
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        return {
            "agent_id": agent_id,
            "message": "Agent registered successfully",
            "status": "active"
        }
        
    except Exception as err:
        db.rollback()
        print(f"Error registering agent: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_owner: Optional[str] = Query(None, description="Filter by agent owner address"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all agents with optional filtering
    """
    try:
        query = db.query(Agent).filter(Agent.is_active == True)
        
        if agent_owner:
            query = query.filter(Agent.agentOwner == agent_owner)
        
        total = query.count()
        
        agents = query.offset((page - 1) * per_page).limit(per_page).all()
        
        agent_responses = [
            AgentResponse(
                id=agent.id,
                name=agent.name,
                imageUrl=agent.imageUrl,
                price=agent.price,
                apiKey=agent.apiKey,
                webhookUrl=agent.webhookUrl,
                toolCallsExampleJson=agent.toolCallsExampleJson,
                agentOwner=agent.agentOwner,
                is_active=agent.is_active,
                created_at=agent.created_at,
                updated_at=agent.updated_at
            )
            for agent in agents
        ]
        
        return AgentListResponse(
            agents=agent_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as err:
        print(f"Error listing agents: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Get a specific agent by ID
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            imageUrl=agent.imageUrl,
            price=agent.price,
            apiKey=agent.apiKey,
            webhookUrl=agent.webhookUrl,
            toolCallsExampleJson=agent.toolCallsExampleJson,
            agentOwner=agent.agentOwner,
            is_active=agent.is_active,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as err:
        print(f"Error getting agent: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.put("/{agent_id}", response_model=dict)
async def update_agent(
    agent_id: str,
    agent_data: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update agent fields
        agent.name = agent_data.name
        agent.description = agent_data.description
        agent.webhook_url = agent_data.webhook_url
        agent.tool_schema = agent_data.tool_schema
        agent.pricing = agent_data.pricing
        agent.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "agent_id": agent_id,
            "message": "Agent updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as err:
        db.rollback()
        print(f"Error updating agent: {err}")
        raise HTTPException(status_code=500, detail="Server error")

@router.delete("/{agent_id}", response_model=dict)
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Soft delete an agent (set is_active to False)
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "agent_id": agent_id,
            "message": "Agent deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as err:
        db.rollback()
        print(f"Error deleting agent: {err}")
        raise HTTPException(status_code=500, detail="Server error") 