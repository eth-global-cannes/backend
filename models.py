from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ApiParam(BaseModel):
    id: str = Field(..., description="Unique identifier for the parameter")
    key: str = Field(..., description="Parameter key name")
    value: str = Field(..., description="Default value for the parameter")
    type: str = Field(..., description="Parameter type (string, number, boolean, etc.)")

class Endpoint(BaseModel):
    id: str = Field(..., description="Unique identifier for the endpoint")
    endpoint: str = Field(..., description="Endpoint path (e.g., '/send')")
    apiParams: List[ApiParam] = Field(..., description="List of API parameters for this endpoint")

class AgentRegisterRequest(BaseModel):
    name: str = Field(..., description="Name of the agent")
    image: str = Field(..., description="Image URL for the agent")
    description: str = Field(..., description="Description of the agent")
    type: str = Field(..., description="Agent type (e.g., 'per-use')")
    price: str = Field(..., description="Price to use the agent")
    url: str = Field(..., description="Agent URL")
    endpoints: List[Endpoint] = Field(..., description="List of available endpoints")
    agentOwner: Optional[str] = Field(None, description="The address of the user who registered the agent")

class AgentResponse(BaseModel):
    id: str
    name: str
    image: str
    description: str
    type: str
    price: str
    url: str
    endpoints: List[Endpoint]
    agentOwner: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ToolCallRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent to call")
    caller_user_id: str = Field(..., description="ID of the user making the call")
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the tool call")

class ToolCallResponse(BaseModel):
    id: str
    agent_id: str
    caller_user_id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    cost: float
    payment_status: str
    created_at: datetime
    completed_at: Optional[datetime]

class PaymentRequest(BaseModel):
    tool_call_id: str = Field(..., description="ID of the tool call to pay for")
    amount: float = Field(..., description="Amount to pay")
    currency: str = Field(default="USD", description="Currency for payment")

class PaymentResponse(BaseModel):
    id: str
    tool_call_id: str
    amount: float
    currency: str
    coinbase_checkout_id: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

class TokenRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent to access")
    user_id: str = Field(..., description="ID of the user requesting access")
    expires_in_days: Optional[int] = Field(30, description="Number of days until token expires")

class TokenResponse(BaseModel):
    id: str
    token: str
    agent_id: str
    user_id: str
    expires_at: Optional[datetime]
    created_at: datetime

class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    page: int
    per_page: int 