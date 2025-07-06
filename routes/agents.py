from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import json

from database import get_db, Agent
from models import (
    AgentRegisterRequest, 
    AgentResponse, 
    AgentListResponse,
    Endpoint,
    ApiParam
)

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.post("/register", response_model=dict)
async def register_agent(
    agent_data: AgentRegisterRequest, 
    db: Session = Depends(get_db)
):
    """
    Register a new agent with the new schema structure
    """
    try:
        # Validate required fields
        if not agent_data.name or not agent_data.image or not agent_data.description:
            raise HTTPException(status_code=400, detail="Missing required fields: name, image, or description")
        
        # Validate price (should be convertible to number)
        try:
            price_float = float(agent_data.price)
            if price_float <= 0:
                raise HTTPException(status_code=400, detail="Price must be greater than 0")
        except ValueError:
            raise HTTPException(status_code=400, detail="Price must be a valid number")
        
        # Validate agent type
        valid_types = ["per-use", "subscription", "free", "one-time"]
        if agent_data.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid agent type. Must be one of: {valid_types}")
        
        # Validate endpoints
        if not agent_data.endpoints or len(agent_data.endpoints) == 0:
            raise HTTPException(status_code=400, detail="At least one endpoint is required")
        
        # Validate Ethereum address format if provided
        if agent_data.agentOwner:
            if not agent_data.agentOwner.startswith("0x") or len(agent_data.agentOwner) != 42:
                raise HTTPException(status_code=400, detail="Invalid Ethereum address format")
        
        # Create new agent
        agent_id = str(uuid.uuid4())
        
        # Convert endpoints to JSON format for database storage
        endpoints_json = [
            {
                "id": endpoint.id,
                "endpoint": endpoint.endpoint,
                "apiParams": [
                    {
                        "id": param.id,
                        "key": param.key,
                        "value": param.value,
                        "type": param.type
                    }
                    for param in endpoint.apiParams
                ]
            }
            for endpoint in agent_data.endpoints
        ]
        
        new_agent = Agent(
            id=agent_id,
            name=agent_data.name,
            image=agent_data.image,
            description=agent_data.description,
            type=agent_data.type,
            price=agent_data.price,
            url=agent_data.url,
            endpoints=endpoints_json,
            agentOwner="0xxx....."
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
        raise HTTPException(status_code=500, detail=f"Server error: {str(err)}")

@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_owner: Optional[str] = Query(None, description="Filter by agent owner address"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
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
        
        if agent_type:
            query = query.filter(Agent.type == agent_type)
        
        total = query.count()
        
        agents = query.offset((page - 1) * per_page).limit(per_page).all()
        
        agent_responses = []
        for agent in agents:
            # Convert JSON endpoints back to Pydantic models
            endpoints = []
            for endpoint_data in agent.endpoints:
                api_params = [
                    ApiParam(
                        id=param["id"],
                        key=param["key"],
                        value=param["value"],
                        type=param["type"]
                    )
                    for param in endpoint_data["apiParams"]
                ]
                endpoints.append(Endpoint(
                    id=endpoint_data["id"],
                    endpoint=endpoint_data["endpoint"],
                    apiParams=api_params
                ))
            
            agent_responses.append(AgentResponse(
                id=agent.id,
                name=agent.name,
                image=agent.image,
                description=agent.description,
                type=agent.type,
                price=agent.price,
                url=agent.url,
                endpoints=endpoints,
                agentOwner=agent.agentOwner,
                is_active=agent.is_active,
                created_at=agent.created_at,
                updated_at=agent.updated_at
            ))
        
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
        
        # Convert JSON endpoints back to Pydantic models
        endpoints = []
        for endpoint_data in agent.endpoints:
            api_params = [
                ApiParam(
                    id=param["id"],
                    key=param["key"],
                    value=param["value"],
                    type=param["type"]
                )
                for param in endpoint_data["apiParams"]
            ]
            endpoints.append(Endpoint(
                id=endpoint_data["id"],
                endpoint=endpoint_data["endpoint"],
                apiParams=api_params
            ))
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            image=agent.image,
            description=agent.description,
            type=agent.type,
            price=agent.price,
            url=agent.url,
            endpoints=endpoints,
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
        
        # Validate price (should be convertible to number)
        try:
            price_float = float(agent_data.price)
            if price_float <= 0:
                raise HTTPException(status_code=400, detail="Price must be greater than 0")
        except ValueError:
            raise HTTPException(status_code=400, detail="Price must be a valid number")
        
        # Validate agent type
        valid_types = ["per-use", "subscription", "free", "one-time"]
        if agent_data.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid agent type. Must be one of: {valid_types}")
        
        # Convert endpoints to JSON format for database storage
        endpoints_json = [
            {
                "id": endpoint.id,
                "endpoint": endpoint.endpoint,
                "apiParams": [
                    {
                        "id": param.id,
                        "key": param.key,
                        "value": param.value,
                        "type": param.type
                    }
                    for param in endpoint.apiParams
                ]
            }
            for endpoint in agent_data.endpoints
        ]
        
        # Update agent fields
        agent.name = agent_data.name
        agent.image = agent_data.image
        agent.description = agent_data.description
        agent.type = agent_data.type
        agent.price = agent_data.price
        agent.url = agent_data.url
        agent.endpoints = endpoints_json
        agent.agentOwner = agent_data.agentOwner
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