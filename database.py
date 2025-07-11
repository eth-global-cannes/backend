from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from config import DATABASE_URL

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)  # Changed from imageUrl to image
    description = Column(Text, nullable=False)  # New field
    type = Column(String, nullable=False)  # New field (per-use, subscription, etc.)
    price = Column(String, nullable=False)  # Changed from Integer to String
    url = Column(String, nullable=False)  # New field
    endpoints = Column(JSON, nullable=False)  # New field to store endpoints as JSON
    agentOwner = Column(String, nullable=True)  # Address of the owner, now optional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolCall(Base):
    __tablename__ = "tool_calls"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    caller_user_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    parameters = Column(JSON)
    result = Column(JSON)
    cost = Column(Float, nullable=False)
    payment_status = Column(String, default="pending")  # pending, paid, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_call_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    coinbase_checkout_id = Column(String)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, nullable=False, unique=True)
    agent_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 