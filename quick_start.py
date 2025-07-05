#!/usr/bin/env python3
"""
Quick Start Script for Agent Registry & MCP Server

This script helps you get started quickly by:
1. Setting up the database
2. Creating a .env file
3. Starting the server
4. Running basic tests
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def create_env_file():
    """Create a .env file with default values"""
    env_content = """# Database Configuration
DATABASE_URL=postgresql://localhost/agents_db

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Coinbase Integration
COINBASE_API_KEY=your-coinbase-api-key
COINBASE_WEBHOOK_SECRET=your-coinbase-webhook-secret

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("⚠️  .env file already exists")

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def check_postgresql():
    """Check if PostgreSQL is available"""
    try:
        result = subprocess.run(["psql", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL is available")
            return True
        else:
            print("⚠️  PostgreSQL not found in PATH")
            return False
    except FileNotFoundError:
        print("⚠️  PostgreSQL not found")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Try to create the database
        result = subprocess.run(["createdb", "agents_db"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database 'agents_db' created")
        else:
            if "already exists" in result.stderr:
                print("⚠️  Database 'agents_db' already exists")
            else:
                print(f"❌ Failed to create database: {result.stderr}")
                return False
    except FileNotFoundError:
        print("❌ createdb command not found. Please install PostgreSQL")
        return False
    
    return True

def start_server():
    """Start the server"""
    print("🚀 Starting the server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n✅ Server stopped")

def run_tests():
    """Run the test script"""
    print("🧪 Running API tests...")
    try:
        subprocess.run([sys.executable, "test_api.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
    except FileNotFoundError:
        print("❌ test_api.py not found")

def main():
    """Main setup function"""
    print("🚀 Agent Registry & MCP Server - Quick Start")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    # Check PostgreSQL
    postgres_available = check_postgresql()
    
    if postgres_available:
        create_database()
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Start the server: python main.py")
        print("2. Test the API: python test_api.py")
        print("3. Visit http://localhost:8000/docs for API documentation")
        
        # Ask if user wants to start the server
        start_now = input("\nWould you like to start the server now? (y/n): ").lower().strip()
        if start_now in ['y', 'yes']:
            start_server()
    else:
        print("\n⚠️  Setup incomplete - PostgreSQL not available")
        print("\nTo use with Docker:")
        print("1. Run: docker-compose up -d")
        print("2. Visit http://localhost:8000/docs")
        
        print("\nTo install PostgreSQL locally:")
        print("- macOS: brew install postgresql")
        print("- Ubuntu: sudo apt-get install postgresql")
        print("- Windows: Download from https://www.postgresql.org/download/")

if __name__ == "__main__":
    main() 