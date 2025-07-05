from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AgentRegisterRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user registering the agent")
    name: str = Field(..., description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for the agent")
    tool_schema: Dict[str, Any] = Field(..., description="JSON schema of the tools")
    pricing: float = Field(..., description="Price per tool call")

class AgentResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    webhook_url: Optional[str]
    tool_schema: Dict[str, Any]
    pricing: float
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