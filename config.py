import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Debug: Check if .env file exists and where
env_path = find_dotenv()
print(f"DEBUG: .env file found at: {env_path}")

# Load .env file - try multiple approaches
if env_path:
    # Load from found .env file
    load_dotenv(env_path)
    print("DEBUG: Loaded .env file successfully")
else:
    # Try loading from current directory
    current_dir_env = Path(".env")
    if current_dir_env.exists():
        load_dotenv(current_dir_env)
        print("DEBUG: Loaded .env from current directory")
    else:
        print("DEBUG: No .env file found")

# Debug: Check what DATABASE_URL is being loaded
db_url_from_env = os.getenv("DATABASE_URL")
db_url_from_shell = os.environ.get("DATABASE_URL")
print(f"DEBUG: DATABASE_URL from os.getenv(): {db_url_from_env}")
print(f"DEBUG: DATABASE_URL from os.environ: {db_url_from_shell}")

# Force SQLite for development - ignore any PostgreSQL URLs from environment
if db_url_from_env and "postgresql" in db_url_from_env.lower():
    print("DEBUG: Detected PostgreSQL URL in environment, forcing SQLite for development")
    DATABASE_URL = "sqlite:///./agents.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agents.db")

print(f"DEBUG: Final DATABASE_URL: {DATABASE_URL}")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", "")
COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001") 