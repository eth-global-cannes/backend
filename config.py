import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/agents_db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", "")
COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001") 