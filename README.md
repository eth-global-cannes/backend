# Agent Registry with FastMCP Server

A complete system for registering agents and handling tool calls through MCP (Model Context Protocol) using FastMCP.

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Agent Registry    │    │   FastMCP Server    │    │   Agent Webhook     │
│   (FastAPI)         │    │   (server.py)       │    │   (Example)         │
│   Port: 8000        │    │   Port: MCP         │    │   Port: 8001        │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                           │                           │
         │ 1. Register Agent         │ 2. Call Tools            │ 3. Execute Tools
         │ 2. Create Tokens          │ 3. Get Resources         │ 4. Return Results
         │ 3. Manage Payments        │ 4. Handle Payments       │
         └───────────────────────────┼───────────────────────────┘
                                     │
                              ┌─────────────────────┐
                              │   PostgreSQL        │
                              │   Database          │
                              └─────────────────────┘
```

## Components

### 1. Agent Registry Server (`main.py`)
- **FastAPI** application for agent registration
- **PostgreSQL** database with SQLAlchemy ORM
- **JWT** authentication and token management
- **Coinbase Commerce** payment integration

### 2. FastMCP Server (`server.py`)
- **FastMCP** implementation with proper MCP protocol
- **Resources** (GET-like operations) for data retrieval
- **Tools** (POST-like operations) for actions
- **Database** integration for persistent storage

### 3. Example Agent Webhook (`example_agent_webhook.py`)
- **FastAPI** webhook handler for agent implementation
- **Calculator tools** for demonstration
- **Tool execution** and result handling

## FastMCP Resources

Resources are like GET endpoints that return data:

| Resource | Description |
|----------|-------------|
| `agent://list` | List all registered agents |
| `agent://get/{agent_id}` | Get specific agent details |
| `tool_call://status/{tool_call_id}` | Get tool call status |
| `payment://get_status/{identifier}` | Get payment status |
| `user://tokens/{user_id}` | Get user tokens |

## FastMCP Tools

Tools are like POST endpoints that perform actions:

| Tool | Description |
|------|-------------|
| `agent_call_tool` | Call a tool on an agent via webhook |
| `payment_create` | Create a payment for a tool call |
| `tool_call_poll` | Poll tool call completion status |
| `tool_call_finalize` | Finalize off-chain tool call |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Environment

```bash
cp .env.example .env
# Edit .env with your database and API keys
```

### 3. Start Services

```bash
# Terminal 1: Start Agent Registry
python main.py

# Terminal 2: Start FastMCP Server
python server.py

# Terminal 3: Start Example Agent Webhook
python example_agent_webhook.py
```

### 4. Run Demo

```bash
# Run the complete workflow demo
python mcp_client_example.py
```

## Example Usage

### 1. Register an Agent

```python
import requests

agent_data = {
    "user_id": "user123",
    "name": "Calculator Agent",
    "description": "Basic math operations",
    "webhook_url": "http://localhost:8001/webhook",
    "tool_schema": {
        "tools": {
            "add": {
                "description": "Add two numbers",
                "parameters": {"a": "number", "b": "number"}
            }
        }
    },
    "pricing": 0.02
}

response = requests.post(
    "http://localhost:8000/api/agents/register",
    json=agent_data
)
agent = response.json()
```

### 2. Create Access Token

```python
token_data = {
    "agent_id": agent["agent_id"],
    "user_id": "caller456",
    "expires_in_days": 30
}

response = requests.post(
    "http://localhost:8000/api/tokens/create",
    json=token_data
)
token = response.json()
```

### 3. Use FastMCP Resources

```python
# Using FastMCP client (pseudo-code)
from fastmcp import FastMCPClient

client = FastMCPClient("mcp://localhost")

# Get all agents
agents = client.get_resource("agent://list")

# Get specific agent
agent = client.get_resource(f"agent://get/{agent_id}")

# Check tool call status
status = client.get_resource(f"tool_call://status/{call_id}")
```

### 4. Use FastMCP Tools

```python
# Call a tool on an agent
result = client.call_tool("agent_call_tool", {
    "agent_id": "agent123",
    "tool_name": "add",
    "parameters": {"a": 10, "b": 20},
    "caller_user_id": "user456"
})

# Create payment
payment = client.call_tool("payment_create", {
    "tool_call_id": "call123",
    "amount": 0.02,
    "currency": "USD"
})
```

## Database Schema

### Tables

- **agents**: Agent registration and metadata
- **tool_calls**: Tool execution records
- **payments**: Payment tracking
- **tokens**: Access token management

### Key Relations

```sql
agents (1) -> (many) tool_calls
tool_calls (1) -> (many) payments
agents (1) -> (many) tokens
```

## API Endpoints

### Agent Registry (Port 8000)

- `POST /api/agents/register` - Register new agent
- `GET /api/agents/` - List all agents
- `GET /api/agents/{agent_id}` - Get agent details
- `POST /api/tokens/create` - Create access token
- `GET /api/tokens/tool-call/{tool_call_id}` - Get tool call status

### Example Agent Webhook (Port 8001)

- `POST /webhook` - Handle tool calls
- `GET /` - Get agent info
- `GET /health` - Health check

## Testing

```bash
# Run API tests
python test_api.py

# Run MCP demo
python mcp_client_example.py

# Test agent webhook
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "add", "parameters": {"a": 5, "b": 3}, "tool_call_id": "test"}'
```

## Development

### Project Structure

```
ETHGlobalCannes/
├── main.py                    # FastAPI agent registry
├── server.py                  # FastMCP server
├── database.py                # Database models
├── models.py                  # Pydantic models
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── routes/
│   ├── agents.py             # Agent routes
│   └── mcp.py                # Token routes
├── example_agent_webhook.py  # Example webhook
├── mcp_client_example.py     # MCP client demo
├── docker-compose.yml        # Docker setup
└── README.md                 # This file
```

### Key Features

- **FastMCP Integration**: Proper MCP protocol implementation
- **Resource-based Access**: GET-like operations for data retrieval
- **Tool-based Actions**: POST-like operations for actions
- **Database Persistence**: PostgreSQL with SQLAlchemy
- **Payment Integration**: Coinbase Commerce support
- **Token-based Auth**: JWT tokens for access control
- **Webhook Support**: Agent tool execution via webhooks
- **Docker Support**: Container-based deployment

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API Keys
COINBASE_API_KEY=your_coinbase_api_key
JWT_SECRET_KEY=your_jwt_secret_key

# Server Config
AGENT_REGISTRY_PORT=8000
MCP_SERVER_PORT=8080
WEBHOOK_PORT=8001
```

## Troubleshooting

### Common Issues

1. **FastMCP import errors**: Make sure `fastmcp==0.2.0` is installed
2. **Database connection**: Check PostgreSQL is running and credentials are correct
3. **Port conflicts**: Ensure ports 8000, 8001 are available
4. **Webhook timeouts**: Check agent webhook is running and reachable

### Logs

- Agent Registry: Check FastAPI logs for registration/token issues
- FastMCP Server: Check MCP protocol logs for resource/tool calls
- Agent Webhook: Check webhook logs for tool execution

## License

MIT License 