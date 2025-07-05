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
    Register a new agent with tool schema and pricing
    """
    try:
        # Validate required fields
        if not agent_data.name or not agent_data.tool_schema or not agent_data.pricing or not agent_data.user_id:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate tool schema structure
        if not isinstance(agent_data.tool_schema, dict):
            raise HTTPException(status_code=400, detail="Tool schema must be a valid JSON object")
        
        # Validate pricing
        if agent_data.pricing <= 0:
            raise HTTPException(status_code=400, detail="Pricing must be greater than 0")
        
        # Create new agent
        agent_id = str(uuid.uuid4())
        
        new_agent = Agent(
            id=agent_id,
            user_id=agent_data.user_id,
            name=agent_data.name,
            description=agent_data.description,
            webhook_url=agent_data.webhook_url,
            tool_schema=agent_data.tool_schema,
            pricing=agent_data.pricing
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # TODO: Generate Coinbase checkout in next step
        
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
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all agents with optional filtering
    """
    try:
        query = db.query(Agent).filter(Agent.is_active == True)
        
        if user_id:
            query = query.filter(Agent.user_id == user_id)
        
        total = query.count()
        
        agents = query.offset((page - 1) * per_page).limit(per_page).all()
        
        agent_responses = [
            AgentResponse(
                id=agent.id,
                user_id=agent.user_id,
                name=agent.name,
                description=agent.description,
                webhook_url=agent.webhook_url,
                tool_schema=agent.tool_schema,
                pricing=agent.pricing,
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
            user_id=agent.user_id,
            name=agent.name,
            description=agent.description,
            webhook_url=agent.webhook_url,
            tool_schema=agent.tool_schema,
            pricing=agent.pricing,
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