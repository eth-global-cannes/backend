from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database import create_tables
from routes import agents, mcp

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="Agent Registry & MCP Server",
    description="A server for registering agents and executing tool calls through MCP",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)
app.include_router(mcp.router)  # Now handles tokens and payments

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Agent Registry & MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "agents": "/api/agents",
            "tokens": "/api/tokens",
            "mcp_server": "http://localhost:8080",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 