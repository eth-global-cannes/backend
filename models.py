from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AgentRegisterRequest(BaseModel):
    name: str = Field(..., description="Name of the agent")
    imageUrl: str = Field(..., description="Image URL for the agent")
    price: int = Field(..., description="Price to use the agent, in wei (1 ether = 1e18 wei)")
    apiKey: str = Field(..., description="API key for the agent (WARNING: Stored publicly)")
    webhookUrl: str = Field(..., description="Webhook URL for the agent")
    toolCallsExampleJson: str = Field(..., description="Example of the agent's tool call structure")
    agentOwner: str = Field(..., description="The address of the user who registered the agent")

class AgentResponse(BaseModel):
    id: str
    name: str
    imageUrl: str
    price: int
    apiKey: str
    webhookUrl: str
    toolCallsExampleJson: str
    agentOwner: str
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